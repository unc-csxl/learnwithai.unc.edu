import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { signal, WritableSignal } from '@angular/core';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { SubmissionDetail } from './submission-detail.component';
import { PageTitleService } from '../../../../page-title.service';
import { JobUpdateService } from '../../../../job-update.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { ActivityService } from '../activity.service';

const flush = () => new Promise((resolve) => setTimeout(resolve));

const baseActivity = {
  id: 10,
  title: 'Test IYOW',
  prompt: 'Explain X',
  rubric: 'Must be clear',
  type: 'iyow',
  release_date: '2025-01-01T00:00:00Z',
  due_date: '2025-06-01T00:00:00Z',
  late_date: null as string | null,
  course_id: 1,
  created_at: '2025-01-01T00:00:00Z',
};

const historySubmissions = [
  {
    id: 101,
    activity_id: 10,
    student_pid: 111,
    is_active: true,
    submitted_at: '2025-03-02T00:00:00Z',
    response_text: 'Current answer',
    feedback: 'Good!',
    job: { id: 42, status: 'completed', completed_at: '2025-03-02T01:00:00Z' },
  },
  {
    id: 100,
    activity_id: 10,
    student_pid: 111,
    is_active: false,
    submitted_at: '2025-03-01T00:00:00Z',
    response_text: 'Old answer',
    feedback: 'Needs work',
    job: null,
  },
];

describe('SubmissionDetail', () => {
  function setup(
    overrides: {
      activityService?: object;
      jobSignals?: Map<number, WritableSignal<{ status: string } | null>>;
    } = {},
  ) {
    const mockPageTitle = { title: vi.fn(), setTitle: vi.fn() };
    const jobSignals = overrides.jobSignals ?? new Map();
    const mockJobUpdate = {
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      updateForJob: vi.fn((id: number) => {
        if (!jobSignals.has(id)) jobSignals.set(id, signal(null));
        return jobSignals.get(id)!;
      }),
    };
    const mockActivityService = overrides.activityService ?? {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getStudentHistory: vi.fn(() => Promise.resolve([...historySubmissions])),
    };
    const mockRoute = {
      parent: { parent: { snapshot: { paramMap: new Map([['id', '1']]) } } },
      snapshot: {
        paramMap: new Map([
          ['activityId', '10'],
          ['studentPid', '111'],
        ]),
      },
    };

    const mockLayoutNavigation = { setContextSection: vi.fn(), clearContext: vi.fn() };

    TestBed.configureTestingModule({
      imports: [SubmissionDetail],
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

    const fixture = TestBed.createComponent(SubmissionDetail);
    fixture.detectChanges();

    return { fixture, mockPageTitle, mockJobUpdate, mockActivityService, mockLayoutNavigation };
  }

  it('should load activity and submissions, then set title', async () => {
    const { fixture, mockPageTitle } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Test IYOW — Student 111');
    expect(fixture.nativeElement.textContent).toContain('Release date');
    expect(fixture.nativeElement.textContent).toContain('Due date');
  });

  it('should subscribe to job updates on create and unsubscribe on destroy', () => {
    const { fixture, mockJobUpdate, mockLayoutNavigation } = setup();
    expect(mockJobUpdate.subscribe).toHaveBeenCalledWith(1);

    fixture.destroy();
    expect(mockJobUpdate.unsubscribe).toHaveBeenCalledWith(1);
    expect(mockLayoutNavigation.clearContext).not.toHaveBeenCalled();
  });

  it('should show error on load failure', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.reject(new Error('fail'))),
      getStudentHistory: vi.fn(() => Promise.reject(new Error('fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to load submission details.');
  });

  it('should display submissions with response text and feedback', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Current answer');
    expect(text).toContain('Good!');
    expect(text).toContain('Old answer');
    expect(text).toContain('Needs work');
  });

  it('should show "(Active)" marker on the active submission', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('(Active)');
  });

  it('should show empty state when no submissions', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getStudentHistory: vi.fn(() => Promise.resolve([])),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No submissions yet from this student');
  });

  it('should show rubric when present', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).not.toContain('Prompt');
    expect(fixture.nativeElement.textContent).not.toContain('Explain X');
    expect(fixture.nativeElement.textContent).not.toContain('Rubric');
    expect(fixture.nativeElement.textContent).not.toContain('Must be clear');
  });

  it('should show spinner for pending submission and refresh on job complete', async () => {
    const jobSignals = new Map<number, WritableSignal<{ status: string } | null>>();
    const pendingSub = {
      id: 200,
      activity_id: 10,
      student_pid: 111,
      is_active: true,
      submitted_at: '2025-03-01T00:00:00Z',
      response_text: 'Waiting answer',
      feedback: null,
      job: { id: 77, status: 'pending' },
    };
    const completedSub = {
      ...pendingSub,
      feedback: 'Done!',
      job: { id: 77, status: 'completed' },
    };

    const getStudentHistory = vi
      .fn()
      .mockResolvedValueOnce([pendingSub])
      .mockResolvedValueOnce([completedSub]);

    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getStudentHistory,
    };
    const { fixture } = setup({ activityService: mockActivityService, jobSignals });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Generating feedback');

    // Simulate job completing
    jobSignals.get(77)!.set({ status: 'completed' });
    TestBed.flushEffects();
    await flush();
    fixture.detectChanges();

    expect(getStudentHistory).toHaveBeenCalledTimes(2);
  });

  it('should return correct status icons', () => {
    const { fixture } = setup();
    const comp = fixture.componentInstance as unknown as {
      statusIcon: (status: string | undefined) => string;
    };

    expect(comp.statusIcon('pending')).toBe('schedule');
    expect(comp.statusIcon('processing')).toBe('sync');
    expect(comp.statusIcon('completed')).toBe('check_circle');
    expect(comp.statusIcon('failed')).toBe('error');
    expect(comp.statusIcon(undefined)).toBe('help');
    expect(comp.statusIcon('unknown')).toBe('help');
  });

  it('should set layout navigation with activity and submission context', async () => {
    const { fixture, mockLayoutNavigation } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockLayoutNavigation.setContextSection).toHaveBeenCalledWith(
      expect.objectContaining({
        visibleBaseRoutes: ['/courses/1/dashboard', '/courses/1/activities'],
        groups: expect.arrayContaining([
          expect.objectContaining({
            label: 'Current activity',
            items: expect.arrayContaining([
              expect.objectContaining({ label: 'Submissions', icon: 'assignment' }),
              expect.objectContaining({ label: 'Activity Editor' }),
              expect.objectContaining({ label: 'Preview & Test' }),
            ]),
          }),
          expect.objectContaining({
            label: 'Submission',
            items: expect.arrayContaining([expect.objectContaining({ label: 'Student 111' })]),
          }),
        ]),
      }),
    );
  });

  it('should select and clear a prior submission', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      selectPriorSubmission: (sub: (typeof historySubmissions)[0]) => void;
      clearSelectedPrior: () => void;
      selectedPriorSub: { (): (typeof historySubmissions)[0] | null };
    };

    expect(comp.selectedPriorSub()).toBeNull();

    comp.selectPriorSubmission(historySubmissions[1]);
    expect(comp.selectedPriorSub()).toEqual(historySubmissions[1]);

    comp.clearSelectedPrior();
    expect(comp.selectedPriorSub()).toBeNull();
  });

  it('should keep the activity information card limited to release and due dates', async () => {
    const noRubricActivity = { ...baseActivity, rubric: null };
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve(noRubricActivity)),
      getStudentHistory: vi.fn(() => Promise.resolve([...historySubmissions])),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Release date');
    expect(fixture.nativeElement.textContent).toContain('Due date');
    expect(fixture.nativeElement.textContent).not.toContain('Prompt');
    expect(fixture.nativeElement.textContent).not.toContain('Rubric');
  });
});
