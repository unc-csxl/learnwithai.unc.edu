import { Injectable, inject } from '@angular/core';
import { Api } from '../api/generated/api';
import { listMyCourses } from '../api/generated/fn/courses/list-my-courses';
import { createCourse as createCourseFn } from '../api/generated/fn/courses/create-course';
import { getCourseRoster } from '../api/generated/fn/courses/get-course-roster';
import { addMember as addMemberFn } from '../api/generated/fn/courses/add-member';
import { dropMember as dropMemberFn } from '../api/generated/fn/courses/drop-member';
import { Course, CreateCourse, Membership, AddMember } from '../api/models';

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

  /** Fetches the roster for a course. */
  getRoster(courseId: number): Promise<Membership[]> {
    return this.api.invoke(getCourseRoster, { course_id: courseId });
  }

  /** Adds a member to a course. */
  addMember(courseId: number, request: AddMember): Promise<Membership> {
    return this.api.invoke(addMemberFn, { course_id: courseId, body: request });
  }

  /** Drops a member from a course. */
  dropMember(courseId: number, pid: number): Promise<Membership> {
    return this.api.invoke(dropMemberFn, { course_id: courseId, pid });
  }
}
