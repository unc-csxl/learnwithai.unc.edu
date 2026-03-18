import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AddMemberRequest } from '../api/generated/models/add-member-request';
import { CourseResponse } from '../api/generated/models/course-response';
import { CreateCourseRequest } from '../api/generated/models/create-course-request';
import { MembershipResponse } from '../api/generated/models/membership-response';

/** Handles HTTP communication with the course management API. */
@Injectable({ providedIn: 'root' })
export class CourseService {
  private http = inject(HttpClient);

  /** Fetches courses the current user is enrolled in. */
  getMyCourses(): Observable<CourseResponse[]> {
    return this.http.get<CourseResponse[]>('/api/courses');
  }

  /** Creates a new course. */
  createCourse(request: CreateCourseRequest): Observable<CourseResponse> {
    return this.http.post<CourseResponse>('/api/courses', request);
  }

  /** Fetches the roster for a course. */
  getRoster(courseId: number): Observable<MembershipResponse[]> {
    return this.http.get<MembershipResponse[]>(`/api/courses/${courseId}/roster`);
  }

  /** Adds a member to a course. */
  addMember(courseId: number, request: AddMemberRequest): Observable<MembershipResponse> {
    return this.http.post<MembershipResponse>(`/api/courses/${courseId}/members`, request);
  }

  /** Drops a member from a course. */
  dropMember(courseId: number, pid: number): Observable<MembershipResponse> {
    return this.http.delete<MembershipResponse>(`/api/courses/${courseId}/members/${pid}`);
  }
}
