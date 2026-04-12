/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatDialog } from '@angular/material/dialog';
import { vi } from 'vitest';
import { JobControlComponent } from './job-control.component';
import { ConfirmPurgeDialogComponent } from './confirm-purge-dialog.component';
import { OperationsService } from '../operations.service';
import { JobControlOverview, QueueInfo, QueueMessagePreview, WorkerInfo } from '../../api/models';
import { PageTitleService } from '../../page-title.service';

const STUB_OVERVIEW: JobControlOverview = {
  total_queued: 14,
  total_unacked: 2,
  dlq_depth: 7,
  retry_depth: 1,
  consumers_online: 3,
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
    message_ttl_ms: null,
    dead_letter_exchange: null,
    dead_letter_routing_key: null,
  },
  {
    name: 'default.DQ',
    ready: 1,
    unacked: 0,
    consumers: 1,
    ack_rate: 0,
    is_dlq: false,
    is_retry: true,
    message_ttl_ms: 30000,
    dead_letter_exchange: '',
    dead_letter_routing_key: 'default',
  },
  {
    name: 'default.XQ',
    ready: 7,
    unacked: 0,
    consumers: 0,
    ack_rate: 0,
    is_dlq: true,
    is_retry: false,
    message_ttl_ms: 604800000,
    dead_letter_exchange: null,
    dead_letter_routing_key: null,
  },
  {
    name: 'amq.gen-1234',
    ready: 0,
    unacked: 0,
    consumers: 1,
    ack_rate: 0,
    is_dlq: false,
    is_retry: false,
    message_ttl_ms: null,
    dead_letter_exchange: null,
    dead_letter_routing_key: null,
  },
];

const STUB_WORKERS: WorkerInfo[] = [
  {
    consumer_tag: 'worker.default',
    queue: 'default',
    channel_details: 'ch-default',
    prefetch_count: 4,
  },
  {
    consumer_tag: 'worker.retry',
    queue: 'default.DQ',
    channel_details: 'ch-default',
    prefetch_count: 4,
  },
  {
    consumer_tag: 'worker.live',
    queue: 'amq.gen-1234',
    channel_details: 'ch-live',
    prefetch_count: 0,
  },
];

const PAGE_ONE_PREVIEWS: QueueMessagePreview[] = Array.from({ length: 5 }, (_, index) => ({
  queue_name: 'default',
  routing_key: 'default.XQ',
  actor_name: 'job_queue',
  message_id: `preview-${index + 1}`,
  job_id: index + 1,
  job_type: 'iyow_feedback',
  retries: 3,
  enqueued_at: '2026-04-10T00:00:00Z',
  death_reason: 'rejected',
  source_queue: 'default',
  payload_preview: '{"args": [], "kwargs": {}}',
  error_summary: 'ValueError: AsyncJob not found',
}));

const PAGE_TWO_PREVIEWS: QueueMessagePreview[] = Array.from({ length: 2 }, (_, index) => ({
  queue_name: 'default',
  routing_key: 'default.XQ',
  actor_name: 'job_queue',
  message_id: `preview-${index + 6}`,
  job_id: index + 6,
  job_type: 'iyow_feedback',
  retries: 4,
  enqueued_at: '2026-04-11T00:00:00Z',
  death_reason: 'rejected',
  source_queue: 'default',
  payload_preview: '{"args": [], "kwargs": {}}',
  error_summary: 'ValueError: AsyncJob not found',
}));

type SetupOptions = {
  error?: boolean;
  overview?: JobControlOverview;
  queues?: QueueInfo[];
  workers?: WorkerInfo[];
  dialogConfirmed?: boolean;
  previewPages?: Record<string, Record<number, QueueMessagePreview[]>>;
  previewErrors?: string[];
};

function setup(options: SetupOptions = {}) {
  const overview = options.overview ?? STUB_OVERVIEW;
  const queues = options.queues ?? STUB_QUEUES;
  const workers = options.workers ?? STUB_WORKERS;
  const previewPages = options.previewPages ?? {
    'default.XQ': {
      1: PAGE_ONE_PREVIEWS,
      2: PAGE_TWO_PREVIEWS,
    },
  };
  const previewErrors = new Set(options.previewErrors ?? []);

  const mockService = {
    getJobsOverview: options.error
      ? vi.fn().mockRejectedValue(new Error('fail'))
      : vi.fn().mockResolvedValue(overview),
    getJobsQueues: options.error
      ? vi.fn().mockRejectedValue(new Error('fail'))
      : vi.fn().mockResolvedValue(queues),
    getJobsWorkers: options.error
      ? vi.fn().mockRejectedValue(new Error('fail'))
      : vi.fn().mockResolvedValue(workers),
    getJobsFailures: vi.fn().mockResolvedValue({}),
    getJobQueuePreview: options.error
      ? vi.fn().mockRejectedValue(new Error('fail'))
      : vi.fn().mockImplementation((...args: [string, number?, number?]) => {
          const [queueName, , page = 1] = args;
          if (previewErrors.has(queueName)) {
            return Promise.reject(new Error('preview fail'));
          }
          return Promise.resolve(previewPages[queueName]?.[page] ?? []);
        }),
    purgeQueue: vi.fn().mockResolvedValue(undefined),
  };

  const mockDialog = {
    open: vi.fn().mockReturnValue({
      afterClosed: () => ({ toPromise: () => Promise.resolve(options.dialogConfirmed ?? false) }),
    }),
  };
  const mockTitle = {
    setTitle: vi.fn(),
    title: vi.fn(),
  };

  TestBed.configureTestingModule({
    imports: [NoopAnimationsModule],
    providers: [
      { provide: OperationsService, useValue: mockService },
      { provide: MatDialog, useValue: mockDialog },
      { provide: PageTitleService, useValue: mockTitle },
    ],
  });

  const fixture = TestBed.createComponent(JobControlComponent);
  fixture.detectChanges();

  return { fixture, mockDialog, mockService, mockTitle };
}

async function setupAndLoad(options: SetupOptions = {}) {
  const result = setup(options);
  await new Promise((resolve) => setTimeout(resolve, 0));
  result.fixture.detectChanges();
  return result;
}

describe('JobControlComponent', () => {
  it('creates the component and sets the page title', () => {
    const { fixture, mockTitle } = setup();

    expect(fixture.componentInstance).toBeTruthy();
    expect(mockTitle.setTitle).toHaveBeenCalledWith('Job Queue Control');
  });

  it('formats queue labels and insights with the requested copy', () => {
    const { fixture } = setup();
    const component = fixture.componentInstance as unknown as {
      queueDisplayNameFromName: (queueName: string) => string;
      queueBadgeLabel: (queue: { name: string; is_dlq: boolean; is_retry: boolean }) => string;
      queueStatusLabel: (queue: { name: string; is_dlq: boolean; is_retry: boolean }) => string;
      formatDuration: (ttl: number | null | undefined, missing?: string) => string;
      queueShowsUnacked: (queue: { name: string; is_dlq: boolean }) => boolean;
      queueShowsConsumers: (queue: { is_dlq: boolean }) => boolean;
      queueShowsAckRate: (queue: { name: string; is_dlq: boolean; is_retry: boolean }) => boolean;
      deadLetterPreviewFor: (queueName: string) => QueueMessagePreview[];
      deadLetterPreviewPage: (queueName: string) => number;
    };

    expect(component.queueDisplayNameFromName('default')).toBe('Jobs');
    expect(component.queueDisplayNameFromName('default.DQ')).toBe('Retry Queue');
    expect(component.queueDisplayNameFromName('default.XQ')).toBe('Failed');
    expect(component.queueDisplayNameFromName('reports.DQ')).toBe('Reports Retry Queue');
    expect(component.queueDisplayNameFromName('reports.XQ')).toBe('Reports Failed');
    expect(component.queueDisplayNameFromName('amq.gen-123')).toBe('Notifications');
    expect(component.queueBadgeLabel({ name: 'amq.gen-123', is_dlq: false, is_retry: false })).toBe(
      'Fanout Exchange',
    );
    expect(component.queueStatusLabel({ name: 'default', is_dlq: false, is_retry: false })).toBe(
      'Jobs',
    );
    expect(component.queueStatusLabel({ name: 'default.XQ', is_dlq: true, is_retry: false })).toBe(
      'Failed',
    );
    expect(component.queueStatusLabel({ name: 'default.DQ', is_dlq: false, is_retry: true })).toBe(
      'Retry Queue',
    );
    expect(
      component.queueStatusLabel({ name: 'amq.gen-123', is_dlq: false, is_retry: false }),
    ).toBe('Notifications');
    expect(component.formatDuration(1000)).toBe('1s');
    expect(component.formatDuration(60000)).toBe('1m');
    expect(component.formatDuration(1501)).toBe('1501 ms');
    expect(component.formatDuration(null, 'No automatic expiry')).toBe('No automatic expiry');
    expect(component.queueShowsUnacked({ name: 'default', is_dlq: false })).toBe(true);
    expect(component.queueShowsUnacked({ name: 'amq.gen-123', is_dlq: false })).toBe(false);
    expect(component.queueShowsConsumers({ is_dlq: true })).toBe(false);
    expect(component.queueShowsAckRate({ name: 'default.DQ', is_dlq: false, is_retry: true })).toBe(
      false,
    );
    expect(component.deadLetterPreviewFor('missing')).toEqual([]);
    expect(component.deadLetterPreviewPage('missing')).toBe(1);
  });

  it('derives worker group labels for fallback worker combinations', () => {
    const { fixture } = setup();
    const component = fixture.componentInstance as unknown as {
      workerGroupDisplayName: (workers: WorkerInfo[]) => string;
      workerGroupRoleLabel: (workers: WorkerInfo[]) => string;
    };

    expect(
      component.workerGroupDisplayName([
        {
          consumer_tag: 'worker.alpha',
          queue: 'alpha',
          channel_details: 'ch-alpha',
          prefetch_count: 1,
        },
        {
          consumer_tag: 'worker.beta',
          queue: 'beta',
          channel_details: 'ch-beta',
          prefetch_count: 1,
        },
      ]),
    ).toBe('Worker');
    expect(
      component.workerGroupRoleLabel([
        {
          consumer_tag: 'worker.jobs',
          queue: 'default',
          channel_details: 'ch-jobs',
          prefetch_count: 1,
        },
      ]),
    ).toBe('Jobs');
    expect(
      component.workerGroupRoleLabel([
        {
          consumer_tag: 'worker.retry',
          queue: 'default.DQ',
          channel_details: 'ch-retry',
          prefetch_count: 1,
        },
      ]),
    ).toBe('Retry Queue');
    expect(
      component.workerGroupRoleLabel([
        {
          consumer_tag: 'worker.failed',
          queue: 'default.XQ',
          channel_details: 'ch-failed',
          prefetch_count: 1,
        },
      ]),
    ).toBe('Failed');
    expect(component.workerGroupRoleLabel([])).toBe('Worker');
  });

  it('covers pagination guard and queue comparison helper branches', async () => {
    const { fixture, mockService } = await setupAndLoad();
    const component = fixture.componentInstance as unknown as {
      goToPreviousDeadLetterPage: (queue: QueueInfo) => Promise<void>;
      goToNextDeadLetterPage: (queue: QueueInfo) => Promise<void>;
      compareQueues: (left: QueueInfo, right: QueueInfo) => number;
    };

    await component.goToPreviousDeadLetterPage(STUB_QUEUES[2]);
    expect(mockService.getJobQueuePreview).toHaveBeenCalledTimes(1);

    await component.goToNextDeadLetterPage({ ...STUB_QUEUES[2], ready: 5 });
    expect(mockService.getJobQueuePreview).toHaveBeenCalledTimes(1);

    expect(
      component.compareQueues(
        { ...STUB_QUEUES[0], name: 'alpha' },
        { ...STUB_QUEUES[0], name: 'beta.jobs' },
      ),
    ).toBeLessThan(0);
    expect(component.compareQueues(STUB_QUEUES[0], STUB_QUEUES[1])).toBeLessThan(0);
    expect(
      component.compareQueues(
        { ...STUB_QUEUES[3], name: 'amq.gen-1' },
        { ...STUB_QUEUES[3], name: 'amq.gen-2' },
      ),
    ).toBeLessThan(0);
  });

  it('covers worker grouping and preview page fallback helpers', async () => {
    const { fixture, mockService } = await setupAndLoad();
    const component = fixture.componentInstance as unknown as {
      buildWorkerGroups: (workers: WorkerInfo[]) => Array<{
        id: string;
        displayName: string;
        subscriptionSummary: string;
      }>;
      loadDeadLetterPreviews: (
        queues: QueueInfo[],
        pages: Record<string, number>,
      ) => Promise<Record<string, QueueMessagePreview[]>>;
    };

    const workerGroups = component.buildWorkerGroups([
      {
        consumer_tag: 'worker.alpha',
        queue: 'alpha',
        channel_details: '',
        prefetch_count: 2,
      },
    ]);

    expect(workerGroups).toEqual([
      expect.objectContaining({
        id: 'worker.alpha',
        displayName: 'Alpha worker',
        subscriptionSummary: '',
      }),
    ]);

    await component.loadDeadLetterPreviews([STUB_QUEUES[2]], {});

    expect(mockService.getJobQueuePreview).toHaveBeenCalledWith('default.XQ', 5, 1);
  });

  it('shows the loading spinner while initial requests are unresolved', () => {
    const mockService = {
      getJobsOverview: vi.fn().mockReturnValue(new Promise(() => {})),
      getJobsQueues: vi.fn().mockReturnValue(new Promise(() => {})),
      getJobsWorkers: vi.fn().mockReturnValue(new Promise(() => {})),
      getJobQueuePreview: vi.fn().mockReturnValue(new Promise(() => {})),
      purgeQueue: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [{ provide: OperationsService, useValue: mockService }],
    });

    const fixture = TestBed.createComponent(JobControlComponent);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('mat-spinner')).toBeTruthy();
  });

  it('renders the queue table and simplified failed jobs pane', async () => {
    const { fixture, mockService } = await setupAndLoad();
    const queueOrder = Array.from(
      fixture.nativeElement.querySelectorAll('.queue-table .queue-display-name'),
      (node: Element) => node.textContent?.trim(),
    );
    const failedJobsSection = fixture.nativeElement.querySelector(
      'section[aria-label="Failed Jobs"]',
    ) as HTMLElement;

    expect(mockService.getJobsFailures).not.toHaveBeenCalled();
    expect(mockService.getJobsOverview).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('Fanout Exchange');
    expect(fixture.nativeElement.textContent).toContain('Notifications');
    expect(fixture.nativeElement.textContent).toContain('Jobs');
    expect(fixture.nativeElement.textContent).toContain('Retry Queue');
    expect(fixture.nativeElement.textContent).toContain('Failed');
    expect(fixture.nativeElement.textContent).toContain('Failed Jobs');
    expect(queueOrder).toEqual(['Jobs', 'Retry Queue', 'Failed', 'Notifications']);
    expect(fixture.nativeElement.querySelector('section[aria-label="Overview"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('section[aria-label="Failures"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('section[aria-label="Delayed Queues"]')).toBeNull();
    expect(failedJobsSection).toBeTruthy();
    expect(failedJobsSection.querySelector('.detail-queue-insight')).toBeNull();
    expect(failedJobsSection.querySelector('.detail-queue-facts')).toBeNull();
  });

  it('hides DLQ purge actions in the queue table, highlights ready, and blanks non-applicable metrics', async () => {
    const { fixture } = await setupAndLoad();
    const queueRows = fixture.nativeElement.querySelectorAll('tr.mat-mdc-row');
    const deadLetterRow = (Array.from(queueRows) as HTMLElement[]).find((row) =>
      row.textContent?.includes('Failed'),
    ) as HTMLElement;

    expect(
      fixture.nativeElement.querySelector('button[aria-label="Purge Failed (default.XQ)"]'),
    ).toBeNull();
    expect(
      fixture.nativeElement.querySelector(
        'button[aria-label="Clear all retained messages from Failed (default.XQ)"]',
      ),
    ).toBeTruthy();
    expect(deadLetterRow.querySelector('.metric-attention')?.textContent?.trim()).toBe('7');

    const notApplicableCells = deadLetterRow.querySelectorAll('[aria-label="Not applicable"]');
    expect(notApplicableCells.length).toBe(3);
  });

  it('opens the purge confirmation from both queue action buttons', async () => {
    const { fixture } = await setupAndLoad({ dialogConfirmed: false });
    const dialogOpen = vi.fn().mockReturnValue({
      afterClosed: () => ({ toPromise: () => Promise.resolve(false) }),
    });
    const component = fixture.componentInstance as unknown as {
      dialog: {
        open: typeof dialogOpen;
      };
    };
    component.dialog = { open: dialogOpen };

    const queuePurgeButton = fixture.nativeElement.querySelector(
      'button[aria-label="Purge Jobs (default)"]',
    ) as HTMLButtonElement;
    queuePurgeButton.click();
    await new Promise((resolve) => setTimeout(resolve, 0));

    const deadLetterClearButton = fixture.nativeElement.querySelector(
      'button[aria-label="Clear all retained messages from Failed (default.XQ)"]',
    ) as HTMLButtonElement;
    deadLetterClearButton.click();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(dialogOpen).toHaveBeenCalledTimes(2);
    expect(dialogOpen).toHaveBeenNthCalledWith(
      1,
      ConfirmPurgeDialogComponent,
      expect.objectContaining({ data: { queueName: 'default' } }),
    );
    expect(dialogOpen).toHaveBeenNthCalledWith(
      2,
      ConfirmPurgeDialogComponent,
      expect.objectContaining({ data: { queueName: 'default.XQ' } }),
    );
  });

  it('pages through dead-letter previews five at a time', async () => {
    const { fixture, mockService } = await setupAndLoad();

    expect(mockService.getJobQueuePreview).toHaveBeenCalledWith('default.XQ', 5, 1);
    expect(fixture.nativeElement.textContent).toContain('Page 1 of 2 · Showing 1-5 of 7');

    const nextButton = fixture.nativeElement.querySelector(
      'button[aria-label="Show the next dead-letter page for Failed"]',
    ) as HTMLButtonElement;
    nextButton.click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    fixture.detectChanges();

    expect(mockService.getJobQueuePreview).toHaveBeenCalledWith('default.XQ', 5, 2);
    expect(fixture.nativeElement.textContent).toContain('Page 2 of 2 · Showing 6-7 of 7');
    expect(fixture.nativeElement.textContent).toContain('iyow_feedback #6');

    const previousButton = fixture.nativeElement.querySelector(
      'button[aria-label="Show the previous dead-letter page for Failed"]',
    ) as HTMLButtonElement;
    previousButton.click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    fixture.detectChanges();

    expect(mockService.getJobQueuePreview).toHaveBeenCalledWith('default.XQ', 5, 1);
    expect(fixture.nativeElement.textContent).toContain('Page 1 of 2 · Showing 1-5 of 7');
  });

  it('shows an empty preview state when loading retained messages fails', async () => {
    const { fixture } = await setupAndLoad({ previewErrors: ['default.XQ'] });

    expect(fixture.nativeElement.textContent).toContain('No preview messages available right now.');
  });

  it('hides failed-job actions when there are no retained messages', async () => {
    const { fixture } = await setupAndLoad({
      queues: STUB_QUEUES.map((queue) =>
        queue.name === 'default.XQ' ? { ...queue, ready: 0 } : queue,
      ),
      previewPages: {
        'default.XQ': {
          1: [],
        },
      },
    });

    expect(
      fixture.nativeElement.querySelector(
        'button[aria-label="Clear all retained messages from Failed (default.XQ)"]',
      ),
    ).toBeNull();
    expect(
      fixture.nativeElement.querySelector(
        'button[aria-label="Show the previous dead-letter page for Failed"]',
      ),
    ).toBeNull();
    expect(
      fixture.nativeElement.querySelector(
        'button[aria-label="Show the next dead-letter page for Failed"]',
      ),
    ).toBeNull();
  });

  it('omits optional preview metadata when it is not present', async () => {
    const { fixture } = await setupAndLoad({
      previewPages: {
        'default.XQ': {
          1: [
            {
              queue_name: 'default',
              routing_key: 'default.XQ',
              actor_name: null,
              message_id: 'preview-minimal',
              job_id: null,
              job_type: null,
              retries: null,
              enqueued_at: null,
              death_reason: null,
              source_queue: null,
              payload_preview: '{"args": [], "kwargs": {}}',
              error_summary: null,
            },
          ],
        },
      },
    });

    const previewCardText = fixture.nativeElement.querySelector('.preview-card')?.textContent ?? '';

    expect(previewCardText).toContain('Routing key: default.XQ');
    expect(previewCardText).not.toContain('From default');
    expect(previewCardText).not.toContain('Retries:');
    expect(previewCardText).not.toContain('Death reason:');
    expect(fixture.nativeElement.querySelector('.preview-error')).toBeNull();
  });

  it('shows an empty preview state when a follow-up page load fails', async () => {
    const { fixture, mockService } = await setupAndLoad();

    mockService.getJobQueuePreview.mockImplementation(
      (queueName: string, _size?: number, page = 1) =>
        page === 1 ? Promise.resolve(PAGE_ONE_PREVIEWS) : Promise.reject(new Error('page fail')),
    );

    const nextButton = fixture.nativeElement.querySelector(
      'button[aria-label="Show the next dead-letter page for Failed"]',
    ) as HTMLButtonElement;
    nextButton.click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No preview messages available right now.');
  });

  it('falls back to generic preview titles when preview metadata is missing', () => {
    const { fixture } = setup();
    const component = fixture.componentInstance as unknown as {
      deadLetterPreviewTitle: (preview: QueueMessagePreview) => string;
      deadLetterPreviewLabel: (preview: QueueMessagePreview) => string;
    };

    const preview: QueueMessagePreview = {
      queue_name: 'default',
      routing_key: 'default.XQ',
      actor_name: null,
      message_id: null,
      job_id: null,
      job_type: null,
      retries: null,
      enqueued_at: null,
      death_reason: null,
      source_queue: null,
      payload_preview: '{"args": [], "kwargs": {}}',
      error_summary: null,
    };

    expect(component.deadLetterPreviewTitle(preview)).toBe('Queued message');
    expect(component.deadLetterPreviewLabel(preview)).toBe('Preview payload for Queued message');
    expect(
      component.deadLetterPreviewTitle({
        ...preview,
        job_type: 'iyow_feedback',
      }),
    ).toBe('iyow_feedback');
    expect(
      component.deadLetterPreviewTitle({
        ...preview,
        actor_name: 'job_queue',
      }),
    ).toBe('job_queue');
  });

  it('groups workers by channel and exposes subscriptions in the expanded details', async () => {
    const { fixture } = await setupAndLoad();
    const groups = fixture.nativeElement.querySelectorAll('.worker-group');

    expect(groups.length).toBe(2);
    expect(fixture.nativeElement.textContent).toContain('Worker');
    expect(fixture.nativeElement.textContent).not.toContain('Default worker');
    expect(fixture.nativeElement.textContent).toContain('Jobs + Retry Queue');
    expect(fixture.nativeElement.textContent).toContain('2 queue subscriptions');
    expect(fixture.nativeElement.textContent).toContain('Fanout exchange bridge');
    expect(fixture.nativeElement.textContent).toContain('Queue: default.DQ');
    expect(fixture.nativeElement.textContent).not.toContain('ch-default');
  });

  it('purges from the DLQ clear-all button after confirmation', async () => {
    const { fixture, mockService } = await setupAndLoad({ dialogConfirmed: true });
    const component = fixture.componentInstance as unknown as {
      confirmPurge: (queue: QueueInfo) => Promise<void>;
      dialog: {
        open: () => { afterClosed: () => { toPromise: () => Promise<boolean> } };
      };
    };
    component.dialog = {
      open: vi.fn().mockReturnValue({
        afterClosed: () => ({ toPromise: () => Promise.resolve(true) }),
      }),
    };

    await component.confirmPurge(STUB_QUEUES[2]);
    await new Promise((resolve) => setTimeout(resolve, 0));
    fixture.detectChanges();

    expect(mockService.purgeQueue).toHaveBeenCalledWith('default.XQ');
    expect(mockService.getJobsQueues).toHaveBeenCalledTimes(2);
  });

  it('does not purge when the confirmation dialog is cancelled', async () => {
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

    await component.confirmPurge(STUB_QUEUES[2]);
    await new Promise((resolve) => setTimeout(resolve, 0));
    fixture.detectChanges();

    expect(mockService.purgeQueue).not.toHaveBeenCalled();
  });

  it('shows error messaging when loading fails', async () => {
    const { fixture } = await setupAndLoad({ error: true });

    expect(fixture.nativeElement.querySelector('.error-message')?.textContent).toContain(
      'Failed to load job control data.',
    );
  });

  it('toggles auto-refresh and clears the interval on destroy', async () => {
    vi.useFakeTimers();
    const clearIntervalSpy = vi.spyOn(window, 'clearInterval');

    try {
      const { fixture, mockService } = setup();
      await vi.advanceTimersByTimeAsync(0);
      await Promise.resolve();
      fixture.detectChanges();

      const toggle = fixture.nativeElement.querySelector('mat-slide-toggle') as HTMLElement;
      toggle.dispatchEvent(new Event('change'));
      fixture.detectChanges();

      toggle.dispatchEvent(new Event('change'));
      fixture.detectChanges();

      await vi.advanceTimersByTimeAsync(10_000);
      await Promise.resolve();
      fixture.detectChanges();

      expect(mockService.getJobsQueues).toHaveBeenCalledTimes(2);

      fixture.destroy();
      expect(clearIntervalSpy).toHaveBeenCalled();
    } finally {
      clearIntervalSpy.mockRestore();
      vi.useRealTimers();
    }
  });

  it('allows destroy before auto-refresh starts', () => {
    const mockService = {
      getJobsOverview: vi.fn().mockResolvedValue(STUB_OVERVIEW),
      getJobsQueues: vi.fn().mockResolvedValue(STUB_QUEUES),
      getJobsWorkers: vi.fn().mockResolvedValue(STUB_WORKERS),
      getJobQueuePreview: vi.fn().mockResolvedValue(PAGE_ONE_PREVIEWS),
      purgeQueue: vi.fn().mockResolvedValue(undefined),
    };
    const mockDialog = {
      open: vi.fn().mockReturnValue({
        afterClosed: () => ({ toPromise: () => Promise.resolve(false) }),
      }),
    };
    const mockTitle = {
      setTitle: vi.fn(),
      title: vi.fn(),
    };

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [
        { provide: OperationsService, useValue: mockService },
        { provide: MatDialog, useValue: mockDialog },
        { provide: PageTitleService, useValue: mockTitle },
      ],
    });

    const fixture = TestBed.createComponent(JobControlComponent);

    expect(() => fixture.componentInstance.ngOnDestroy()).not.toThrow();
  });

  it('shows empty states when there are no queues or workers', async () => {
    const { fixture } = await setupAndLoad({ queues: [], workers: [] });

    const emptyStates = Array.from(
      fixture.nativeElement.querySelectorAll('.empty-state'),
      (node: Element) => node.textContent?.trim(),
    );

    expect(emptyStates).toContain('No queues found.');
    expect(emptyStates).toContain('No dead-letter queues are configured right now.');
    expect(emptyStates).toContain('No active workers.');
  });
});
