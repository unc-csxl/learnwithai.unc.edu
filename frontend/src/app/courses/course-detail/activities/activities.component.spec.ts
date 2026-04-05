import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { Activities } from './activities.component';
import { PageTitleService } from '../../../page-title.service';
import { CourseService } from '../../course.service';
import { ActivityService } from './activity.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('Activities', () => {
  function setup(overrides: { courseService?: object; activityService?: object } = {}) {
    const mockPageTitle = { title: vi.fn(), setTitle: vi.fn() };
    const mockLayoutNavigation = { clearContext: vi.fn() };
    const mockCourseService = overrides.courseService ?? {
      getMyCourses: vi.fn(() => Promise.resolve([{ id: 1, membership: { type: 'instructor' } }])),
    };
    const mockActivityService = overrides.activityService ?? {
      list: vi.fn(() =>
        Promise.resolve([
          {
            id: 10,
            title: 'Test Activity',
            type: 'iyow',
            due_date: '2025-12-01T00:00:00Z',
            release_date: '2025-11-01T00:00:00Z',
            late_date: null,
            course_id: 1,
            created_at: '2025-11-01T00:00:00Z',
          },
        ]),
      ),
    };
    const mockRoute = {
      parent: { parent: { snapshot: { paramMap: new Map([['id', '1']]) } } },
    };

    TestBed.configureTestingModule({
      imports: [Activities],
      providers: [
        provideRouter([]),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
        { provide: CourseService, useValue: mockCourseService },
        { provide: ActivityService, useValue: mockActivityService },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(Activities);
    fixture.detectChanges();

    return { fixture, mockPageTitle, mockLayoutNavigation };
  }

  it('should set the page title and list activities for instructor', async () => {
    const { fixture, mockPageTitle, mockLayoutNavigation } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockLayoutNavigation.clearContext).toHaveBeenCalled();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Student Activities');
    expect(fixture.nativeElement.textContent).toContain('Test Activity');
    expect(fixture.nativeElement.textContent).toContain('Create IYOW Activity');
  });

  it('should show empty state when no activities', async () => {
    const { fixture } = setup({
      activityService: { list: vi.fn(() => Promise.resolve([])) },
    });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No activities yet.');
  });

  it('should hide create button for students', async () => {
    const { fixture } = setup({
      courseService: {
        getMyCourses: vi.fn(() => Promise.resolve([{ id: 1, membership: { type: 'student' } }])),
      },
    });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).not.toContain('Create IYOW Activity');
  });

  it('should show error on load failure', async () => {
    const { fixture } = setup({
      courseService: { getMyCourses: vi.fn(() => Promise.reject(new Error('fail'))) },
      activityService: { list: vi.fn(() => Promise.reject(new Error('fail'))) },
    });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to load activities.');
  });

  it('should show late_date chip when present', async () => {
    const { fixture } = setup({
      activityService: {
        list: vi.fn(() =>
          Promise.resolve([
            {
              id: 10,
              title: 'Late Activity',
              type: 'iyow',
              due_date: '2025-12-01T00:00:00Z',
              release_date: '2025-11-01T00:00:00Z',
              late_date: '2025-12-15T00:00:00Z',
              course_id: 1,
              created_at: '2025-11-01T00:00:00Z',
            },
          ]),
        ),
      },
    });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Late Activity');
  });
});
