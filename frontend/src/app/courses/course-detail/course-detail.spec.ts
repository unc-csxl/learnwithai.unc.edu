import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { of, throwError } from 'rxjs';
import { CourseDetail } from './course-detail';
import { CourseService } from '../course.service';
import { MembershipResponse } from '../../api/generated/models/membership-response';

const fakeRoster: MembershipResponse[] = [
  { user_pid: 111, course_id: 1, type: 'instructor', state: 'enrolled' },
  { user_pid: 222, course_id: 1, type: 'student', state: 'enrolled' },
];

describe('CourseDetail', () => {
  function setup(options: { roster?: MembershipResponse[]; error?: { status: number } } = {}) {
    const mockService = {
      getRoster: options.error
        ? vi.fn(() => throwError(() => options.error))
        : vi.fn(() => of(options.roster ?? fakeRoster)),
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
    return { fixture, mockService };
  }

  it('should display roster members', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const rows = el.querySelectorAll('tbody tr');
    expect(rows.length).toBe(2);
    expect(rows[0].textContent).toContain('111');
    expect(rows[0].textContent).toContain('instructor');
  });

  it('should show add member link', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const link = el.querySelector('a[href="/courses/1/add-member"]');
    expect(link).toBeTruthy();
  });

  it('should show 403 error message', () => {
    const { fixture } = setup({ error: { status: 403 } });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('do not have permission');
  });

  it('should show generic error message', () => {
    const { fixture } = setup({ error: { status: 500 } });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to load roster');
  });

  it('should show empty message when roster is empty', () => {
    const { fixture } = setup({ roster: [] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No members found');
  });
});
