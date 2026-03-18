import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { CourseList } from './course-list';
import { CourseService } from '../course.service';
import { CourseResponse } from '../../api/generated/models/course-response';

const fakeCourses: CourseResponse[] = [
  { id: 1, name: 'Intro to CS', term: 'Fall 2026', section: '001' },
  { id: 2, name: 'Data Structures', term: 'Spring 2027', section: '001' },
];

describe('CourseList', () => {
  function setup(options: { courses?: CourseResponse[]; error?: boolean } = {}) {
    const mockService = {
      getMyCourses: options.error
        ? vi.fn(() => throwError(() => new Error('fail')))
        : vi.fn(() => of(options.courses ?? fakeCourses)),
    };

    TestBed.configureTestingModule({
      imports: [CourseList],
      providers: [provideRouter([]), { provide: CourseService, useValue: mockService }],
    });

    const fixture = TestBed.createComponent(CourseList);
    fixture.detectChanges();
    return { fixture, mockService };
  }

  it('should display courses when available', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const items = el.querySelectorAll('li');
    expect(items.length).toBe(2);
    expect(items[0].textContent).toContain('Intro to CS');
  });

  it('should display empty message when no courses', () => {
    const { fixture } = setup({ courses: [] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('not enrolled in any courses');
  });

  it('should show create course link', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const createLink = el.querySelector('a[href="/courses/create"]');
    expect(createLink).toBeTruthy();
  });

  it('should load courses from service', () => {
    const { mockService } = setup();
    expect(mockService.getMyCourses).toHaveBeenCalled();
  });

  it('should handle errors gracefully', () => {
    const { fixture } = setup({ error: true });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('not enrolled in any courses');
  });
});
