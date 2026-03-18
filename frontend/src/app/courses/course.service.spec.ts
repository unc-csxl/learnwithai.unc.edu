import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { CourseService } from './course.service';
import { CourseResponse } from '../api/generated/models/course-response';
import { MembershipResponse } from '../api/generated/models/membership-response';

describe('CourseService', () => {
  let service: CourseService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CourseService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpTesting.verify());

  it('fetches courses from GET /api/courses', () => {
    const mockCourses: CourseResponse[] = [
      { id: 1, name: 'Intro', term: 'Fall 2026', section: '001' },
    ];
    service.getMyCourses().subscribe((courses) => {
      expect(courses).toEqual(mockCourses);
    });
    const req = httpTesting.expectOne('/api/courses');
    expect(req.request.method).toBe('GET');
    req.flush(mockCourses);
  });

  it('creates a course via POST /api/courses', () => {
    const created: CourseResponse = {
      id: 2,
      name: 'Algo',
      term: 'Spring 2027',
      section: '002',
    };
    service
      .createCourse({ name: 'Algo', term: 'Spring 2027', section: '002' })
      .subscribe((course) => {
        expect(course).toEqual(created);
      });
    const req = httpTesting.expectOne('/api/courses');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      name: 'Algo',
      term: 'Spring 2027',
      section: '002',
    });
    req.flush(created);
  });

  it('fetches roster via GET /api/courses/:id/roster', () => {
    const members: MembershipResponse[] = [
      {
        user_pid: 123,
        course_id: 1,
        type: 'instructor',
        state: 'enrolled',
      },
    ];
    service.getRoster(1).subscribe((roster) => {
      expect(roster).toEqual(members);
    });
    const req = httpTesting.expectOne('/api/courses/1/roster');
    expect(req.request.method).toBe('GET');
    req.flush(members);
  });

  it('adds a member via POST /api/courses/:id/members', () => {
    const member: MembershipResponse = {
      user_pid: 999,
      course_id: 1,
      type: 'student',
      state: 'pending',
    };
    service.addMember(1, { pid: 999, type: 'student' }).subscribe((m) => expect(m).toEqual(member));
    const req = httpTesting.expectOne('/api/courses/1/members');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ pid: 999, type: 'student' });
    req.flush(member);
  });

  it('drops a member via DELETE /api/courses/:id/members/:pid', () => {
    const member: MembershipResponse = {
      user_pid: 999,
      course_id: 1,
      type: 'student',
      state: 'dropped',
    };
    service.dropMember(1, 999).subscribe((m) => expect(m).toEqual(member));
    const req = httpTesting.expectOne('/api/courses/1/members/999');
    expect(req.request.method).toBe('DELETE');
    req.flush(member);
  });
});
