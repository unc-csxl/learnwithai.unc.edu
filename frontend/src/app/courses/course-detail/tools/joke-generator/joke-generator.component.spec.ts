import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { signal, WritableSignal } from '@angular/core';
import { JokeGenerator } from './joke-generator.component';
import { JokeGeneratorService } from '../joke-generator.service';
import { PageTitleService } from '../../../../page-title.service';
import { SuccessSnackbarService } from '../../../../success-snackbar.service';
import { JobUpdateService, JobUpdate } from '../../../../job-update.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { AsyncJobInfo, JokeRequest } from '../../../../api/models';

const fakeRequest: JokeRequest = {
  id: 1,
  prompt: 'Tell me jokes about recursion',
  jokes: ['Why do recursive functions never finish? Because they keep calling themselves!'],
  created_at: '2025-01-01T00:00:00Z',
  job: { id: 10, status: 'completed', completed_at: '2025-01-01T00:01:00Z' },
};

const fakePendingRequest: JokeRequest = {
  id: 2,
  prompt: 'Jokes about algorithms',
  jokes: [],
  created_at: '2025-01-01T00:02:00Z',
  job: { id: 20, status: 'pending', completed_at: null },
};

function formatExpectedCompletedAt(completedAt: string): string {
  const completedDate = new Date(completedAt);
  const month = new Intl.DateTimeFormat('en-US', { month: 'long' }).format(completedDate);
  const day = completedDate.getDate();
  const year = completedDate.getFullYear();
  const hours = completedDate.getHours();
  const minutes = completedDate.getMinutes();
  const displayHour = hours % 12 || 12;
  const meridiem = hours >= 12 ? 'pm' : 'am';
  const time =
    minutes === 0
      ? `${displayHour}${meridiem}`
      : `${displayHour}:${minutes.toString().padStart(2, '0')}${meridiem}`;

  return `${month} ${day}${ordinalSuffix(day)}, ${year} at ${time}`;
}

function ordinalSuffix(day: number): string {
  if (day >= 11 && day <= 13) return 'th';

  switch (day % 10) {
    case 1:
      return 'st';
    case 2:
      return 'nd';
    case 3:
      return 'rd';
    default:
      return 'th';
  }
}

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('JokeGenerator', () => {
  let jobUpdateSignal: WritableSignal<JobUpdate | null>;

  async function setup(options: { requests?: JokeRequest[]; listError?: boolean } = {}) {
    jobUpdateSignal = signal<JobUpdate | null>(null);

    const mockService = {
      list: options.listError
        ? vi.fn(() => Promise.reject(new Error('fail')))
        : vi.fn(() => Promise.resolve(options.requests ?? [fakeRequest])),
      create: vi.fn(() => Promise.resolve(fakePendingRequest)),
      get: vi.fn(() =>
        Promise.resolve({
          ...fakePendingRequest,
          job: { id: 20, status: 'completed' as const, completed_at: '2025-01-01T00:03:00Z' },
          jokes: ['Ha!'],
        }),
      ),
      delete: vi.fn(() => Promise.resolve()),
    };

    const mockJobUpdate = {
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      updateForJob: vi.fn(() => jobUpdateSignal.asReadonly()),
    };
    const mockLayoutNavigation = { clearContext: vi.fn() };

    const mockSnackbar = { open: vi.fn() };

    const mockRoute = {
      parent: {
        parent: { snapshot: { paramMap: new Map([['id', '1']]) } },
      },
    };

    TestBed.configureTestingModule({
      imports: [JokeGenerator, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: JokeGeneratorService, useValue: mockService },
        { provide: JobUpdateService, useValue: mockJobUpdate },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
        { provide: SuccessSnackbarService, useValue: mockSnackbar },
        {
          provide: PageTitleService,
          useValue: { title: vi.fn(), setTitle: vi.fn() },
        },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(JokeGenerator);
    fixture.detectChanges();
    await flush();
    fixture.detectChanges();

    return { fixture, mockService, mockJobUpdate, mockSnackbar, mockLayoutNavigation };
  }

  it('should set the page title', async () => {
    const { mockLayoutNavigation } = await setup();
    const titleService = TestBed.inject(PageTitleService);
    expect(mockLayoutNavigation.clearContext).toHaveBeenCalled();
    expect(titleService.setTitle).toHaveBeenCalledWith('Joke Generator');
  });

  it('should subscribe to job updates for the course', async () => {
    const { mockJobUpdate } = await setup();
    expect(mockJobUpdate.subscribe).toHaveBeenCalledWith(1);
  });

  it('should load and display joke requests', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Tell me jokes about recursion');
    expect(el.textContent).toContain(
      'Why do recursive functions never finish? Because they keep calling themselves!',
    );
    expect(el.textContent).toContain(formatExpectedCompletedAt('2025-01-01T00:01:00Z'));
    expect(el.textContent).not.toContain('Completed');
  });

  it('should format completed requests with a local-time human subtitle', async () => {
    const { fixture } = await setup();
    const component = fixture.componentInstance;

    expect(component['requestSubtitle'](fakeRequest.job)).toBe(
      formatExpectedCompletedAt('2025-01-01T00:01:00Z'),
    );
    expect(component['requestSubtitle'](fakePendingRequest.job)).toBe('Pending');

    const completedWithoutTimestamp: AsyncJobInfo = {
      id: 99,
      status: 'completed',
      completed_at: null,
    };
    expect(component['requestSubtitle'](completedWithoutTimestamp)).toBe('');
  });

  it('should format ordinal suffixes and optional minutes correctly', async () => {
    const { fixture } = await setup();
    const component = fixture.componentInstance;

    expect(component['formatCompletedAt']('2026-03-01T15:00:00Z')).toBe(
      formatExpectedCompletedAt('2026-03-01T15:00:00Z'),
    );
    expect(component['formatCompletedAt']('2026-03-02T15:05:00Z')).toBe(
      formatExpectedCompletedAt('2026-03-02T15:05:00Z'),
    );
    expect(component['formatCompletedAt']('2026-03-03T15:00:00Z')).toBe(
      formatExpectedCompletedAt('2026-03-03T15:00:00Z'),
    );
    expect(component['formatCompletedAt']('2026-03-04T15:00:00Z')).toBe(
      formatExpectedCompletedAt('2026-03-04T15:00:00Z'),
    );
    expect(component['formatCompletedAt']('2026-03-11T15:00:00Z')).toBe(
      formatExpectedCompletedAt('2026-03-11T15:00:00Z'),
    );
    expect(component['formatCompletedAt']('not-a-date')).toBe('');
  });

  it('should show empty state when no requests exist', async () => {
    const { fixture } = await setup({ requests: [] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('No joke requests yet');
  });

  it('should show error when list fails to load', async () => {
    const { fixture } = await setup({ listError: true });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to load joke requests');
  });

  it('should submit a joke request and prepend it to the list', async () => {
    const { fixture, mockService, mockSnackbar } = await setup({ requests: [fakeRequest] });
    const component = fixture.componentInstance;

    component['form'].setValue({ prompt: 'Tell me puns' });
    fixture.detectChanges();

    const formEl = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    formEl.dispatchEvent(new Event('submit'));
    await flush();
    fixture.detectChanges();

    expect(mockService.create).toHaveBeenCalledWith(1, 'Tell me puns');
    expect(mockSnackbar.open).toHaveBeenCalledWith('Joke request submitted!');

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Jokes about algorithms');
  });

  it('should handle created request with null job without watching', async () => {
    const nullJobRequest: JokeRequest = {
      id: 5,
      prompt: 'Null job',
      jokes: [],
      created_at: '2025-01-01T00:00:00Z',
      job: null,
    };
    const { fixture, mockService, mockJobUpdate } = await setup({ requests: [] });
    mockService.create.mockResolvedValueOnce(nullJobRequest);
    const component = fixture.componentInstance;

    component['form'].setValue({ prompt: 'Null job' });
    await component['onSubmit']();
    fixture.detectChanges();

    expect(mockJobUpdate.updateForJob).not.toHaveBeenCalled();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Null job');
  });

  it('should delete a joke request and remove it from the list', async () => {
    const { fixture, mockService, mockSnackbar } = await setup({ requests: [fakeRequest] });

    const deleteBtn = fixture.nativeElement.querySelector(
      'button[aria-label="Delete joke request"]',
    ) as HTMLButtonElement;
    deleteBtn.click();
    await flush();
    fixture.detectChanges();

    expect(mockService.delete).toHaveBeenCalledWith(1, 1);
    expect(mockSnackbar.open).toHaveBeenCalledWith('Joke request deleted.');

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).not.toContain('Tell me jokes about recursion');
  });

  it('should show pending indicator for in-progress requests', async () => {
    const { fixture } = await setup({ requests: [fakePendingRequest] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Generating jokes');
  });

  it('should watch pending jobs and refresh when completed', async () => {
    const { fixture, mockService, mockJobUpdate } = await setup({
      requests: [fakeRequest, fakePendingRequest],
    });

    expect(mockJobUpdate.updateForJob).toHaveBeenCalledWith(20);

    // Simulate intermediate status that should be ignored
    jobUpdateSignal.set({
      job_id: 20,
      course_id: 1,
      user_id: 1,
      kind: 'joke_generation',
      status: 'processing',
    });
    await flush();
    fixture.detectChanges();
    expect(mockService.get).not.toHaveBeenCalled();

    // Simulate job completion via WebSocket
    jobUpdateSignal.set({
      job_id: 20,
      course_id: 1,
      user_id: 1,
      kind: 'joke_generation',
      status: 'completed',
    });

    await flush();
    fixture.detectChanges();

    expect(mockService.get).toHaveBeenCalledWith(1, 2);
  });

  it('should not submit when form is invalid', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;

    // Form starts empty, which is invalid
    component['form'].setValue({ prompt: '' });
    await component['onSubmit']();

    expect(mockService.create).not.toHaveBeenCalled();
  });

  it('should show error when submission fails', async () => {
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;

    mockService.create.mockRejectedValueOnce(new Error('fail'));
    component['form'].setValue({ prompt: 'Tell me jokes' });
    await component['onSubmit']();
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to submit joke request');
  });

  it('should show error when delete fails', async () => {
    const { fixture, mockService } = await setup({ requests: [fakeRequest] });
    const component = fixture.componentInstance;

    mockService.delete.mockRejectedValueOnce(new Error('fail'));
    await component['onDelete'](1);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed to delete joke request');
  });

  it('should show spinner while submitting', async () => {
    let resolveCreate!: (value: JokeRequest) => void;
    const { fixture, mockService } = await setup();
    const component = fixture.componentInstance;

    mockService.create.mockReturnValueOnce(
      new Promise<JokeRequest>((res) => {
        resolveCreate = res;
      }),
    );

    component['form'].setValue({ prompt: 'Tell me jokes' });
    const submitPromise = component['onSubmit']();
    fixture.detectChanges();

    expect(component['submitting']()).toBe(true);

    resolveCreate(fakePendingRequest);
    await submitPromise;
    fixture.detectChanges();

    expect(component['submitting']()).toBe(false);
  });

  it('should unsubscribe from job updates on destroy', async () => {
    const { fixture, mockJobUpdate } = await setup({ requests: [fakePendingRequest] });
    fixture.destroy();
    expect(mockJobUpdate.unsubscribe).toHaveBeenCalledWith(1);
  });

  it('should return fallback labels for unknown status', async () => {
    const { fixture } = await setup();
    const component = fixture.componentInstance;
    expect(component['statusLabel']('unknown')).toBe('Unknown');
    expect(component['statusIcon']('unknown')).toBe('help');
  });

  it('should silently handle refreshJob errors', async () => {
    const { fixture, mockService } = await setup({
      requests: [fakePendingRequest],
    });

    mockService.get.mockRejectedValueOnce(new Error('fail'));

    jobUpdateSignal.set({
      job_id: 20,
      course_id: 1,
      user_id: 1,
      kind: 'joke_generation',
      status: 'completed',
    });

    await flush();
    fixture.detectChanges();

    expect(mockService.get).toHaveBeenCalledWith(1, 2);
    // The list should still contain the old request
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Jokes about algorithms');
  });

  it('should read status from nested job field (regression)', async () => {
    const { fixture } = await setup({ requests: [fakePendingRequest] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Pending');
    expect(el.querySelector('.pending-indicator')).toBeTruthy();
    expect(el.querySelector('mat-spinner')).toBeTruthy();
  });

  it('should track async job ID for WebSocket updates (regression)', async () => {
    const { mockJobUpdate } = await setup({
      requests: [fakePendingRequest],
    });
    // Must watch the async_job.id (20), not the joke.id (2)
    expect(mockJobUpdate.updateForJob).toHaveBeenCalledWith(20);
    expect(mockJobUpdate.updateForJob).not.toHaveBeenCalledWith(2);
  });

  it('should display the failed status style and label', async () => {
    const failedRequest: JokeRequest = {
      id: 3,
      prompt: 'Bad prompt',
      jokes: [],
      created_at: '2025-01-01T00:00:00Z',
      job: { id: 30, status: 'failed', completed_at: null },
    };
    const { fixture } = await setup({ requests: [failedRequest] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Failed');
    expect(el.querySelector('.status-failed')).toBeTruthy();
  });

  it('should handle a request with null job gracefully', async () => {
    const orphanRequest: JokeRequest = {
      id: 4,
      prompt: 'Orphan prompt',
      jokes: ['A joke'],
      created_at: '2025-01-01T00:00:00Z',
      job: null,
    };
    const { fixture } = await setup({ requests: [orphanRequest] });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Orphan prompt');
    expect(el.textContent).toContain('A joke');
    expect(el.textContent).toContain('Unknown');
  });
});
