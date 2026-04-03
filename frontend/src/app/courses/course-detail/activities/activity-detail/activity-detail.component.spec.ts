import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { signal, WritableSignal } from '@angular/core';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ActivityDetail } from './activity-detail.component';
import { PageTitleService } from '../../../../page-title.service';
import { JobUpdateService } from '../../../../job-update.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { ActivityService } from '../activity.service';

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

describe('ActivityDetail', () => {
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
      listSubmissions: vi.fn(() => Promise.resolve([])),
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

    return { fixture, mockPageTitle, mockJobUpdate, mockActivityService, jobSignals };
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
      listSubmissions: vi.fn(() => Promise.reject(new Error('fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to load activity details.');
  });

  it('should show submissions with feedback', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissions: vi.fn(() =>
        Promise.resolve([
          {
            id: 100,
            activity_id: 10,
            student_pid: 123,
            is_active: true,
            submitted_at: '2025-03-01T00:00:00Z',
            response_text: 'Student answer',
            feedback: 'Great work!',
            job: { id: 42, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
          },
          {
            id: 101,
            activity_id: 10,
            student_pid: 456,
            is_active: true,
            submitted_at: '2025-03-02T00:00:00Z',
            response_text: 'No job answer',
            feedback: null,
            job: null,
          },
        ]),
      ),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Student answer');
    expect(fixture.nativeElement.textContent).toContain('Great work!');
    expect(fixture.nativeElement.textContent).toContain('No job answer');
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
      listSubmissions: vi.fn(() => Promise.resolve([])),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Late date');
    expect(fixture.nativeElement.textContent).toContain('Must explain clearly');
  });

  it('should show spinner for pending submission and refresh on job complete', async () => {
    const jobSignals = new Map<number, WritableSignal<{ status: string } | null>>();
    const pendingSub = {
      id: 200,
      activity_id: 10,
      student_pid: 456,
      is_active: true,
      submitted_at: '2025-03-01T00:00:00Z',
      response_text: 'Waiting answer',
      feedback: null,
      job: { id: 77, status: 'pending' },
    };
    const completedSub = { ...pendingSub, feedback: 'Done!', job: { id: 77, status: 'completed' } };

    const listSubmissions = vi
      .fn()
      .mockResolvedValueOnce([pendingSub])
      .mockResolvedValueOnce([completedSub]);

    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissions,
    };
    const { fixture } = setup({ activityService: mockActivityService, jobSignals });
    await flush();
    fixture.detectChanges();

    // Should show spinner for pending
    expect(fixture.nativeElement.textContent).toContain('Generating feedback');

    // Simulate job completing
    jobSignals.get(77)!.set({ status: 'completed' });
    TestBed.flushEffects();
    await flush();
    fixture.detectChanges();

    expect(listSubmissions).toHaveBeenCalledTimes(2);
  });

  it('should return correct status icon', () => {
    const { fixture } = setup();
    const component = fixture.componentInstance as unknown as {
      statusIcon: (status: string | undefined) => string;
    };

    expect(component.statusIcon('pending')).toBe('schedule');
    expect(component.statusIcon('processing')).toBe('sync');
    expect(component.statusIcon('completed')).toBe('check_circle');
    expect(component.statusIcon('failed')).toBe('error');
    expect(component.statusIcon(undefined)).toBe('help');
    expect(component.statusIcon('unknown')).toBe('help');
  });

  it('should load and display student submission history via menu interaction', async () => {
    const submissions = [
      {
        id: 100,
        activity_id: 10,
        student_pid: 123,
        is_active: true,
        submitted_at: '2025-03-01T00:00:00Z',
        response_text: 'Current answer',
        feedback: 'Good!',
        job: { id: 42, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
      },
    ];
    const history = [
      {
        id: 99,
        activity_id: 10,
        student_pid: 123,
        is_active: false,
        submitted_at: '2025-02-15T00:00:00Z',
        response_text: 'Old answer',
        feedback: 'Needs work',
        job: null,
      },
      ...submissions,
    ];
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissions: vi.fn(() => Promise.resolve(submissions)),
      getStudentHistory: vi.fn(() => Promise.resolve(history)),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    // Click the "Prior Submissions" button to open the menu (triggers menuOpened -> loadHistory)
    const priorBtn: HTMLButtonElement = fixture.nativeElement.querySelector('button[mat-button]');
    priorBtn.click();
    await flush();
    fixture.detectChanges();

    expect(mockActivityService.getStudentHistory).toHaveBeenCalledWith(1, 10, 123);

    // Menu items should be in the overlay
    const overlay = document.querySelector('.cdk-overlay-container');
    const menuItems = overlay?.querySelectorAll('button[mat-menu-item]') ?? [];
    expect(menuItems.length).toBe(2);

    // Click on the first menu item (Submission 2 — most recent) to select it
    (menuItems[0] as HTMLButtonElement).click();
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      selectedHistorySub: () => unknown;
    };
    expect(comp.selectedHistorySub()).toBe(history[0]);
    expect(fixture.nativeElement.textContent).toContain('Prior Submission');
    expect(fixture.nativeElement.textContent).toContain('Old answer');

    // Click Close button on the prior submission card
    const allButtons: NodeListOf<HTMLButtonElement> =
      fixture.nativeElement.querySelectorAll('button[mat-button]');
    const closeBtn = Array.from(allButtons).find((b) => b.textContent?.includes('Close'));
    closeBtn?.click();
    fixture.detectChanges();
    expect(comp.selectedHistorySub()).toBeNull();
  });

  it('should silently handle loadHistory errors', async () => {
    const submissions = [
      {
        id: 100,
        activity_id: 10,
        student_pid: 123,
        is_active: true,
        submitted_at: '2025-03-01T00:00:00Z',
        response_text: 'Answer',
        feedback: 'Cool',
        job: null,
      },
    ];
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissions: vi.fn(() => Promise.resolve(submissions)),
      getStudentHistory: vi.fn(() => Promise.reject(new Error('network fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      loadHistory: (pid: number) => Promise<void>;
      getHistory: (pid: number) => unknown[];
    };

    // Should not throw
    await comp.loadHistory(123);
    fixture.detectChanges();

    expect(comp.getHistory(123)).toHaveLength(0);
  });

  it('should not refetch history if already cached and display no-feedback prior', async () => {
    const submissions = [
      {
        id: 100,
        activity_id: 10,
        student_pid: 123,
        is_active: true,
        submitted_at: '2025-03-01T00:00:00Z',
        response_text: 'Current answer',
        feedback: 'Good!',
        job: { id: 42, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
      },
    ];
    const history = [
      {
        id: 99,
        activity_id: 10,
        student_pid: 123,
        is_active: false,
        submitted_at: '2025-02-15T00:00:00Z',
        response_text: 'Old response',
        feedback: null,
        job: null,
      },
    ];
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      listSubmissions: vi.fn(() => Promise.resolve(submissions)),
      getStudentHistory: vi.fn(() => Promise.resolve(history)),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const comp = fixture.componentInstance as unknown as {
      loadHistory: (pid: number) => Promise<void>;
      selectHistorySubmission: (sub: unknown) => void;
      selectedHistorySub: () => unknown;
    };

    // Load history first time
    await comp.loadHistory(123);
    fixture.detectChanges();
    expect(mockActivityService.getStudentHistory).toHaveBeenCalledTimes(1);

    // Second call should be cached — no additional fetch
    await comp.loadHistory(123);
    expect(mockActivityService.getStudentHistory).toHaveBeenCalledTimes(1);

    // Select no-feedback submission to test the false branch of @if(prior.feedback)
    comp.selectHistorySubmission(history[0]);
    fixture.detectChanges();
    // Find the prior submission card via its unique mat-card-title text
    const titles = Array.from(fixture.nativeElement.querySelectorAll('mat-card-title'));
    const priorTitle = titles.find(
      (el: unknown) => (el as HTMLElement).textContent?.trim() === 'Prior Submission',
    ) as HTMLElement | undefined;
    expect(priorTitle).toBeTruthy();
    const priorCard = priorTitle!.closest('mat-card') as HTMLElement;
    // The card should show the response text but NOT the feedback section
    expect(priorCard.textContent).toContain('Old response');
    expect(priorCard.textContent).not.toContain('Feedback:');
  });
});
