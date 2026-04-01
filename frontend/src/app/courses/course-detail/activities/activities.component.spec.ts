import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { Activities } from './activities.component';
import { PageTitleService } from '../../../page-title.service';
import { CourseService } from '../../course.service';
import { ActivityService } from './activity.service';

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('Activities', () => {
  it('should set the page title and list activities', async () => {
    const mockPageTitle = {
      title: vi.fn(),
      setTitle: vi.fn(),
    };

    const mockCourseService = {
      getMyCourses: vi.fn(() => Promise.resolve([{ id: 1, membership: { type: 'instructor' } }])),
    };

    const mockActivityService = {
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
      parent: { snapshot: { paramMap: new Map([['id', '1']]) } },
    };

    TestBed.configureTestingModule({
      imports: [Activities],
      providers: [
        provideRouter([]),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: CourseService, useValue: mockCourseService },
        { provide: ActivityService, useValue: mockActivityService },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(Activities);
    fixture.detectChanges();
    await flush();
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Student Activities');
    expect(fixture.nativeElement.textContent).toContain('Test Activity');
  });
});
