"""Service for parsing Canvas gradebook CSVs and importing roster members."""

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..db import Session, get_engine
from ..repositories.roster_upload_repository import RosterUploadRepository
from ..repositories.membership_repository import MembershipRepository
from ..repositories.user_repository import UserRepository
from ..tables.membership import Membership, MembershipState, MembershipType
from ..tables.roster_upload_job import RosterUploadJob, RosterUploadStatus
from ..tables.user import User


@dataclass
class ParsedStudent:
    """A single student row extracted from a Canvas gradebook CSV."""

    family_name: str
    given_name: str
    pid: int
    onyen: str


@dataclass
class ImportResult:
    """Summary of a roster import operation."""

    created: int = 0
    updated: int = 0
    errors: list[str] = field(default_factory=list)


def parse_canvas_csv(csv_text: str) -> list[ParsedStudent]:
    """Parses a Canvas gradebook CSV and extracts student records.

    Canvas gradebook format:
    - Row 1: headers (Student, ID, SIS User ID, SIS Login ID, ...)
    - Row 2: posting info (skipped)
    - Row 3: points possible (starts with leading whitespace, skipped)
    - Row 4+: student data rows

    The Student column uses "Last, First" format.

    Args:
        csv_text: Raw CSV content as a string.

    Returns:
        A list of parsed student records.

    Raises:
        ValueError: If the CSV is missing required columns.
    """
    reader = csv.DictReader(io.StringIO(csv_text))

    required = {"Student", "SIS User ID", "SIS Login ID"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        missing = required - set(reader.fieldnames or [])
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    students: list[ParsedStudent] = []
    for row in reader:
        student_name = row.get("Student", "").strip()
        sis_user_id = row.get("SIS User ID", "").strip()
        sis_login_id = row.get("SIS Login ID", "").strip()

        # Skip non-data rows (posting info, points possible)
        if not student_name or not sis_user_id or not sis_login_id:
            continue

        # Parse "Last, First" name format
        parts = student_name.split(",", 1)
        family_name = parts[0].strip().strip('"')
        given_name = parts[1].strip() if len(parts) > 1 else ""

        try:
            pid = int(sis_user_id)
        except ValueError:
            continue

        students.append(
            ParsedStudent(
                family_name=family_name,
                given_name=given_name,
                pid=pid,
                onyen=sis_login_id,
            )
        )

    return students


def process_roster_upload(job_id: int) -> None:
    """Processes a roster upload job: parses CSV, creates/updates users and memberships.

    This function is designed to run inside the background worker. It opens its
    own session, loads the job, parses the CSV, and creates or updates users and
    memberships idempotently.

    Args:
        job_id: Primary key of the RosterUploadJob to process.
    """
    from sqlmodel import Session as _Session

    engine = get_engine()
    with _Session(engine) as session:
        try:
            _do_process(session, job_id)
            session.commit()
        except Exception:
            session.rollback()
            _mark_failed(session, job_id)
            session.commit()
            raise


def _do_process(session: Session, job_id: int) -> None:
    """Core processing logic within a session context."""
    repo = RosterUploadRepository(session)
    job = repo.get_by_id(job_id)
    if job is None:
        raise ValueError(f"RosterUploadJob {job_id} not found")

    job.status = RosterUploadStatus.PROCESSING
    repo.update(job)
    session.flush()

    students = parse_canvas_csv(job.csv_data)
    result = _import_students(session, job.course_id, students)

    job.status = RosterUploadStatus.COMPLETED
    job.created_count = result.created
    job.updated_count = result.updated
    job.error_count = len(result.errors)
    job.error_details = "\n".join(result.errors) if result.errors else None
    job.completed_at = datetime.now(timezone.utc)
    repo.update(job)


def _mark_failed(session: Session, job_id: int) -> None:
    """Marks a job as failed after an unhandled exception."""
    try:
        repo = RosterUploadRepository(session)
        job = repo.get_by_id(job_id)
        if job is not None:
            job.status = RosterUploadStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            repo.update(job)
    except Exception:
        pass


def _import_students(
    session: Session, course_id: int, students: list[ParsedStudent]
) -> ImportResult:
    """Creates or updates users and memberships for parsed students.

    Args:
        session: Open database session.
        course_id: Course to add students to.
        students: Parsed student records from the CSV.

    Returns:
        An ImportResult summarizing counts and errors.
    """
    user_repo = UserRepository(session)
    membership_repo = MembershipRepository(session)
    result = ImportResult()

    for student in students:
        try:
            existing_user = user_repo.get_by_pid(student.pid)
            if existing_user is None:
                user_repo.register_user(
                    User(
                        pid=student.pid,
                        name=f"{student.given_name} {student.family_name}",
                        onyen=student.onyen,
                        given_name=student.given_name,
                        family_name=student.family_name,
                        email=f"{student.onyen}@unc.edu",
                    )
                )

            existing_membership = membership_repo.get_by_user_and_course_ids(
                student.pid, course_id
            )
            if existing_membership is None:
                membership_repo.create(
                    Membership(
                        user_pid=student.pid,
                        course_id=course_id,
                        type=MembershipType.STUDENT,
                        state=MembershipState.ENROLLED,
                    )
                )
                result.created += 1
            elif existing_membership.state != MembershipState.ENROLLED:
                existing_membership.state = MembershipState.ENROLLED
                session.flush()
                result.updated += 1
        except Exception as exc:
            result.errors.append(f"PID {student.pid}: {exc}")

    return result
