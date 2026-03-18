import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { CourseDetail } from './course-detail.component';
import { CourseService } from '../course.service';
import { PageTitleService } from '../../page-title.service';
import { Course } from '../../api/models';

@Component({ template: '' })
class DummyComponent {}

const fakeCourse: Course = { id: 1, name: 'Intro CS', term: 'Fall 2026', section: '001' };
const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('CourseDetail', () => {
  async function setup(options: { courses?: Course[]; error?: boolean } = {}) {
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
    };

    TestBed.configureTestingModule({
      imports: [CourseDetail, NoopAnimationsModule],
      providers: [
        provideRouter([
          { path: 'roster', component: DummyComponent },
          { path: 'activities', component: DummyComponent },
          { path: 'tools', component: DummyComponent },
        ]),
        { provide: CourseService, useValue: mockService },
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(CourseDetail);
    fixture.detectChanges();
    await flush();
    fixture.detectChanges();
    return { fixture, mockService, mockPageTitle };
  }

  it('should set page title to course name and show term', async () => {
    const { fixture, mockPageTitle } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Intro CS');
    expect(el.textContent).toContain('Fall 2026');
  });

  it('should show nav tabs for roster, activities, and tools', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const links = el.querySelectorAll('[mat-tab-link]');
    expect(links.length).toBe(3);
    expect(links[0].textContent).toContain('Roster');
    expect(links[1].textContent).toContain('Activities');
    expect(links[2].textContent).toContain('Tools');
  });

  it('should show error message on load failure', async () => {
    const { fixture } = await setup({ error: true });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to load course details');
  });

  it('should show error when course not found', async () => {
    const { fixture } = await setup({ courses: [] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Course not found');
  });

  it('should have a router outlet for child views', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('router-outlet')).toBeTruthy();
  });
});
