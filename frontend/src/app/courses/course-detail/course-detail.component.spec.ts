import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute, Router } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { CourseDetail } from './course-detail.component';
import { CourseService } from '../course.service';
import { PageTitleService } from '../../page-title.service';
import { Course } from '../../api/models';
import { LayoutNavigationService } from '../../layout/layout-navigation.service';

@Component({ template: '' })
class DummyComponent {}

const fakeCourse: Course = {
  id: 1,
  name: 'Intro CS',
  term: 'Fall 2026',
  section: '001',
  membership: { type: 'instructor', state: 'enrolled' },
};

const fakeStudentCourse: Course = {
  id: 1,
  name: 'Intro CS',
  term: 'Fall 2026',
  section: '001',
  membership: { type: 'student', state: 'enrolled' },
};

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('CourseDetail', () => {
  async function setup(
    options: { courses?: Course[]; error?: boolean; activeChildPath?: string | null } = {},
  ) {
    const courses = options.courses ?? [fakeCourse];
    const mockService = {
      getMyCourses: options.error
        ? vi.fn(() => Promise.reject(new Error('fail')))
        : vi.fn(() => Promise.resolve(courses)),
    };

    const mockPageTitle = {
      title: vi.fn(),
      setTitle: vi.fn(),
    };

    const mockRoute = {
      snapshot: { paramMap: new Map([['id', '1']]) },
      firstChild:
        options.activeChildPath === null
          ? null
          : { routeConfig: { path: options.activeChildPath ?? 'dashboard' } },
    };

    const mockLayoutNavigation = {
      section: vi.fn(),
      setSection: vi.fn(),
      clear: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [CourseDetail, NoopAnimationsModule],
      providers: [
        provideRouter([
          { path: 'dashboard', component: DummyComponent },
          { path: 'roster', component: DummyComponent },
          { path: 'activities', component: DummyComponent },
          { path: 'tools', component: DummyComponent },
          { path: 'student', component: DummyComponent },
          { path: 'settings', component: DummyComponent },
        ]),
        { provide: CourseService, useValue: mockService },
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    const fixture = TestBed.createComponent(CourseDetail);
    fixture.detectChanges();
    await flush();
    fixture.detectChanges();
    return { fixture, mockService, mockPageTitle, mockLayoutNavigation, navigateSpy };
  }

  it('should set page title to course name and show term', async () => {
    const { fixture, mockPageTitle } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Intro CS');
    expect(el.textContent).toContain('Fall 2026');
  });

  it('should register instructor navigation with the shared app sidebar', async () => {
    const { mockLayoutNavigation } = await setup();
    expect(mockLayoutNavigation.setSection).toHaveBeenCalledWith({
      label: 'Instructor view',
      title: 'Intro CS',
      subtitle: 'Fall 2026 - Section 001',
      items: [
        {
          route: '/courses/1/dashboard',
          label: 'Dashboard',
          description: 'Course overview and quick links',
          icon: 'dashboard',
        },
        {
          route: '/courses/1/activities',
          label: 'Student Activities',
          description: 'Review student-facing work and participation',
          icon: 'assignment',
        },
        {
          route: '/courses/1/tools',
          label: 'Instructor Tools',
          description: 'Manage instructional workflows and tools',
          icon: 'build',
        },
        {
          route: '/courses/1/roster',
          label: 'Roster',
          description: 'See current course membership',
          icon: 'groups',
        },
        {
          route: '/courses/1/settings',
          label: 'Course Settings',
          description: 'Adjust course-level options and setup',
          icon: 'settings',
        },
      ],
    });
  });

  it('should register student navigation with only student links', async () => {
    const { mockLayoutNavigation, navigateSpy } = await setup({
      courses: [fakeStudentCourse],
      activeChildPath: 'activities',
    });

    expect(mockLayoutNavigation.setSection).toHaveBeenCalledWith({
      label: 'Student view',
      title: 'Intro CS',
      subtitle: 'Fall 2026 - Section 001',
      items: [
        {
          route: '/courses/1/activities',
          label: 'Student Activities',
          description: 'Review your course activities and assigned work',
          icon: 'assignment',
        },
        {
          route: '/courses/1/student',
          label: 'Student Tools',
          description: 'Open student-facing tools and workflows',
          icon: 'build',
        },
      ],
    });
    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it('should redirect students away from the dashboard route', async () => {
    const { navigateSpy } = await setup({ courses: [fakeStudentCourse] });
    expect(navigateSpy).toHaveBeenCalledWith(['/courses', 1, 'activities']);
  });

  it('should show course term metadata in the content area', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).not.toContain('Instructor view');
    expect(el.textContent).toContain('Section 001');
  });

  it('should show error message on load failure', async () => {
    const { fixture, mockLayoutNavigation } = await setup({ error: true });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to load course details');
    expect(mockLayoutNavigation.clear).toHaveBeenCalled();
  });

  it('should show error when course not found', async () => {
    const { fixture, mockLayoutNavigation } = await setup({ courses: [] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Course not found');
    expect(mockLayoutNavigation.clear).toHaveBeenCalled();
  });

  it('should have a router outlet for child views', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('router-outlet')).toBeTruthy();
  });

  it('should clear contextual navigation on destroy', async () => {
    const { fixture, mockLayoutNavigation } = await setup();
    fixture.destroy();
    expect(mockLayoutNavigation.clear).toHaveBeenCalled();
  });
});
