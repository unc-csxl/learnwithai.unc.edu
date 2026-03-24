"""Roster CSV upload routes for the public API."""

from fastapi import APIRouter, HTTPException, UploadFile

from ..dependency_injection import (
    AuthenticatedUserDI,
    CourseByCourseIDPathDI,
    CourseServiceDI,
    JobQueueDI,
    RosterUploadRepositoryDI,
)
from ..models import RosterUploadResponse, RosterUploadStatusResponse
from learnwithai.jobs.roster_upload import RosterUploadJob as RosterUploadJobPayload
from learnwithai.tables.roster_upload_job import RosterUploadJob

router = APIRouter(
    prefix="/courses/{course_id}/roster-uploads", tags=["Roster Uploads"]
)


@router.post(
    "",
    response_model=RosterUploadResponse,
    status_code=202,
    summary="Upload a roster CSV",
    response_description="The accepted upload job.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Course not found."},
        400: {"description": "Invalid file."},
    },
)
async def upload_roster_csv(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    course_svc: CourseServiceDI,
    upload_repo: RosterUploadRepositoryDI,
    job_queue: JobQueueDI,
    file: UploadFile,
) -> RosterUploadResponse:
    """Accepts a Canvas gradebook CSV for asynchronous roster import.

    Only instructors may upload a roster CSV.

    Args:
        subject: Authenticated subject.
        course: Course loaded via DI from the path.
        course_svc: Service used for authorization check.
        upload_repo: Repository for persisting the upload job.
        job_queue: Queue for dispatching background work.
        file: Uploaded CSV file.

    Returns:
        The accepted upload job ID and status.
    """
    course_svc.authorize_instructor(subject, course)

    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(status_code=400, detail="File must be a CSV.")

    csv_bytes = await file.read()
    try:
        csv_text = csv_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    assert course.id is not None

    job = upload_repo.create(
        RosterUploadJob(
            course_id=course.id,
            uploaded_by_pid=subject.pid,
            csv_data=csv_text,
        )
    )

    assert job.id is not None
    job_queue.enqueue(RosterUploadJobPayload(job_id=job.id))

    return RosterUploadResponse(id=job.id, status=job.status)


@router.get(
    "/{job_id}",
    response_model=RosterUploadStatusResponse,
    summary="Get roster upload status",
    response_description="Current status of the upload job.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Course or job not found."},
    },
)
def get_roster_upload_status(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    course_svc: CourseServiceDI,
    upload_repo: RosterUploadRepositoryDI,
    job_id: int,
) -> RosterUploadStatusResponse:
    """Returns the current status and results of a roster upload job.

    Only instructors may check upload status.

    Args:
        subject: Authenticated subject.
        course: Course loaded via DI from the path.
        course_svc: Service used for authorization check.
        upload_repo: Repository for loading the upload job.
        job_id: Primary key of the upload job.

    Returns:
        The upload job status and result counts.
    """
    course_svc.authorize_instructor(subject, course)

    job = upload_repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Upload job not found.")

    assert course.id is not None
    if job.course_id != course.id:
        raise HTTPException(status_code=404, detail="Upload job not found.")

    return RosterUploadStatusResponse(
        id=job.id,  # type: ignore[arg-type]
        status=job.status,
        created_count=job.created_count,
        updated_count=job.updated_count,
        error_count=job.error_count,
        error_details=job.error_details,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
