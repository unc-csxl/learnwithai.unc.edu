"""Service for parsing Canvas gradebook CSVs and importing roster members."""

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..interfaces import JobQueue
from ..jobs.roster_upload import RosterUploadOutput
from ..repositories.async_job_repository import AsyncJobRepository
from ..repositories.membership_repository import MembershipRepository
from ..repositories.user_repository import UserRepository
from ..tables.async_job import AsyncJob, AsyncJobStatus
from ..tables.membership import Membership, MembershipState, MembershipType
from ..tables.user import User

ROSTER_UPLOAD_KIND = "roster_upload"


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


class RosterUploadService:
    """Orchestrates roster CSV upload creation and processing."""

    def __init__(
        self,
        async_job_repo: AsyncJobRepository,
        user_repo: UserRepository,
        membership_repo: MembershipRepository,
        job_queue: JobQueue,
    ):
        """Initializes the service with its dependencies.

        Args:
            async_job_repo: Repository for unified async job records.
            user_repo: Repository for user persistence.
            membership_repo: Repository for membership persistence.
            job_queue: Queue used to dispatch background jobs.
        """
        self._async_job_repo = async_job_repo
        self._user_repo = user_repo
        self._membership_repo = membership_repo
        self._job_queue = job_queue

    def submit_upload(
        self,
        subject: User,
        course_id: int,
        csv_text: str,
    ) -> AsyncJob:
        """Creates a roster upload job record and enqueues it for processing.

        Args:
            subject: The authenticated user submitting the upload.
            course_id: Primary key of the course to import into.
            csv_text: Raw UTF-8 Canvas gradebook CSV content.

        Returns:
            The persisted async job with its assigned ID and PENDING status.
        """
        from ..jobs.roster_upload import RosterUploadJob as RosterUploadJobPayload

        job = self._async_job_repo.create(
            AsyncJob(
                course_id=course_id,
                created_by_pid=subject.pid,
                kind=ROSTER_UPLOAD_KIND,
                input_data={"csv_text": csv_text},
            )
        )
        assert job.id is not None
        self._job_queue.enqueue(RosterUploadJobPayload(job_id=job.id))
        return job

    def process_upload(self, job_id: int) -> None:
        """Processes a roster upload job: parses CSV and upserts users/memberships.

        The caller (:class:`BaseJobHandler`) is responsible for setting the
        ``PROCESSING`` status before calling this method and for committing
        or rolling back the session afterward.

        Args:
            job_id: Primary key of the AsyncJob to process.

        Raises:
            ValueError: If the job does not exist.
        """
        job = self._async_job_repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"AsyncJob {job_id} not found")

        csv_text = job.input_data.get("csv_text", "")
        students = self._parse_canvas_csv(csv_text)
        result = self._import_students(job.course_id, students)

        job.status = AsyncJobStatus.COMPLETED
        job.output_data = RosterUploadOutput(  # type: ignore[assignment]
            created_count=result.created,
            updated_count=result.updated,
            error_count=len(result.errors),
            error_details="\n".join(result.errors) if result.errors else None,
        )
        job.completed_at = datetime.now(timezone.utc)
        self._async_job_repo.update(job)

    def _parse_canvas_csv(self, csv_text: str) -> list[ParsedStudent]:
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

    def _import_students(self, course_id: int, students: list[ParsedStudent]) -> ImportResult:
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

                existing_membership = self._membership_repo.get_by_user_and_course_ids(student.pid, course_id)
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
