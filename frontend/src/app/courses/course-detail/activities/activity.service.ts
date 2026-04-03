import { Injectable, inject } from '@angular/core';
import { Api } from '../../../api/generated/api';
import { listActivities } from '../../../api/generated/fn/activities/list-activities';
import { getActivity } from '../../../api/generated/fn/activities/get-activity';
import { createIyowActivity } from '../../../api/generated/fn/activities/create-iyow-activity';
import { updateIyowActivity as updateIyowActivityFn } from '../../../api/generated/fn/activities/update-iyow-activity';
import { deleteActivity as deleteActivityFn } from '../../../api/generated/fn/activities/delete-activity';
import { submitIyowResponse } from '../../../api/generated/fn/activities/submit-iyow-response';
import { listSubmissions } from '../../../api/generated/fn/activities/list-submissions';
import { getActiveSubmission } from '../../../api/generated/fn/activities/get-active-submission';
import { getStudentSubmissionHistory } from '../../../api/generated/fn/activities/get-student-submission-history';
import {
  Activity,
  IyowActivity,
  IyowSubmission,
  CreateIyowActivity,
  UpdateIyowActivity,
} from '../../../api/models';

/** Handles HTTP communication with the student activities API. */
@Injectable({ providedIn: 'root' })
export class ActivityService {
  private api = inject(Api);

  /** Lists all activities for a course. */
  list(courseId: number): Promise<Activity[]> {
    return this.api.invoke(listActivities, { course_id: courseId });
  }

  /** Gets a single activity detail. */
  get(courseId: number, activityId: number): Promise<IyowActivity> {
    return this.api.invoke(getActivity, { course_id: courseId, activity_id: activityId });
  }

  /** Creates an IYOW activity. */
  createIyow(courseId: number, body: CreateIyowActivity): Promise<IyowActivity> {
    return this.api.invoke(createIyowActivity, { course_id: courseId, body });
  }

  /** Updates an IYOW activity. */
  updateIyow(
    courseId: number,
    activityId: number,
    body: UpdateIyowActivity,
  ): Promise<IyowActivity> {
    return this.api.invoke(updateIyowActivityFn, {
      course_id: courseId,
      activity_id: activityId,
      body,
    });
  }

  /** Deletes an activity. */
  delete(courseId: number, activityId: number): Promise<void> {
    return this.api.invoke(deleteActivityFn, { course_id: courseId, activity_id: activityId });
  }

  /** Submits a student response to an IYOW activity. */
  submitIyow(courseId: number, activityId: number, responseText: string): Promise<IyowSubmission> {
    return this.api.invoke(submitIyowResponse, {
      course_id: courseId,
      activity_id: activityId,
      body: { response_text: responseText },
    });
  }

  /** Lists submissions for an activity. */
  listSubmissions(courseId: number, activityId: number): Promise<IyowSubmission[]> {
    return this.api.invoke(listSubmissions, { course_id: courseId, activity_id: activityId });
  }

  /** Gets the student's current active submission. */
  getActiveSubmission(courseId: number, activityId: number): Promise<IyowSubmission | null> {
    return this.api.invoke(getActiveSubmission, { course_id: courseId, activity_id: activityId });
  }

  /** Gets all submissions for a specific student on an activity (instructor). */
  getStudentHistory(
    courseId: number,
    activityId: number,
    studentPid: number,
  ): Promise<IyowSubmission[]> {
    return this.api.invoke(getStudentSubmissionHistory, {
      course_id: courseId,
      activity_id: activityId,
      student_pid: studentPid,
    });
  }
}
