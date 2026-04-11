/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatDialog } from '@angular/material/dialog';
import { JobControlComponent } from './job-control.component';
import { OperationsService } from '../operations.service';
import { JobControlOverview, QueueInfo, WorkerInfo, JobFailures } from '../../api/models';

const STUB_OVERVIEW: JobControlOverview = {
  total_queued: 10,
  total_unacked: 2,
  dlq_depth: 1,
  retry_depth: 0,
  consumers_online: 4,
  broker_alarms: [],
};

const STUB_QUEUES: QueueInfo[] = [
  {
    name: 'default',
    ready: 5,
    unacked: 1,
    consumers: 2,
    ack_rate: 1.5,
    is_dlq: false,
    is_retry: false,
  },
  {
    name: 'default.DQ',
    ready: 1,
    unacked: 0,
    consumers: 0,
    ack_rate: 0,
    is_dlq: true,
    is_retry: false,
  },
];

const STUB_WORKERS: WorkerInfo[] = [
  { consumer_tag: 'worker.1', queue: 'default', channel_details: 'ch-1', prefetch_count: 1 },
];

const STUB_FAILURES: JobFailures = {
  dlq_messages: 1,
  recent_failed_jobs: [
    {
      id: 42,
      kind: 'roster_upload',
      course_id: 100,
      error_message: 'Parse error',
      created_at: '2026-01-01T00:00:00Z',
      completed_at: null,
    },
  ],
  error_buckets: { roster_upload: 1 },
};

type SetupOptions = {
  error?: boolean;
  overview?: JobControlOverview;
  queues?: QueueInfo[];
  workers?: WorkerInfo[];
  failures?: JobFailures;
  dialogConfirmed?: boolean;
};

function setup(opts: SetupOptions = {}) {
  const overview = opts.overview ?? STUB_OVERVIEW;
  const queues = opts.queues ?? STUB_QUEUES;
  const workers = opts.workers ?? STUB_WORKERS;
  const failures = opts.failures ?? STUB_FAILURES;

  const mockService = {
    getJobsOverview: opts.error
      ? vi.fn().mockRejectedValue(new Error('fail'))
      : vi.fn().mockResolvedValue(overview),
    getJobsQueues: opts.error
      ? vi.fn().mockRejectedValue(new Error('fail'))
      : vi.fn().mockResolvedValue(queues),
    getJobsWorkers: opts.error
      ? vi.fn().mockRejectedValue(new Error('fail'))
      : vi.fn().mockResolvedValue(workers),
    getJobsFailures: opts.error
      ? vi.fn().mockRejectedValue(new Error('fail'))
      : vi.fn().mockResolvedValue(failures),
    purgeQueue: vi.fn().mockResolvedValue(undefined),
  };

  const mockDialog = {
    open: vi.fn().mockReturnValue({
      afterClosed: () => ({ toPromise: () => Promise.resolve(opts.dialogConfirmed ?? false) }),
    }),
  };

  TestBed.configureTestingModule({
    imports: [NoopAnimationsModule],
    providers: [
      { provide: OperationsService, useValue: mockService },
      { provide: MatDialog, useValue: mockDialog },
    ],
  });

  const fixture = TestBed.createComponent(JobControlComponent);
  fixture.detectChanges();

  return { fixture, mockService, mockDialog };
}

async function setupAndLoad(opts: SetupOptions = {}) {
  const result = setup(opts);
  // Flush microtasks from the async ngOnInit / Promise.all
  await new Promise((resolve) => setTimeout(resolve, 0));
  result.fixture.detectChanges();
  return result;
}

describe('JobControlComponent', () => {
  it('should create the component', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should show loading spinner initially', () => {
    const mockService = {
      getJobsOverview: vi.fn().mockReturnValue(new Promise(() => {})),
      getJobsQueues: vi.fn().mockReturnValue(new Promise(() => {})),
      getJobsWorkers: vi.fn().mockReturnValue(new Promise(() => {})),
      getJobsFailures: vi.fn().mockReturnValue(new Promise(() => {})),
    };

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [{ provide: OperationsService, useValue: mockService }],
    });

    const fixture = TestBed.createComponent(JobControlComponent);
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector('mat-spinner');
    expect(spinner).toBeTruthy();
  });

  it('should display overview stats after loading', async () => {
    const { fixture } = await setupAndLoad();

    const statValues = fixture.nativeElement.querySelectorAll(
      '.stat-bar:not(.compact) .stat-value',
    );
    expect(statValues.length).toBe(5);
    expect(statValues[0].textContent.trim()).toBe('10');
    expect(statValues[4].textContent.trim()).toBe('4');
  });

  it('should display queue table', async () => {
    const { fixture } = await setupAndLoad();

    const rows = fixture.nativeElement.querySelectorAll(
      '.queue-table tbody tr, .queue-table mat-row',
    );
    expect(rows.length).toBe(2);
  });

  it('should display DLQ badge for DLQ queues', async () => {
    const { fixture } = await setupAndLoad();

    const badges = fixture.nativeElement.querySelectorAll('.badge-dlq');
    expect(badges.length).toBe(1);
  });

  it('should display worker table', async () => {
    const { fixture } = await setupAndLoad();

    const rows = fixture.nativeElement.querySelectorAll(
      '.worker-table tbody tr, .worker-table mat-row',
    );
    expect(rows.length).toBe(1);
  });

  it('should display failure summary', async () => {
    const { fixture } = await setupAndLoad();

    const failedCards = fixture.nativeElement.querySelectorAll('.failed-job-card');
    expect(failedCards.length).toBe(1);
  });

  it('should show error message on load failure', async () => {
    const { fixture } = await setupAndLoad({ error: true });

    const error = fixture.nativeElement.querySelector('.error-message');
    expect(error).toBeTruthy();
    expect(error.textContent).toContain('Failed to load job control data');
  });

  it('should display alarm banner when broker has alarms', async () => {
    const mockService = {
      getJobsOverview: vi.fn().mockResolvedValue({ ...STUB_OVERVIEW, broker_alarms: ['disk'] }),
      getJobsQueues: vi.fn().mockResolvedValue(STUB_QUEUES),
      getJobsWorkers: vi.fn().mockResolvedValue(STUB_WORKERS),
      getJobsFailures: vi.fn().mockResolvedValue(STUB_FAILURES),
    };
    const mockDialog = {
      open: vi.fn().mockReturnValue({
        afterClosed: () => ({ toPromise: () => Promise.resolve(false) }),
      }),
    };

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [
        { provide: OperationsService, useValue: mockService },
        { provide: MatDialog, useValue: mockDialog },
      ],
    });

    const fixture = TestBed.createComponent(JobControlComponent);
    fixture.detectChanges();
    await new Promise((resolve) => setTimeout(resolve, 0));
    fixture.detectChanges();

    const banner = fixture.nativeElement.querySelector('.alarm-banner');
    expect(banner).toBeTruthy();
    expect(banner.textContent).toContain('disk');
  });

  it('should toggle auto-refresh off and on', async () => {
    const clearIntervalSpy = vi.spyOn(globalThis, 'clearInterval');

    const { fixture } = await setupAndLoad();
    const toggle = fixture.nativeElement.querySelector('mat-slide-toggle');
    expect(toggle).toBeTruthy();

    toggle.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    toggle.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
  });

  it('should refresh on the auto-refresh interval and cleanup on destroy', async () => {
    vi.useFakeTimers();
    const clearIntervalSpy = vi.spyOn(window, 'clearInterval');

    try {
      const { fixture, mockService } = setup();

      await vi.advanceTimersByTimeAsync(0);
      await Promise.resolve();
      fixture.detectChanges();

      await vi.advanceTimersByTimeAsync(10_000);
      await Promise.resolve();
      fixture.detectChanges();

      expect(mockService.getJobsOverview).toHaveBeenCalledTimes(2);

      fixture.destroy();
      expect(clearIntervalSpy).toHaveBeenCalled();
    } finally {
      clearIntervalSpy.mockRestore();
      vi.useRealTimers();
    }
  });

  it('should purge queue and reload when dialog is confirmed', async () => {
    const { fixture, mockService } = await setupAndLoad({ dialogConfirmed: true });
    const component = fixture.componentInstance as unknown as {
      confirmPurge: (queue: QueueInfo) => Promise<void>;
      dialog: {
        open: () => { afterClosed: () => { toPromise: () => Promise<boolean> } };
      };
    };
    const mockDialog = {
      open: vi.fn().mockReturnValue({
        afterClosed: () => ({ toPromise: () => Promise.resolve(true) }),
      }),
    };
    component.dialog = mockDialog;

    await component.confirmPurge(STUB_QUEUES[0]);
    await new Promise((resolve) => setTimeout(resolve, 0));
    fixture.detectChanges();

    expect(mockDialog.open).toHaveBeenCalled();
    expect(mockService.purgeQueue).toHaveBeenCalledWith('default');
    expect(mockService.getJobsOverview).toHaveBeenCalledTimes(2);
  });

  it('should not purge queue when dialog is cancelled', async () => {
    const { fixture, mockService } = await setupAndLoad({ dialogConfirmed: false });
    const component = fixture.componentInstance as unknown as {
      confirmPurge: (queue: QueueInfo) => Promise<void>;
      dialog: {
        open: () => { afterClosed: () => { toPromise: () => Promise<boolean> } };
      };
    };
    component.dialog = {
      open: vi.fn().mockReturnValue({
        afterClosed: () => ({ toPromise: () => Promise.resolve(false) }),
      }),
    };

    await component.confirmPurge(STUB_QUEUES[0]);
    await new Promise((resolve) => setTimeout(resolve, 0));
    fixture.detectChanges();

    expect(mockService.purgeQueue).not.toHaveBeenCalled();
    expect(mockService.getJobsOverview).toHaveBeenCalledTimes(1);
  });

  it('should display retry badge and hide purge for empty queue', async () => {
    const { fixture } = await setupAndLoad({
      queues: [
        {
          name: 'default.XQ',
          ready: 0,
          unacked: 0,
          consumers: 0,
          ack_rate: 0,
          is_dlq: false,
          is_retry: true,
        },
      ],
    });

    const retryBadge = fixture.nativeElement.querySelector('.badge-retry');
    expect(retryBadge).toBeTruthy();

    const purgeButton = fixture.nativeElement.querySelector(
      'button[aria-label="Purge default.XQ"]',
    );
    expect(purgeButton).toBeNull();
  });

  it('should call confirmPurge when purge button is clicked', async () => {
    const { fixture } = await setupAndLoad();
    const component = fixture.componentInstance as unknown as {
      confirmPurge: (queue: QueueInfo) => Promise<void>;
    };
    const confirmPurgeSpy = vi.spyOn(component, 'confirmPurge').mockResolvedValue();

    const purgeButton = fixture.nativeElement.querySelector('button[aria-label="Purge default"]');
    expect(purgeButton).toBeTruthy();

    purgeButton.click();

    expect(confirmPurgeSpy).toHaveBeenCalledWith(STUB_QUEUES[0]);
  });

  it('should show empty states for queues, failures, and workers', async () => {
    const { fixture } = await setupAndLoad({
      queues: [],
      workers: [],
      failures: {
        dlq_messages: 0,
        recent_failed_jobs: [],
        error_buckets: {},
      },
    });

    const emptyStates = Array.from(
      fixture.nativeElement.querySelectorAll('.empty-state'),
      (node: Element) => node.textContent?.trim(),
    );

    expect(emptyStates).toContain('No queues found.');
    expect(emptyStates).toContain('No recent failures.');
    expect(emptyStates).toContain('No active workers.');
  });

  it('should hide overview pane when overview state is null', async () => {
    const { fixture } = await setupAndLoad();
    const component = fixture.componentInstance as unknown as {
      overview: { set: (value: JobControlOverview | null) => void };
      loading: { set: (value: boolean) => void };
      errorMessage: { set: (value: string) => void };
    };

    component.overview.set(null);
    component.loading.set(false);
    component.errorMessage.set('');
    fixture.detectChanges();

    const overviewPane = fixture.nativeElement.querySelector('section[aria-label="Overview"]');
    expect(overviewPane).toBeNull();
  });

  it('should hide failures pane when failures state is null', async () => {
    const { fixture } = await setupAndLoad();
    const component = fixture.componentInstance as unknown as {
      failures: { set: (value: JobFailures | null) => void };
      loading: { set: (value: boolean) => void };
      errorMessage: { set: (value: string) => void };
    };

    component.failures.set(null);
    component.loading.set(false);
    component.errorMessage.set('');
    fixture.detectChanges();

    const failuresPane = fixture.nativeElement.querySelector('section[aria-label="Failures"]');
    expect(failuresPane).toBeNull();
  });

  it('should hide failed job error paragraph when job has no error message', async () => {
    const { fixture } = await setupAndLoad({
      failures: {
        dlq_messages: 1,
        recent_failed_jobs: [
          {
            id: 42,
            kind: 'roster_upload',
            course_id: 100,
            error_message: null,
            created_at: '2026-01-01T00:00:00Z',
            completed_at: null,
          },
        ],
        error_buckets: { roster_upload: 1 },
      },
    });

    const errorParagraph = fixture.nativeElement.querySelector('.failed-job-error');
    expect(errorParagraph).toBeNull();
  });
});
