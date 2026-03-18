import { TestBed } from '@angular/core/testing';
import { CourseService } from './course.service';
import { Api } from '../api/generated/api';
import { listMyCourses } from '../api/generated/fn/courses/list-my-courses';
import { createCourse } from '../api/generated/fn/courses/create-course';
import { getCourseRoster } from '../api/generated/fn/courses/get-course-roster';
import { addMember } from '../api/generated/fn/courses/add-member';
import { dropMember } from '../api/generated/fn/courses/drop-member';
import { Course, Membership } from '../api/models';

describe('CourseService', () => {
  let service: CourseService;
  let api: { invoke: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    api = { invoke: vi.fn() };
    TestBed.configureTestingModule({
      providers: [{ provide: Api, useValue: api }],
    });
    service = TestBed.inject(CourseService);
  });

  it('fetches courses via listMyCourses', async () => {
    const mockCourses: Course[] = [{ id: 1, name: 'Intro', term: 'Fall 2026', section: '001' }];
    api.invoke.mockResolvedValue(mockCourses);
    const result = await service.getMyCourses();
    expect(result).toEqual(mockCourses);
    expect(api.invoke).toHaveBeenCalledWith(listMyCourses);
  });

  it('creates a course via createCourse', async () => {
    const created: Course = { id: 2, name: 'Algo', term: 'Spring 2027', section: '002' };
    api.invoke.mockResolvedValue(created);
    const result = await service.createCourse({
      name: 'Algo',
      term: 'Spring 2027',
      section: '002',
    });
    expect(result).toEqual(created);
    expect(api.invoke).toHaveBeenCalledWith(createCourse, {
      body: { name: 'Algo', term: 'Spring 2027', section: '002' },
    });
  });

  it('fetches roster via getCourseRoster', async () => {
    const members: Membership[] = [
      { user_pid: 123, course_id: 1, type: 'instructor', state: 'enrolled' },
    ];
    api.invoke.mockResolvedValue(members);
    const result = await service.getRoster(1);
    expect(result).toEqual(members);
    expect(api.invoke).toHaveBeenCalledWith(getCourseRoster, { course_id: 1 });
  });

  it('adds a member via addMember', async () => {
    const member: Membership = { user_pid: 999, course_id: 1, type: 'student', state: 'pending' };
    api.invoke.mockResolvedValue(member);
    const result = await service.addMember(1, { pid: 999, type: 'student' });
    expect(result).toEqual(member);
    expect(api.invoke).toHaveBeenCalledWith(addMember, {
      course_id: 1,
      body: { pid: 999, type: 'student' },
    });
  });

  it('drops a member via dropMember', async () => {
    const member: Membership = { user_pid: 999, course_id: 1, type: 'student', state: 'dropped' };
    api.invoke.mockResolvedValue(member);
    const result = await service.dropMember(1, 999);
    expect(result).toEqual(member);
    expect(api.invoke).toHaveBeenCalledWith(dropMember, { course_id: 1, pid: 999 });
  });
});
