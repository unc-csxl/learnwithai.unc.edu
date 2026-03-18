import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { CourseList } from './course-list.component';
import { CourseService } from '../course.service';
import { Course } from '../../api/models';

const fakeCourses: Course[] = [
  { id: 1, name: 'Intro to CS', term: 'Fall 2026', section: '001' },
  { id: 2, name: 'Data Structures', term: 'Spring 2027', section: '001' },
];

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('CourseList', () => {
  async function setup(options: { courses?: Course[]; error?: boolean } = {}) {
    const mockService = {
      getMyCourses: options.error
        ? vi.fn(() => Promise.reject(new Error('fail')))
        : vi.fn(() => Promise.resolve(options.courses ?? fakeCourses)),
    };

    TestBed.configureTestingModule({
      imports: [CourseList],
      providers: [provideRouter([]), { provide: CourseService, useValue: mockService }],
    });

    const fixture = TestBed.createComponent(CourseList);
    fixture.detectChanges();
    await flush();
    fixture.detectChanges();
    return { fixture, mockService };
  }

  it('should display courses when available', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const items = el.querySelectorAll('li');
    expect(items.length).toBe(2);
    expect(items[0].textContent).toContain('Intro to CS');
  });

  it('should display empty message when no courses', async () => {
    const { fixture } = await setup({ courses: [] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('not enrolled in any courses');
  });

  it('should show create course link', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const createLink = el.querySelector('a[href="/courses/create"]');
    expect(createLink).toBeTruthy();
  });

  it('should load courses from service', async () => {
    const { mockService } = await setup();
    expect(mockService.getMyCourses).toHaveBeenCalled();
  });

  it('should handle errors gracefully', async () => {
    const { fixture } = await setup({ error: true });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('not enrolled in any courses');
  });
});
