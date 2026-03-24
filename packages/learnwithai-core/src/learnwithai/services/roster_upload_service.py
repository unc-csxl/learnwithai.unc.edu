"""Service for parsing Canvas gradebook CSVs and importing roster members."""

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..db import get_engine
from ..interfaces import JobQueue
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


class RosterUploadService:
    """Orchestrates roster CSV upload creation and processing."""

    def __init__(
        self,
        upload_repo: RosterUploadRepository,
        user_repo: UserRepository,
        membership_repo: MembershipRepository,
    ):
        """Initializes the service with its repository dependencies.

        Args:
            upload_repo: Repository for roster upload job records.
            user_repo: Repository for user persistence.
            membership_repo: Repository for membership persistence.
        """
        self._upload_repo = upload_repo
        self._user_repo = user_repo
        self._membership_repo = membership_repo

    def submit_upload(
        self,
        subject: User,
        course_id: int,
        csv_text: str,
        job_queue: JobQueue,
    ) -> RosterUploadJob:
        """Creates a roster upload job record and enqueues it for processing.

        ``job_queue`` is accepted as a method parameter rather than a
        constructor dependency because the ``learnwithai-core`` package
        cannot import from ``learnwithai-jobqueue`` without creating a
        circular package dependency.  Callers from the API layer pass the
        real ``JobQueue`` implementation; job handler callers never invoke
        this method.

        Args:
            subject: The authenticated user submitting the upload.
            course_id: Primary key of the course to import into.
            csv_text: Raw UTF-8 Canvas gradebook CSV content.
            job_queue: Queue used to dispatch the background job.

        Returns:
            The persisted upload job with its assigned ID and PENDING status.
        """
        from ..jobs.roster_upload import RosterUploadJob as RosterUploadJobPayload

        job = self._upload_repo.create(
            RosterUploadJob(
                course_id=course_id,
                uploaded_by_pid=subject.pid,
                csv_data=csv_text,
            )
        )
        assert job.id is not None
        job_queue.enqueue(RosterUploadJobPayload(job_id=job.id))
        return job

    def process_upload(self, job_id: int) -> None:
        """Processes a roster upload job: parses CSV and upserts users/memberships.

        Does not manage the database session or transaction — the caller is
        responsible for committing or rolling back.

        Args:
            job_id: Primary key of the RosterUploadJob to process.

        Raises:
            ValueError: If the job does not exist.
        """
        job = self._upload_repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"RosterUploadJob {job_id} not found")

        job.status = RosterUploadStatus.PROCESSING
        self._upload_repo.update(job)

        students = parse_canvas_csv(job.csv_data)
        result = self._import_students(job.course_id, students)

        job.status = RosterUploadStatus.COMPLETED
        job.created_count = result.created
        job.updated_count = result.updated
        job.error_count = len(result.errors)
        job.error_details = "\n".join(result.errors) if result.errors else None
        job.completed_at = datetime.now(timezone.utc)
        self._upload_repo.update(job)

    def mark_failed(self, job_id: int) -> None:
        """Marks a roster upload job as failed.

        Best-effort: all exceptions are swallowed so that a failure during
        error-marking does not hide the original exception.

        Args:
            job_id: Primary key of the RosterUploadJob to mark failed.
        """
        try:
            job = self._upload_repo.get_by_id(job_id)
            if job is not None:
                job.status = RosterUploadStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                self._upload_repo.update(job)
        except Exception:
            pass

    def _import_students(
        self, course_id: int, students: list[ParsedStudent]
    ) -> ImportResult:
        """Creates or updates users and memberships for parsed students.

        Args:
            course_id: Course to add students to.
            students: Parsed student records from the CSV.

        Returns:
            An ImportResult summarizing counts and errors.
        """
        result = ImportResult()

        for student in students:
            try:
                existing_user = self._user_repo.get_by_pid(student.pid)
                if existing_user is None:
                    self._user_repo.register_user(
                        User(
                            pid=student.pid,
                            name=f"{student.given_name} {student.family_name}",
                            onyen=student.onyen,
                            given_name=student.given_name,
                            family_name=student.family_name,
                            email=f"{student.onyen}@unc.edu",
                        )
                    )

                existing_membership = self._membership_repo.get_by_user_and_course_ids(
                    student.pid, course_id
                )
                if existing_membership is None:
                    self._membership_repo.create(
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
                    self._membership_repo.update(existing_membership)
                    result.updated += 1
            except Exception as exc:
                result.errors.append(f"PID {student.pid}: {exc}")

        return result


def process_roster_upload(job_id: int) -> None:
    """Backward-compatibility shim used by the job handler.

    Opens its own session and delegates to ``RosterUploadService``.
    This function will be removed once ``RosterUploadJobHandler`` manages
    its own session lifecycle directly.

    Args:
        job_id: Primary key of the RosterUploadJob to process.
    """
    from sqlmodel import Session as _Session

    engine = get_engine()
    with _Session(engine) as session:
        upload_repo = RosterUploadRepository(session)
        user_repo = UserRepository(session)
        membership_repo = MembershipRepository(session)
        svc = RosterUploadService(upload_repo, user_repo, membership_repo)
        try:
            svc.process_upload(job_id)
            session.commit()
        except Exception:
            session.rollback()
            svc.mark_failed(job_id)
            session.commit()
            raise

