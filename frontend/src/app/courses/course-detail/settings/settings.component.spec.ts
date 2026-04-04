import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { signal } from '@angular/core';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Settings } from './settings.component';
import { CourseService } from '../../course.service';
import { PageTitleService } from '../../../page-title.service';
import { SuccessSnackbarService } from '../../../success-snackbar.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';
import { Course } from '../../../api/models';

const flush = () => new Promise((resolve) => setTimeout(resolve));

const fakeCourse: Course = {
  id: 1,
  course_number: 'COMP423',
  name: 'Foundations of Software Engineering',
  description: 'A great course',
  term: 'spring',
  year: 2026,
  membership: { type: 'instructor', state: 'enrolled' },
};

const fakeSection = {
  groups: [
    {
      label: 'Course',
      items: [
        {
          route: '/courses/1/dashboard',
          label: 'COMP423',
          subtitle: 'Spring 2026',
          description: 'Foundations of Software Engineering dashboard',
          icon: 'dashboard',
        },
      ],
    },
  ],
};

describe('Settings', () => {
  function setup(
    courses: Course[] = [fakeCourse],
    initialSection: typeof fakeSection | null = fakeSection,
  ) {
    const mockCourseService = {
      getMyCourses: vi.fn(() => Promise.resolve(courses)),
      updateCourse: vi.fn(() => Promise.resolve(fakeCourse)),
    };

    const mockPageTitle = {
      title: vi.fn(),
      setTitle: vi.fn(),
    };

    const mockRoute = {
      parent: { snapshot: { paramMap: { get: () => '1' } } },
    };

    const mockRouter = { navigate: vi.fn(() => Promise.resolve(true)) };

    const mockSuccessSnackbar = { open: vi.fn() };

    const sectionSignal = signal<typeof fakeSection | null>(initialSection);
    const mockLayoutNavigation = {
      section: sectionSignal.asReadonly(),
      updateSection: vi.fn((update: (section: typeof fakeSection) => typeof fakeSection) => {
        const current = sectionSignal();
        if (current !== null) {
          sectionSignal.set(update(current));
        }
      }),
    };

    TestBed.configureTestingModule({
      imports: [Settings, NoopAnimationsModule],
      providers: [
        { provide: CourseService, useValue: mockCourseService },
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: ActivatedRoute, useValue: mockRoute },
        { provide: Router, useValue: mockRouter },
        { provide: SuccessSnackbarService, useValue: mockSuccessSnackbar },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
      ],
    });

    const fixture = TestBed.createComponent(Settings);
    fixture.detectChanges();
    return {
      fixture,
      mockCourseService,
      mockPageTitle,
      mockRouter,
      mockSuccessSnackbar,
      mockLayoutNavigation,
    };
  }

  it('should set the page title', () => {
    const { mockPageTitle } = setup();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Course Settings');
  });

  it('should load and populate form with course data', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const component = fixture.componentInstance;
    expect(component['form'].value).toEqual({
      course_number: 'COMP423',
      name: 'Foundations of Software Engineering',
      description: 'A great course',
      term: 'spring',
      year: 2026,
    });
  });

  it('should show error when course is not found', async () => {
    const { fixture } = setup([]);
    await flush();
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Course not found');
  });

  it('should show error when fetch fails', async () => {
    const { mockCourseService } = setup();
    mockCourseService.getMyCourses.mockRejectedValueOnce(new Error('fail'));

    // Recreate to trigger the failed fetch
    const newFixture = TestBed.createComponent(Settings);
    newFixture.detectChanges();
    await flush();
    newFixture.detectChanges();

    const el: HTMLElement = newFixture.nativeElement;
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Failed to load course');
  });

  it('should submit update, show snackbar, update sidebar, and navigate to dashboard', async () => {
    const { fixture, mockCourseService, mockRouter, mockSuccessSnackbar, mockLayoutNavigation } =
      setup();
    await flush();
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    button.click();
    await flush();
    fixture.detectChanges();

    expect(mockCourseService.updateCourse).toHaveBeenCalledWith(1, {
      course_number: 'COMP423',
      name: 'Foundations of Software Engineering',
      description: 'A great course',
      term: 'spring',
      year: 2026,
    });
    expect(mockLayoutNavigation.updateSection).toHaveBeenCalled();
    expect(readSection(mockLayoutNavigation.section).groups[0].items[0]).toEqual(
      expect.objectContaining({
        label: 'COMP423',
        subtitle: 'Spring 2026',
      }),
    );
    expect(mockSuccessSnackbar.open).toHaveBeenCalledWith('Course settings updated.');
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/courses', 1, 'dashboard']);
  });

  it('should not submit when form is invalid', async () => {
    const { fixture, mockCourseService } = setup();
    await flush();
    fixture.detectChanges();

    fixture.componentInstance['form'].patchValue({ course_number: '' });
    fixture.componentInstance['onSubmit']();
    expect(mockCourseService.updateCourse).not.toHaveBeenCalled();
  });

  it('should show error on failed update', async () => {
    const { fixture, mockCourseService } = setup();
    await flush();
    fixture.detectChanges();

    mockCourseService.updateCourse.mockRejectedValueOnce(new Error('fail'));
    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    button.click();
    await flush();
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Failed to save');
  });

  it('should show saving state during submission', async () => {
    let resolveUpdate!: (value: Course) => void;
    const { fixture, mockCourseService, mockRouter, mockSuccessSnackbar } = setup();
    await flush();
    fixture.detectChanges();

    mockCourseService.updateCourse.mockReturnValue(
      new Promise<Course>((r) => {
        resolveUpdate = r;
      }),
    );

    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();

    expect(button.textContent).toContain('Saving');
    expect(button.disabled).toBe(true);

    resolveUpdate(fakeCourse);
    await flush();

    expect(mockSuccessSnackbar.open).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalled();
  });

  it('should save successfully even when no base sidebar section is active', async () => {
    const { fixture, mockLayoutNavigation } = setup();
    mockLayoutNavigation.section = signal<null>(null).asReadonly();
    mockLayoutNavigation.updateSection.mockImplementation(() => undefined);
    await flush();
    fixture.detectChanges();

    fixture.nativeElement.querySelector('button[type="submit"]').click();
    await flush();

    expect(mockLayoutNavigation.updateSection).toHaveBeenCalled();
  });

  it('should leave an empty sidebar section unchanged when there is no course item to update', async () => {
    const emptySection = { groups: [] };
    const { fixture, mockLayoutNavigation } = setup([fakeCourse], emptySection);
    await flush();
    fixture.detectChanges();

    fixture.nativeElement.querySelector('button[type="submit"]').click();
    await flush();

    expect(readSection(mockLayoutNavigation.section)).toEqual(emptySection);
  });

  it('should leave a section unchanged when the first group has no items', async () => {
    const emptyCourseGroup = { groups: [{ label: 'Course', items: [] }] };
    const { fixture, mockLayoutNavigation } = setup([fakeCourse], emptyCourseGroup);
    await flush();
    fixture.detectChanges();

    fixture.nativeElement.querySelector('button[type="submit"]').click();
    await flush();

    expect(readSection(mockLayoutNavigation.section)).toEqual(emptyCourseGroup);
  });

  it('should update the student dashboard description when the course home route points to the student view', async () => {
    const studentSection = {
      groups: [
        {
          label: 'Course',
          items: [
            {
              route: '/courses/1/student',
              label: 'COMP423',
              subtitle: 'Spring 2026',
              description: 'Foundations of Software Engineering student dashboard',
              icon: 'dashboard',
            },
          ],
        },
      ],
    };
    const { fixture, mockLayoutNavigation } = setup([fakeCourse], studentSection);
    await flush();
    fixture.detectChanges();

    fixture.nativeElement.querySelector('button[type="submit"]').click();
    await flush();

    expect(readSection(mockLayoutNavigation.section).groups[0].items[0].description).toBe(
      'Foundations of Software Engineering student dashboard',
    );
  });
});

function readSection<T>(signalReader: () => T | null): T {
  const section = signalReader();
  expect(section).not.toBeNull();
  return section as T;
}
