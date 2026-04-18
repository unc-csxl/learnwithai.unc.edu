/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Injectable, inject } from '@angular/core';
import { Api } from '../../../api/generated/api';
import { listActivities } from '../../../api/generated/fn/activities/list-activities';
import { getIyowActivity } from '../../../api/generated/fn/activities/get-iyow-activity';
import { createIyowActivity } from '../../../api/generated/fn/activities/create-iyow-activity';
import { updateIyowActivity as updateIyowActivityFn } from '../../../api/generated/fn/activities/update-iyow-activity';
import { deleteActivity as deleteActivityFn } from '../../../api/generated/fn/activities/delete-activity';
import { submitIyowResponse } from '../../../api/generated/fn/activities/submit-iyow-response';
import { listIyowSubmissions } from '../../../api/generated/fn/activities/list-iyow-submissions';
import { listIyowSubmissionsRoster } from '../../../api/generated/fn/activities/list-iyow-submissions-roster';
import { getIyowActiveSubmission } from '../../../api/generated/fn/activities/get-iyow-active-submission';
import { getIyowStudentSubmissionHistory } from '../../../api/generated/fn/activities/get-iyow-student-submission-history';
import {
  Activity,
  IyowActivity,
  IyowSubmission,
  CreateIyowActivity,
  IyowStudentSubmissionRow,
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

  /** Gets a single IYOW activity detail. */
  getIyow(courseId: number, activityId: number): Promise<IyowActivity> {
    return this.api.invoke(getIyowActivity, { course_id: courseId, activity_id: activityId });
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

  /** Lists IYOW submissions for an activity. */
  listIyowSubmissions(courseId: number, activityId: number): Promise<IyowSubmission[]> {
    return this.api.invoke(listIyowSubmissions, { course_id: courseId, activity_id: activityId });
  }

  /** Lists all enrolled students paired with their active IYOW submission (instructor view). */
  listIyowSubmissionsRoster(
    courseId: number,
    activityId: number,
  ): Promise<IyowStudentSubmissionRow[]> {
    return this.api.invoke(listIyowSubmissionsRoster, {
      course_id: courseId,
      activity_id: activityId,
    });
  }

  /** Gets the student's current active IYOW submission. */
  getIyowActiveSubmission(courseId: number, activityId: number): Promise<IyowSubmission | null> {
    return this.api.invoke(getIyowActiveSubmission, {
      course_id: courseId,
      activity_id: activityId,
    });
  }

  /** Gets all IYOW submissions for a specific student on an activity (instructor). */
  getIyowStudentHistory(
    courseId: number,
    activityId: number,
    studentPid: number,
  ): Promise<IyowSubmission[]> {
    return this.api.invoke(getIyowStudentSubmissionHistory, {
      course_id: courseId,
      activity_id: activityId,
      student_pid: studentPid,
    });
  }
}
