import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { CourseList } from './course-list.component';
import { CourseService } from '../course.service';
import { Course } from '../../api/models';

const fakeCourses: Course[] = [
  {
    id: 1,
    course_number: 'COMP101',
    name: 'Intro to CS',
    description: '',
    term: 'fall',
    year: 2026,
    membership: { type: 'student', state: 'enrolled' },
  },
  {
    id: 2,
    course_number: 'COMP210',
    name: 'Data Structures',
    description: '',
    term: 'spring',
    year: 2027,
    membership: { type: 'student', state: 'pending' },
  },
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
      imports: [CourseList, NoopAnimationsModule],
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
    const cards = el.querySelectorAll('mat-card');
    expect(cards.length).toBe(2);
    expect(cards[0].textContent).toContain('Intro to CS');
  });

  it('should display empty message when no courses', async () => {
    const { fixture } = await setup({ courses: [] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('not enrolled in any courses');
  });

  it('should show create course link', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const createLink =
      el.querySelector('a[routerLink="/courses/create"]') ??
      el.querySelector('a[ng-reflect-router-link="/courses/create"]');
    expect(createLink?.textContent).toContain('Create Course');
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
