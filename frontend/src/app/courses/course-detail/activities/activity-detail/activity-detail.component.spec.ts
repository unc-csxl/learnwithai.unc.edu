import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { signal, WritableSignal } from '@angular/core';
import { ActivityDetail } from './activity-detail.component';
import { PageTitleService } from '../../../../page-title.service';
import { JobUpdateService } from '../../../../job-update.service';
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

    TestBed.configureTestingModule({
      imports: [ActivityDetail],
      providers: [
        provideRouter([]),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: JobUpdateService, useValue: mockJobUpdate },
        { provide: ActivityService, useValue: mockActivityService },
        { provide: ActivatedRoute, useValue: mockRoute },
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
});
