# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Business logic for IYOW student submissions and feedback."""

from datetime import datetime

from ...errors import AuthorizationError
from ...interfaces import JobQueue
from ...repositories.activity_repository import ActivityRepository
from ...repositories.async_job_repository import AsyncJobRepository
from ...repositories.membership_repository import MembershipRepository
from ...repositories.submission_repository import SubmissionRepository
from ...tables.activity import Activity, ActivityType
from ...tables.async_job import AsyncJob, AsyncJobStatus
from ...tables.course import Course
from ...tables.membership import MembershipType
from ...tables.submission import Submission
from ...tables.user import User
from .models import IYOW_FEEDBACK_KIND, IyowFeedbackJob
from .repository import IyowActivityRepository, IyowSubmissionRepository
from .tables import IyowSubmission


class IyowSubmissionService:
    """Orchestrates student submissions for In Your Own Words activities."""

    def __init__(
        self,
        activity_repo: ActivityRepository,
        iyow_activity_repo: IyowActivityRepository,
        submission_repo: SubmissionRepository,
        iyow_submission_repo: IyowSubmissionRepository,
        async_job_repo: AsyncJobRepository,
        membership_repo: MembershipRepository,
        job_queue: JobQueue,
    ):
        """Initializes the service with its dependencies.

        Args:
            activity_repo: Repository for base activity records.
            iyow_activity_repo: Repository for IYOW activity details.
            submission_repo: Repository for base submission records.
            iyow_submission_repo: Repository for IYOW submission details.
            async_job_repo: Repository for async job tracking.
            membership_repo: Repository for course membership lookups.
            job_queue: Queue used to dispatch feedback jobs.
        """
        self._activity_repo = activity_repo
        self._iyow_activity_repo = iyow_activity_repo
        self._submission_repo = submission_repo
        self._iyow_submission_repo = iyow_submission_repo
        self._async_job_repo = async_job_repo
        self._membership_repo = membership_repo
        self._job_queue = job_queue

    def submit(
        self,
        subject: User,
        course: Course,
        activity: Activity,
        response_text: str,
        now: datetime,
    ) -> tuple[Submission, IyowSubmission]:
        """Submits (or resubmits) a student response to an IYOW activity.

        Deactivates any existing active submission, creates a new
        base submission and IYOW detail, and enqueues a feedback job.

        Args:
            subject: Authenticated student submitting the response.
            course: Course the activity belongs to.
            activity: The IYOW activity being submitted to.
            response_text: The student's written response.
            now: Current timestamp for deadline enforcement.

        Returns:
            A tuple of the base submission and IYOW detail.

        Raises:
            AuthorizationError: If the subject is not an enrolled student.
            ValueError: If the activity is not released, past deadline,
                or not an IYOW activity.
        """
        self._authorize_submitter(subject, course)
        self._validate_submission_window(activity, now)

        assert activity.id is not None
        assert course.id is not None

        # Deactivate any existing active submission
        self._submission_repo.deactivate_active(activity.id, subject.pid)

        # Create base submission
        submission = self._submission_repo.create(
            Submission(
                activity_id=activity.id,
                student_pid=subject.pid,
                is_active=True,
                submitted_at=now,
            )
        )
        assert submission.id is not None

        # Create async job for LLM feedback
        async_job = self._async_job_repo.create(
            AsyncJob(
                course_id=course.id,
                created_by_pid=subject.pid,
                kind=IYOW_FEEDBACK_KIND,
                status=AsyncJobStatus.PENDING,
                input_data={},
            )
        )
        assert async_job.id is not None

        # Create IYOW-specific detail
        iyow_submission = self._iyow_submission_repo.create(
            IyowSubmission(
                submission_id=submission.id,
                response_text=response_text,
                async_job_id=async_job.id,
            )
        )

        # Enqueue feedback job
        self._job_queue.enqueue(IyowFeedbackJob(job_id=async_job.id))

        return submission, iyow_submission

    def get_active_submission(
        self,
        subject: User,
        course: Course,
        activity: Activity,
    ) -> tuple[Submission, IyowSubmission] | None:
        """Returns the student's current active submission for an activity.

        Args:
            subject: Authenticated student.
            course: Course the activity belongs to.
            activity: The IYOW activity.

        Returns:
            A tuple of the base and IYOW submissions, or ``None`` if no
            active submission exists.

        Raises:
            AuthorizationError: If the subject is not a course member.
        """
        self._authorize_member(subject, course)
        assert activity.id is not None

        submission = self._submission_repo.get_active_for_student(activity.id, subject.pid)
        if submission is None:
            return None

        assert submission.id is not None
        iyow_detail = self._iyow_submission_repo.get_by_submission_id(submission.id)
        if iyow_detail is None:
            return None

        return submission, iyow_detail

    def get_student_submissions(
        self,
        subject: User,
        course: Course,
        activity: Activity,
    ) -> list[tuple[Submission, IyowSubmission]]:
        """Returns all of a student's submissions for an activity.

        Includes both active and inactive submissions, newest first.

        Args:
            subject: Authenticated student.
            course: Course the activity belongs to.
            activity: The IYOW activity.

        Returns:
            A list of (base submission, IYOW detail) tuples.

        Raises:
            AuthorizationError: If the subject is not a course member.
        """
        self._authorize_member(subject, course)
        assert activity.id is not None

        submissions = self._submission_repo.list_by_student_and_activity(activity.id, subject.pid)
        results: list[tuple[Submission, IyowSubmission]] = []
        for sub in submissions:
            assert sub.id is not None
            iyow_detail = self._iyow_submission_repo.get_by_submission_id(sub.id)
            if iyow_detail is not None:
                results.append((sub, iyow_detail))
        return results

    def list_submissions_for_activity(
        self,
        subject: User,
        course: Course,
        activity: Activity,
    ) -> list[tuple[Submission, IyowSubmission]]:
        """Returns all active submissions for an activity (instructor view).

        Only instructors and TAs may call this method.

        Args:
            subject: Authenticated instructor or TA.
            course: Course the activity belongs to.
            activity: The IYOW activity.

        Returns:
            A list of (base submission, IYOW detail) tuples for all students.

        Raises:
            AuthorizationError: If the subject is not staff.
        """
        self._authorize_staff(subject, course)
        assert activity.id is not None

        return self._list_active_submission_pairs(activity.id)

    def list_submissions_with_roster(
        self,
        subject: User,
        course: Course,
        activity: Activity,
    ) -> list[tuple[User, Submission | None, IyowSubmission | None]]:
        """Returns every enrolled student paired with their active submission.

        Students who have not submitted are included with ``None`` values
        for the submission pair.  Only instructors and TAs may call this.

        Args:
            subject: Authenticated instructor or TA.
            course: Course the activity belongs to.
            activity: The IYOW activity.

        Returns:
            A list of (user, submission-or-None, iyow-detail-or-None) tuples
            for every enrolled student, ordered by family name then given name.

        Raises:
            AuthorizationError: If the subject is not staff.
        """
        self._authorize_staff(subject, course)
        assert activity.id is not None

        enrolled = self._membership_repo.get_enrolled_students(course)
        active_submissions_by_pid = {
            submission.student_pid: (submission, detail)
            for submission, detail in self._list_active_submission_pairs(activity.id)
        }

        results: list[tuple[User, Submission | None, IyowSubmission | None]] = []
        for membership in enrolled:
            user = membership.user
            assert user is not None
            sub, iyow_detail = active_submissions_by_pid.get(user.pid, (None, None))
            results.append((user, sub, iyow_detail))

        results.sort(key=lambda t: ((t[0].family_name or "").lower(), (t[0].given_name or "").lower()))
        return results

    def get_student_submission_history(
        self,
        subject: User,
        course: Course,
        activity: Activity,
        student_pid: int,
    ) -> list[tuple[Submission, IyowSubmission]]:
        """Returns all submissions for a specific student (instructor view).

        Includes both active and inactive submissions, newest first.
        Only instructors and TAs may call this method.

        Args:
            subject: Authenticated instructor or TA.
            course: Course the activity belongs to.
            activity: The IYOW activity.
            student_pid: PID of the student whose history is requested.

        Returns:
            A list of (base submission, IYOW detail) tuples.

        Raises:
            AuthorizationError: If the subject is not staff.
        """
        self._authorize_staff(subject, course)
        assert activity.id is not None

        submissions = self._submission_repo.list_by_student_and_activity(activity.id, student_pid)
        results: list[tuple[Submission, IyowSubmission]] = []
        for sub in submissions:
            assert sub.id is not None
            iyow_detail = self._iyow_submission_repo.get_by_submission_id(sub.id)
            if iyow_detail is not None:
                results.append((sub, iyow_detail))
        return results

    def _list_active_submission_pairs(self, activity_id: int) -> list[tuple[Submission, IyowSubmission]]:
        """Loads active submission/detail pairs for an activity in one query."""
        results: list[tuple[Submission, IyowSubmission]] = []
        for iyow_detail in self._iyow_submission_repo.list_active_for_activity(activity_id):
            submission = iyow_detail.submission
            assert submission is not None
            results.append((submission, iyow_detail))
        return results

    def _validate_submission_window(self, activity: Activity, now: datetime) -> None:
        """Verifies the activity is open for submissions.

        Args:
            activity: The activity to check.
            now: Current timestamp.

        Raises:
            ValueError: If the activity is not yet released or past deadline.
        """
        if activity.type != ActivityType.IYOW:
            raise ValueError("Activity is not an IYOW activity")
        if activity.release_date > now:
            raise ValueError("Activity is not yet released")
        cutoff = activity.late_date if activity.late_date else activity.due_date
        if now > cutoff:
            raise ValueError("Submission deadline has passed")

    def _authorize_submitter(self, subject: User, course: Course) -> None:
        """Verifies the subject is an enrolled course member who may submit.

        Students, instructors, and TAs are all permitted to submit.
        Staff submissions serve as preview / test runs.

        Args:
            subject: User to authorize.
            course: Course to check membership for.

        Raises:
            AuthorizationError: If the subject is not a course member.
        """
        membership = self._membership_repo.get_by_user_and_course(subject, course)
        if membership is None:
            raise AuthorizationError("Not a member of this course")

    def _authorize_member(self, subject: User, course: Course) -> None:
        """Verifies the subject is a course member.

        Args:
            subject: User to authorize.
            course: Course to check membership for.

        Raises:
            AuthorizationError: If the subject is not a member.
        """
        membership = self._membership_repo.get_by_user_and_course(subject, course)
        if membership is None:
            raise AuthorizationError("Not a member of this course")

    def _authorize_staff(self, subject: User, course: Course) -> None:
        """Verifies the subject is an instructor or TA.

        Args:
            subject: User to authorize.
            course: Course to check membership for.

        Raises:
            AuthorizationError: If the subject is not staff.
        """
        membership = self._membership_repo.get_by_user_and_course(subject, course)
        if membership is None:
            raise AuthorizationError("Not a member of this course")
        if membership.type not in {MembershipType.INSTRUCTOR, MembershipType.TA}:
            raise AuthorizationError("Insufficient permissions")
