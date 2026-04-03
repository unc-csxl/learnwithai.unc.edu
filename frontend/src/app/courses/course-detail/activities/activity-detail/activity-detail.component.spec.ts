import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ActivityDetail } from './activity-detail.component';
import { PageTitleService } from '../../../../page-title.service';
import { JobUpdateService } from '../../../../job-update.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { ActivityService } from '../activity.service';
import { StudentSubmissionRow } from '../../../../api/models';
import { AsyncJobStatus } from '../../../../api/generated/models/async-job-status';

const flush = () => new Promise((resolve) => setTimeout(resolve));

const baseActivity = {
  id: 10,
  title: 'Test IYOW',
  prompt: 'Explain X',
  rubric: null as string | null,
  type: 'iyow',
  release_date: '2025-01-01T00:00:00Z',
  due_date: '2025-06-01T00:00:00Z',
  late_date: null as string | null,
  course_id: 1,
  created_at: '2025-01-01T00:00:00Z',
};

const rosterRows: StudentSubmissionRow[] = [
  {
    student_pid: 111,
    given_name: 'Alice',
    family_name: 'Anderson',
    email: 'alice@example.com',
    submission: {
      id: 100,
      activity_id: 10,
      student_pid: 111,
      is_active: true,
      submitted_at: '2025-03-01T00:00:00Z',
      response_text: 'My answer',
      feedback: 'Great!',
      job: { id: 42, status: 'completed' as AsyncJobStatus, completed_at: '2025-03-01T01:00:00Z' },
    },
  },
  {
    student_pid: 222,
    given_name: 'Bob',
    family_name: 'Baker',
    email: 'bob@example.com',
    submission: null,
  },
];

describe('ActivityDetail', () => {
  function setup(overrides: { activityService?: object } = {}) {
    const mockPageTitle = { title: vi.fn(), setTitle: vi.fn() };
    const mockJobUpdate = {
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      updateForJob: vi.fn(),
    };
    const mockActivityService = overrides.activityService ?? {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissionsRoster: vi.fn(() => Promise.resolve([...rosterRows])),
    };
    const mockRoute = {
      parent: { parent: { snapshot: { paramMap: new Map([['id', '1']]) } } },
      snapshot: { paramMap: new Map([['activityId', '10']]) },
    };

    const mockLayoutNavigation = { setSection: vi.fn(), clear: vi.fn() };

    TestBed.configureTestingModule({
      imports: [ActivityDetail],
      providers: [
        provideRouter([]),
        provideNoopAnimations(),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: JobUpdateService, useValue: mockJobUpdate },
        { provide: ActivityService, useValue: mockActivityService },
        { provide: ActivatedRoute, useValue: mockRoute },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
      ],
    });

    const fixture = TestBed.createComponent(ActivityDetail);
    fixture.detectChanges();

    return { fixture, mockPageTitle, mockJobUpdate, mockActivityService, mockLayoutNavigation };
  }

  it('should load activity and set title', async () => {
    const { fixture, mockPageTitle } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Test IYOW');
    expect(fixture.nativeElement.textContent).toContain('Explain X');
  });

  it('should subscribe to job updates on create and unsubscribe on destroy', () => {
    const { fixture, mockJobUpdate } = setup();
    expect(mockJobUpdate.subscribe).toHaveBeenCalledWith(1);

    fixture.destroy();
    expect(mockJobUpdate.unsubscribe).toHaveBeenCalledWith(1);
  });

  it('should show error on load failure', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.reject(new Error('fail'))),
      listSubmissionsRoster: vi.fn(() => Promise.reject(new Error('fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to load activity details.');
  });

  it('should render roster rows in the table', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Anderson, Alice');
    expect(text).toContain('Baker, Bob');
  });

  it('should show submission summary counts', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('1 of 2 students have submitted');
  });

  it('should show late_date and rubric when present', async () => {
    const mockActivityService = {
      get: vi.fn(() =>
        Promise.resolve({
          ...baseActivity,
          late_date: '2025-07-01T00:00:00Z',
          rubric: 'Must explain clearly',
        }),
      ),
      listSubmissionsRoster: vi.fn(() => Promise.resolve([])),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Late date');
    expect(fixture.nativeElement.textContent).toContain('Must explain clearly');
  });

  it('should show status labels for submitted and not-submitted rows', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Graded');
    expect(text).toContain('Not submitted');
  });

  it('should render a link for students with submissions', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const link: HTMLAnchorElement | null = fixture.nativeElement.querySelector('a[href]');
    expect(link).toBeTruthy();
    expect(link!.textContent).toContain('Anderson, Alice');
  });

  it('should show "No students found" when roster is empty', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissionsRoster: vi.fn(() => Promise.resolve([])),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No students found');
  });

  it('should filter rows by search query', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      searchQuery: { set: (v: string) => void };
    };
    comp.searchQuery.set('alice');
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Anderson, Alice');
    expect(text).not.toContain('Baker, Bob');
  });

  it('should set layout navigation with sidenav items', async () => {
    const { fixture, mockLayoutNavigation } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockLayoutNavigation.setSection).toHaveBeenCalledWith(
      expect.objectContaining({
        label: 'Test IYOW',
        items: expect.arrayContaining([
          expect.objectContaining({ label: 'Activity Editor' }),
          expect.objectContaining({ label: 'Preview & Test' }),
        ]),
      }),
    );
  });

  it('should return correct status labels', async () => {
    const { fixture } = setup();
    const comp = fixture.componentInstance as unknown as {
      statusLabel: (row: StudentSubmissionRow) => string;
    };

    expect(comp.statusLabel(rosterRows[0])).toBe('Graded');
    expect(comp.statusLabel(rosterRows[1])).toBe('Not submitted');

    const processingRow: StudentSubmissionRow = {
      ...rosterRows[0],
      submission: {
        ...rosterRows[0].submission!,
        job: { id: 1, status: 'pending' as AsyncJobStatus, completed_at: null },
      },
    };
    expect(comp.statusLabel(processingRow)).toBe('Processing');

    const submittedRow: StudentSubmissionRow = {
      ...rosterRows[0],
      submission: { ...rosterRows[0].submission!, feedback: null, job: null },
    };
    expect(comp.statusLabel(submittedRow)).toBe('Submitted');
  });
});
