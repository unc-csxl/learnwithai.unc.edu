/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Injectable, inject } from '@angular/core';
import { Api } from '../api/generated/api';
import { listMyCourses } from '../api/generated/fn/courses/list-my-courses';
import { createCourse as createCourseFn } from '../api/generated/fn/courses/create-course';
import { updateCourse as updateCourseFn } from '../api/generated/fn/courses/update-course';
import { getCourseRoster } from '../api/generated/fn/courses/get-course-roster';
import { addMember as addMemberFn } from '../api/generated/fn/courses/add-member';
import { dropMember as dropMemberFn } from '../api/generated/fn/courses/drop-member';
import { updateMemberRole as updateMemberRoleFn } from '../api/generated/fn/courses/update-member-role';
import { uploadRosterCsv } from '../api/generated/fn/roster-uploads/upload-roster-csv';
import { getRosterUploadStatus as getRosterUploadStatusFn } from '../api/generated/fn/roster-uploads/get-roster-upload-status';
import {
  Course,
  CreateCourse,
  UpdateCourse,
  PaginatedRoster,
  Membership,
  AddMember,
  UpdateMemberRole,
  RosterUpload,
  RosterUploadStatus,
} from '../api/models';

/** Handles HTTP communication with the course management API. */
@Injectable({ providedIn: 'root' })
export class CourseService {
  private api = inject(Api);

  /** Fetches courses the current user is enrolled in. */
  getMyCourses(): Promise<Course[]> {
    return this.api.invoke(listMyCourses);
  }

  /** Creates a new course. */
  createCourse(request: CreateCourse): Promise<Course> {
    return this.api.invoke(createCourseFn, { body: request });
  }

  /** Updates an existing course. */
  updateCourse(courseId: number, request: UpdateCourse): Promise<Course> {
    return this.api.invoke(updateCourseFn, { course_id: courseId, body: request });
  }

  /** Fetches a paginated, optionally filtered roster for a course. */
  getRoster(
    courseId: number,
    options: { page?: number; pageSize?: number; query?: string } = {},
  ): Promise<PaginatedRoster> {
    return this.api.invoke(getCourseRoster, {
      course_id: courseId,
      page: options.page,
      page_size: options.pageSize,
      q: options.query,
    });
  }

  /** Adds a member to a course. */
  addMember(courseId: number, request: AddMember): Promise<Membership> {
    return this.api.invoke(addMemberFn, { course_id: courseId, body: request });
  }

  /** Drops a member from a course. */
  dropMember(courseId: number, pid: number): Promise<Membership> {
    return this.api.invoke(dropMemberFn, { course_id: courseId, pid });
  }

  /** Updates a member's role in a course. */
  updateMemberRole(courseId: number, pid: number, request: UpdateMemberRole): Promise<Membership> {
    return this.api.invoke(updateMemberRoleFn, {
      course_id: courseId,
      pid,
      body: request,
    });
  }

  /** Uploads a Canvas gradebook CSV for asynchronous roster import. */
  uploadRoster(courseId: number, file: Blob): Promise<RosterUpload> {
    return this.api.invoke(uploadRosterCsv, {
      course_id: courseId,
      body: { file: file as unknown as string },
    });
  }

  /** Polls the status of a roster upload job. */
  getRosterUploadStatus(courseId: number, jobId: number): Promise<RosterUploadStatus> {
    return this.api.invoke(getRosterUploadStatusFn, {
      course_id: courseId,
      job_id: jobId,
    });
  }
}
