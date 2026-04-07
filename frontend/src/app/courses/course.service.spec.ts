/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { CourseService } from './course.service';
import { Api } from '../api/generated/api';
import { listMyCourses } from '../api/generated/fn/courses/list-my-courses';
import { createCourse } from '../api/generated/fn/courses/create-course';
import { updateCourse } from '../api/generated/fn/courses/update-course';
import { getCourseRoster } from '../api/generated/fn/courses/get-course-roster';
import { addMember } from '../api/generated/fn/courses/add-member';
import { dropMember } from '../api/generated/fn/courses/drop-member';
import { uploadRosterCsv } from '../api/generated/fn/roster-uploads/upload-roster-csv';
import { getRosterUploadStatus as getRosterUploadStatusFn } from '../api/generated/fn/roster-uploads/get-roster-upload-status';
import {
  Course,
  PaginatedRoster,
  Membership,
  RosterUpload,
  RosterUploadStatus,
} from '../api/models';

describe('CourseService', () => {
  let service: CourseService;
  let api: { invoke: ReturnType<typeof vi.fn> };

  const membership = { type: 'student', state: 'enrolled' } as const;

  beforeEach(() => {
    api = { invoke: vi.fn() };
    TestBed.configureTestingModule({
      providers: [{ provide: Api, useValue: api }],
    });
    service = TestBed.inject(CourseService);
  });

  it('fetches courses via listMyCourses', async () => {
    const mockCourses: Course[] = [
      {
        id: 1,
        course_number: 'COMP101',
        name: 'Intro',
        description: '',
        term: 'fall',
        year: 2026,
        membership,
      },
    ];
    api.invoke.mockResolvedValue(mockCourses);
    const result = await service.getMyCourses();
    expect(result).toEqual(mockCourses);
    expect(api.invoke).toHaveBeenCalledWith(listMyCourses);
  });

  it('creates a course via createCourse', async () => {
    const created: Course = {
      id: 2,
      course_number: 'COMP301',
      name: 'Algo',
      description: '',
      term: 'spring',
      year: 2027,
      membership: { type: 'instructor', state: 'enrolled' },
    };
    api.invoke.mockResolvedValue(created);
    const result = await service.createCourse({
      course_number: 'COMP301',
      name: 'Algo',
      term: 'spring',
      year: 2027,
    });
    expect(result).toEqual(created);
    expect(api.invoke).toHaveBeenCalledWith(createCourse, {
      body: { course_number: 'COMP301', name: 'Algo', term: 'spring', year: 2027 },
    });
  });

  it('fetches roster via getCourseRoster', async () => {
    const response: PaginatedRoster = {
      items: [
        {
          user_pid: 123,
          course_id: 1,
          type: 'instructor',
          state: 'enrolled',
          given_name: 'Jane',
          family_name: 'Doe',
          email: 'jane@unc.edu',
        },
      ],
      total: 1,
      page: 1,
      page_size: 25,
    };
    api.invoke.mockResolvedValue(response);
    const result = await service.getRoster(1);
    expect(result).toEqual(response);
    expect(api.invoke).toHaveBeenCalledWith(getCourseRoster, {
      course_id: 1,
      page: undefined,
      page_size: undefined,
      q: undefined,
    });
  });

  it('passes pagination and query params to getCourseRoster', async () => {
    const response: PaginatedRoster = { items: [], total: 0, page: 2, page_size: 10 };
    api.invoke.mockResolvedValue(response);
    const result = await service.getRoster(1, { page: 2, pageSize: 10, query: 'alice' });
    expect(result).toEqual(response);
    expect(api.invoke).toHaveBeenCalledWith(getCourseRoster, {
      course_id: 1,
      page: 2,
      page_size: 10,
      q: 'alice',
    });
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

  it('uploads a roster CSV via uploadRosterCsv', async () => {
    const upload: RosterUpload = { id: 10, status: 'pending' };
    api.invoke.mockResolvedValue(upload);
    const file = new Blob(['csv'], { type: 'text/csv' });
    const result = await service.uploadRoster(1, file);
    expect(result).toEqual(upload);
    expect(api.invoke).toHaveBeenCalledWith(uploadRosterCsv, {
      course_id: 1,
      body: { file: file as unknown as string },
    });
  });

  it('fetches roster upload status via getRosterUploadStatus', async () => {
    const status: RosterUploadStatus = {
      id: 10,
      status: 'completed',
      created_count: 5,
      updated_count: 2,
      error_count: 0,
      error_details: null,
      created_at: '2025-01-01T00:00:00',
      completed_at: '2025-01-01T00:00:05',
    };
    api.invoke.mockResolvedValue(status);
    const result = await service.getRosterUploadStatus(1, 10);
    expect(result).toEqual(status);
    expect(api.invoke).toHaveBeenCalledWith(getRosterUploadStatusFn, {
      course_id: 1,
      job_id: 10,
    });
  });

  it('updates a course via updateCourse', async () => {
    const updated: Course = {
      id: 1,
      course_number: 'COMP423',
      name: 'Updated Name',
      description: 'New desc',
      term: 'fall',
      year: 2026,
      membership: { type: 'instructor', state: 'enrolled' },
    };
    api.invoke.mockResolvedValue(updated);
    const result = await service.updateCourse(1, {
      course_number: 'COMP423',
      name: 'Updated Name',
      description: 'New desc',
      term: 'fall',
      year: 2026,
    });
    expect(result).toEqual(updated);
    expect(api.invoke).toHaveBeenCalledWith(updateCourse, {
      course_id: 1,
      body: {
        course_number: 'COMP423',
        name: 'Updated Name',
        description: 'New desc',
        term: 'fall',
        year: 2026,
      },
    });
  });
});
