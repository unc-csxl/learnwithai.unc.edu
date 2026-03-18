import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { CourseDetail } from './course-detail';
import { CourseService } from '../course.service';
import { Membership } from '../../api/models';

const fakeRoster: Membership[] = [
  { user_pid: 111, course_id: 1, type: 'instructor', state: 'enrolled' },
  { user_pid: 222, course_id: 1, type: 'student', state: 'enrolled' },
];

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('CourseDetail', () => {
  async function setup(options: { roster?: Membership[]; error?: { status: number } } = {}) {
    const mockService = {
      getRoster: options.error
        ? vi.fn(() => Promise.reject(options.error))
        : vi.fn(() => Promise.resolve(options.roster ?? fakeRoster)),
    };

    const mockRoute = {
      snapshot: { paramMap: new Map([['id', '1']]) },
    };

    TestBed.configureTestingModule({
      imports: [CourseDetail],
      providers: [
        provideRouter([]),
        { provide: CourseService, useValue: mockService },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(CourseDetail);
    fixture.detectChanges();
    await flush();
    fixture.detectChanges();
    return { fixture, mockService };
  }

  it('should display roster members', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const rows = el.querySelectorAll('tbody tr');
    expect(rows.length).toBe(2);
    expect(rows[0].textContent).toContain('111');
    expect(rows[0].textContent).toContain('instructor');
  });

  it('should show add member link', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const link = el.querySelector('a[href="/courses/1/add-member"]');
    expect(link).toBeTruthy();
  });

  it('should show 403 error message', async () => {
    const { fixture } = await setup({ error: { status: 403 } });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('do not have permission');
  });

  it('should show generic error message', async () => {
    const { fixture } = await setup({ error: { status: 500 } });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to load roster');
  });

  it('should show empty message when roster is empty', async () => {
    const { fixture } = await setup({ roster: [] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No members found');
  });
});
