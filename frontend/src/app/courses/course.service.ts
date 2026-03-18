import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Course, CreateCourseRequest, Membership, AddMemberRequest } from './course.model';

/** Handles HTTP communication with the course management API. */
@Injectable({ providedIn: 'root' })
export class CourseService {
  private http = inject(HttpClient);

  /** Fetches courses the current user is enrolled in. */
  getMyCourses(): Observable<Course[]> {
    return this.http.get<Course[]>('/api/courses');
  }

  /** Creates a new course. */
  createCourse(request: CreateCourseRequest): Observable<Course> {
    return this.http.post<Course>('/api/courses', request);
  }

  /** Fetches the roster for a course. */
  getRoster(courseId: number): Observable<Membership[]> {
    return this.http.get<Membership[]>(`/api/courses/${courseId}/roster`);
  }

  /** Adds a member to a course. */
  addMember(courseId: number, request: AddMemberRequest): Observable<Membership> {
    return this.http.post<Membership>(`/api/courses/${courseId}/members`, request);
  }

  /** Drops a member from a course. */
  dropMember(courseId: number, pid: number): Observable<Membership> {
    return this.http.delete<Membership>(`/api/courses/${courseId}/members/${pid}`);
  }
}
