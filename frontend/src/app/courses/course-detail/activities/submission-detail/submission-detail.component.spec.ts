import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute, Router, convertToParamMap } from '@angular/router';
import { signal, WritableSignal } from '@angular/core';
import { FormControl } from '@angular/forms';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { BehaviorSubject } from 'rxjs';
import { SubmissionDetail } from './submission-detail.component';
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
    job: { id: 42, status: 'completed' as AsyncJobStatus, completed_at: '2025-03-02T01:00:00Z' },
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

const otherStudentHistory = [
  {
    id: 202,
    activity_id: 10,
    student_pid: 222,
    is_active: true,
    submitted_at: '2025-03-03T00:00:00Z',
    response_text: 'Peer answer',
    feedback: 'Solid work',
    job: { id: 52, status: 'completed' as AsyncJobStatus, completed_at: '2025-03-03T01:00:00Z' },
  },
];

const rosterRows: StudentSubmissionRow[] = [
  {
    student_pid: 111,
    given_name: 'Sally',
    family_name: 'Student',
    email: 'student@example.com',
    submission: historySubmissions[0],
  },
  {
    student_pid: 222,
    given_name: 'Parker',
    family_name: 'Peer',
    email: 'peer@example.com',
    submission: otherStudentHistory[0],
  },
  {
    student_pid: 333,
    given_name: 'Tatum',
    family_name: 'TA',
    email: 'ta@example.com',
    submission: null,
  },
];

describe('SubmissionDetail', () => {
  function setup(
    overrides: {
      activityService?: object;
      jobSignals?: Map<number, WritableSignal<{ status: string } | null>>;
      initialStudentPid?: string;
      detectChanges?: boolean;
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
      listSubmissionsRoster: vi.fn(() => Promise.resolve([...rosterRows])),
      getStudentHistory: vi.fn((_: number, __: number, studentPid: number) =>
        Promise.resolve(studentPid === 222 ? [...otherStudentHistory] : [...historySubmissions]),
      ),
    };
    const paramMap$ = new BehaviorSubject(
      convertToParamMap({
        activityId: '10',
        studentPid: overrides.initialStudentPid ?? '111',
      }),
    );
    const mockRoute = {
      parent: { parent: { snapshot: { paramMap: convertToParamMap({ id: '1' }) } } },
      snapshot: {
        paramMap: paramMap$.value,
      },
      paramMap: paramMap$.asObservable(),
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
    if (overrides.detectChanges !== false) {
      fixture.detectChanges();
    }

    return {
      fixture,
      mockPageTitle,
      mockJobUpdate,
      mockActivityService,
      mockLayoutNavigation,
      paramMap$,
    };
  }

  it('should load activity and submissions, then set title', async () => {
    const { fixture, mockPageTitle } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Test IYOW — Submission 101');
    expect(fixture.nativeElement.textContent).toContain('Release date');
    expect(fixture.nativeElement.textContent).toContain('Due date');
    expect(fixture.nativeElement.textContent).toContain('Submission 101');
    expect(fixture.nativeElement.textContent).toContain('Submitted by Sally Student');
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
      listSubmissionsRoster: vi.fn(() => Promise.reject(new Error('fail'))),
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
      listSubmissionsRoster: vi.fn(() =>
        Promise.resolve([
          {
            ...rosterRows[0],
            submission: null,
          },
        ]),
      ),
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
      listSubmissionsRoster: vi.fn(() =>
        Promise.resolve([{ ...rosterRows[0], submission: pendingSub }]),
      ),
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
            items: expect.arrayContaining([
              expect.objectContaining({
                label: 'Submission 101',
                description: 'Submitted by Sally Student',
              }),
            ]),
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
      listSubmissionsRoster: vi.fn(() => Promise.resolve([...rosterRows])),
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

  it('should show a submission navigator with jump options and disabled edge controls', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Submission navigator');
    expect(text).toContain('Submitted student 2 of 2');

    const comp = fixture.componentInstance as unknown as {
      jumpOptionLabel: (row: StudentSubmissionRow) => string;
      previousSubmissionRow: { (): StudentSubmissionRow | null };
      nextSubmissionRow: { (): StudentSubmissionRow | null };
    };

    expect(comp.jumpOptionLabel(rosterRows[1])).toBe('Parker Peer - Submission 202');
    expect(comp.previousSubmissionRow()).toEqual(rosterRows[1]);
    expect(comp.nextSubmissionRow()).toBeNull();

    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ) as HTMLButtonElement[];
    const previousButton = buttons.find((button) => button.textContent?.includes('Previous'));
    const nextButton = buttons.find((button) => button.textContent?.includes('Next'));

    expect(previousButton?.disabled).toBe(false);
    expect(nextButton?.disabled).toBe(true);
  });

  it('should navigate to the previous and next submitted students', async () => {
    const { fixture } = setup({ initialStudentPid: '222' });
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      goToPreviousSubmission: () => Promise<void>;
      goToNextSubmission: () => Promise<void>;
    };

    await comp.goToPreviousSubmission();
    expect(router.navigate).not.toHaveBeenCalled();

    await comp.goToNextSubmission();
    expect(router.navigate).toHaveBeenCalledWith([
      '/courses',
      1,
      'activities',
      10,
      'submissions',
      111,
    ]);
  });

  it('should navigate when a jump option is selected', async () => {
    const { fixture } = setup();
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      onJumpSelection: (event: { option: { value: StudentSubmissionRow } }) => Promise<void>;
      jumpControl: FormControl<string | StudentSubmissionRow>;
    };

    comp.jumpControl.setValue('peer');
    await comp.onJumpSelection({ option: { value: rosterRows[1] } });

    expect(comp.jumpControl.value).toBe('');
    expect(router.navigate).toHaveBeenCalledWith([
      '/courses',
      1,
      'activities',
      10,
      'submissions',
      222,
    ]);
  });

  it('should filter jump options from a typed query', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      jumpControl: FormControl<string | StudentSubmissionRow>;
      jumpOptions: { (): StudentSubmissionRow[] };
    };

    comp.jumpControl.setValue('202');
    fixture.detectChanges();

    expect(comp.jumpOptions()).toEqual([rosterRows[1]]);
  });

  it('should ignore invalid student route params', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissionsRoster: vi.fn(() => Promise.resolve([...rosterRows])),
      getStudentHistory: vi.fn(() => Promise.resolve([...historySubmissions])),
    };

    setup({ activityService: mockActivityService, initialStudentPid: 'not-a-number' });
    await flush();

    expect(mockActivityService.get).not.toHaveBeenCalled();
    expect(mockActivityService.listSubmissionsRoster).not.toHaveBeenCalled();
    expect(mockActivityService.getStudentHistory).not.toHaveBeenCalled();
  });

  it('should reload submission data when the student route param changes', async () => {
    const { fixture, paramMap$, mockPageTitle, mockActivityService } = setup();
    await flush();
    fixture.detectChanges();

    paramMap$.next(convertToParamMap({ activityId: '10', studentPid: '222' }));
    await flush();
    fixture.detectChanges();

    expect(
      (mockActivityService as { getStudentHistory: ReturnType<typeof vi.fn> }).getStudentHistory,
    ).toHaveBeenLastCalledWith(1, 10, 222);
    expect(mockPageTitle.setTitle).toHaveBeenLastCalledWith('Test IYOW — Submission 202');
    expect(fixture.nativeElement.textContent).toContain('Submission 202');
    expect(fixture.nativeElement.textContent).toContain('Submitted by Parker Peer');
  });

  it('should clear stale state before loading another student route', async () => {
    let resolveSecondHistory!: (value: typeof otherStudentHistory) => void;
    const getStudentHistory = vi
      .fn()
      .mockResolvedValueOnce([...historySubmissions])
      .mockImplementationOnce(
        () =>
          new Promise<typeof otherStudentHistory>((resolve) => {
            resolveSecondHistory = resolve;
          }),
      );

    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissionsRoster: vi.fn(() => Promise.resolve([...rosterRows])),
      getStudentHistory,
    };
    const { fixture, paramMap$ } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      selectPriorSubmission: (sub: (typeof historySubmissions)[0]) => void;
      activity: { (): typeof baseActivity | null };
      rosterRows: { (): StudentSubmissionRow[] };
      submissions: { (): typeof historySubmissions };
      loaded: { (): boolean };
      selectedPriorSub: { (): (typeof historySubmissions)[0] | null };
    };

    comp.selectPriorSubmission(historySubmissions[1]);
    paramMap$.next(convertToParamMap({ activityId: '10', studentPid: '222' }));
    await flush();
    fixture.detectChanges();

    expect(comp.loaded()).toBe(false);
    expect(comp.activity()).toBeNull();
    expect(comp.rosterRows()).toEqual([]);
    expect(comp.submissions()).toEqual([]);
    expect(comp.selectedPriorSub()).toBeNull();

    resolveSecondHistory([...otherStudentHistory]);
    await flush();
    fixture.detectChanges();

    expect(comp.loaded()).toBe(true);
    expect(getStudentHistory).toHaveBeenLastCalledWith(1, 10, 222);
  });

  it('should fall back to student metadata when no current submission or name is available', async () => {
    const namelessRow: StudentSubmissionRow = {
      student_pid: 111,
      given_name: null as unknown as string,
      family_name: null as unknown as string,
      email: null as unknown as string,
      submission: null,
    };
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissionsRoster: vi.fn(() => Promise.resolve([namelessRow])),
      getStudentHistory: vi.fn(() => Promise.resolve([])),
    };
    const { fixture, mockPageTitle, mockLayoutNavigation } = setup({
      activityService: mockActivityService,
    });
    await flush();
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Test IYOW — Student 111');
    expect(fixture.nativeElement.textContent).toContain('Student 111');
    expect(fixture.nativeElement.textContent).toContain('Student PID 111');
    expect(fixture.nativeElement.textContent).not.toContain('Submitted student');
    expect(mockLayoutNavigation.setContextSection).toHaveBeenCalledWith(
      expect.objectContaining({
        groups: expect.arrayContaining([
          expect.objectContaining({
            label: 'Submission',
            items: expect.arrayContaining([
              expect.objectContaining({
                label: 'Student 111',
                description: 'Review this student submission history',
              }),
            ]),
          }),
        ]),
      }),
    );
  });

  it('should fall back to history when the current student is missing from the roster', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissionsRoster: vi.fn(() => Promise.resolve([rosterRows[1]])),
      getStudentHistory: vi.fn(() => Promise.resolve([...historySubmissions])),
    };
    const { fixture, mockPageTitle, mockLayoutNavigation } = setup({
      activityService: mockActivityService,
      initialStudentPid: '999',
    });
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      currentStudentRow: { (): StudentSubmissionRow | null };
      currentSubmissionLabel: { (): string };
      currentStudentDescription: { (): string };
      currentSubmittedPosition: { (): string };
      previousSubmissionRow: { (): StudentSubmissionRow | null };
      nextSubmissionRow: { (): StudentSubmissionRow | null };
    };

    expect(comp.currentStudentRow()).toBeNull();
    expect(comp.currentSubmissionLabel()).toBe('Submission 101');
    expect(comp.currentStudentDescription()).toBe('Student PID 999');
    expect(comp.currentSubmittedPosition()).toBe('');
    expect(comp.previousSubmissionRow()).toBeNull();
    expect(comp.nextSubmissionRow()).toBeNull();
    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Test IYOW — Submission 101');
    expect(mockLayoutNavigation.setContextSection).toHaveBeenCalledWith(
      expect.objectContaining({
        groups: expect.arrayContaining([
          expect.objectContaining({
            label: 'Submission',
            items: expect.arrayContaining([
              expect.objectContaining({
                label: 'Submission 101',
                description: 'Review this student submission history',
              }),
            ]),
          }),
        ]),
      }),
    );
  });

  it('should cover jump helper fallbacks and search matching', async () => {
    const { fixture } = setup();
    const mockJobUpdate = TestBed.inject(JobUpdateService) as unknown as {
      updateForJob: ReturnType<typeof vi.fn>;
    };
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      jumpDisplay: (value: string | StudentSubmissionRow | null) => string;
      jumpOptionLabel: (row: StudentSubmissionRow) => string;
      formatStudentName: (row: StudentSubmissionRow | null) => string;
      studentSortValue: (row: StudentSubmissionRow) => string;
      matchesJumpQuery: (row: StudentSubmissionRow, query: string) => boolean;
      watchJob: (jobId: number) => void;
    };
    const emailOnlyRow: StudentSubmissionRow = {
      student_pid: 444,
      given_name: null as unknown as string,
      family_name: null as unknown as string,
      email: 'mystery@example.com',
      submission: null,
    };
    const unnamedRow: StudentSubmissionRow = {
      student_pid: 555,
      given_name: null as unknown as string,
      family_name: null as unknown as string,
      email: null as unknown as string,
      submission: null,
    };

    expect(comp.jumpDisplay(null)).toBe('');
    expect(comp.jumpDisplay('peer')).toBe('peer');
    expect(comp.jumpDisplay(rosterRows[1])).toBe('Parker Peer - Submission 202');
    expect(comp.formatStudentName(null)).toBe('');
    expect(comp.formatStudentName(emailOnlyRow)).toBe('mystery@example.com');
    expect(comp.jumpOptionLabel(unnamedRow)).toBe('Student 555 - Unknown submission');
    expect(comp.studentSortValue(emailOnlyRow)).toBe('mystery@example.com');
    expect(comp.matchesJumpQuery(rosterRows[1], 'peer@example.com')).toBe(true);
    expect(comp.matchesJumpQuery(rosterRows[1], '202')).toBe(true);
    expect(comp.matchesJumpQuery(unnamedRow, '555')).toBe(true);
    expect(comp.matchesJumpQuery(unnamedRow, 'missing')).toBe(false);

    comp.watchJob(77);
    comp.watchJob(77);

    expect(mockJobUpdate.updateForJob).toHaveBeenCalledTimes(1);
  });

  it('should fall back to null when computed previous or next rows point to sparse entries', async () => {
    const { fixture } = setup({ detectChanges: false });

    const comp = fixture.componentInstance as unknown as {
      previousSubmissionRow: { (): StudentSubmissionRow | null };
      nextSubmissionRow: { (): StudentSubmissionRow | null };
      currentSubmittedIndex: { (): number };
      submittedRows: { (): StudentSubmissionRow[] };
    };

    Object.assign(comp, {
      currentSubmittedIndex: () => 1,
      submittedRows: () => [undefined, rosterRows[1]] as unknown as StudentSubmissionRow[],
    });
    expect(comp.previousSubmissionRow()).toBeNull();

    Object.assign(comp, {
      currentSubmittedIndex: () => 0,
      submittedRows: () => [rosterRows[0], undefined] as unknown as StudentSubmissionRow[],
    });
    expect(comp.nextSubmissionRow()).toBeNull();
  });

  it('should invoke the previous button click binding', async () => {
    const { fixture } = setup();
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    await flush();
    fixture.detectChanges();

    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ) as HTMLButtonElement[];
    const previousButton = buttons.find((button) => button.textContent?.includes('Previous'));

    previousButton?.click();
    await flush();

    expect(router.navigate).toHaveBeenCalledWith([
      '/courses',
      1,
      'activities',
      10,
      'submissions',
      222,
    ]);
  });

  it('should invoke the next button click binding', async () => {
    const { fixture } = setup({ initialStudentPid: '222' });
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    await flush();
    fixture.detectChanges();

    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ) as HTMLButtonElement[];
    const nextButton = buttons.find((button) => button.textContent?.includes('Next'));

    nextButton?.click();
    await flush();

    expect(router.navigate).toHaveBeenCalledWith([
      '/courses',
      1,
      'activities',
      10,
      'submissions',
      111,
    ]);
  });

  it('should invoke the autocomplete optionSelected binding from the template', async () => {
    const { fixture } = setup();
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    await flush();
    fixture.detectChanges();

    const input: HTMLInputElement = fixture.nativeElement.querySelector(
      'input[aria-label="Jump to a submitted student"]',
    );
    input.focus();
    input.value = 'Parker';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    await flush();

    const option = Array.from(document.body.querySelectorAll('mat-option')).find((element) =>
      element.textContent?.includes('Parker Peer - Submission 202'),
    ) as HTMLElement | undefined;

    option?.click();
    await flush();

    expect(router.navigate).toHaveBeenCalledWith([
      '/courses',
      1,
      'activities',
      10,
      'submissions',
      222,
    ]);
  });

  it('should show the no-other-submissions autocomplete state and disable both navigator buttons', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissionsRoster: vi.fn(() => Promise.resolve([rosterRows[0]])),
      getStudentHistory: vi.fn(() => Promise.resolve([...historySubmissions])),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const input: HTMLInputElement = fixture.nativeElement.querySelector(
      'input[aria-label="Jump to a submitted student"]',
    );
    input.focus();
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    await flush();

    expect(document.body.textContent).toContain('No other submitted students yet');

    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ) as HTMLButtonElement[];
    const previousButton = buttons.find((button) => button.textContent?.includes('Previous'));
    const nextButton = buttons.find((button) => button.textContent?.includes('Next'));

    expect(previousButton?.disabled).toBe(true);
    expect(nextButton?.disabled).toBe(true);
  });
});
