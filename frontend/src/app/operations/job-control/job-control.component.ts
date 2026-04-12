/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  OnDestroy,
  OnInit,
  signal,
} from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { QueueInfo, QueueMessagePreview, WorkerInfo } from '../../api/models';
import { PageTitleService } from '../../page-title.service';
import { OperationsService } from '../operations.service';
import { ConfirmPurgeDialogComponent } from './confirm-purge-dialog.component';

type QueueDisplayMeta = Pick<QueueInfo, 'name' | 'is_dlq' | 'is_retry' | 'message_ttl_ms'>;
type WorkerSubscription = {
  consumerTag: string;
  queueName: string;
  queueDisplayName: string;
  prefetchCount: number;
};
type WorkerGroup = {
  id: string;
  displayName: string;
  roleLabel: string;
  subscriptionSummary: string;
  subscriptions: WorkerSubscription[];
};

@Component({
  selector: 'app-job-control',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    DecimalPipe,
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSlideToggleModule,
    MatTableModule,
    MatTooltipModule,
  ],
  templateUrl: './job-control.component.html',
  styleUrl: './job-control.component.scss',
})
export class JobControlComponent implements OnInit, OnDestroy {
  private readonly operationsService = inject(OperationsService);
  private readonly pageTitle = inject(PageTitleService);
  private readonly dialog = inject(MatDialog);
  private refreshInterval: ReturnType<typeof setInterval> | null = null;

  protected readonly queues = signal<QueueInfo[]>([]);
  protected readonly workers = signal<WorkerInfo[]>([]);
  protected readonly deadLetterPreviews = signal<Record<string, QueueMessagePreview[]>>({});
  protected readonly deadLetterPreviewPages = signal<Record<string, number>>({});
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');
  protected readonly autoRefresh = signal(true);
  protected readonly deadLetterPreviewPageSize = 5;

  protected readonly sortedQueues = computed(() =>
    [...this.queues()].sort((left, right) => this.compareQueues(left, right)),
  );
  protected readonly deadLetterQueues = computed(() =>
    this.queues().filter((queue) => queue.is_dlq),
  );
  protected readonly workerGroups = computed(() => this.buildWorkerGroups(this.workers()));

  protected readonly queueColumns = [
    'queue',
    'ready',
    'unacked',
    'consumers',
    'ack_rate',
    'actions',
  ];

  constructor() {
    this.pageTitle.setTitle('Job Queue Control');
  }

  async ngOnInit(): Promise<void> {
    await this.loadAll();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  protected toggleAutoRefresh(): void {
    this.autoRefresh.update((value) => !value);
    if (this.autoRefresh()) {
      this.startAutoRefresh();
      return;
    }
    this.stopAutoRefresh();
  }

  protected async confirmPurge(queue: QueueInfo): Promise<void> {
    const dialogRef = this.dialog.open(ConfirmPurgeDialogComponent, {
      data: { queueName: queue.name },
    });

    const confirmed = await dialogRef.afterClosed().toPromise();
    if (!confirmed) {
      return;
    }

    await this.operationsService.purgeQueue(queue.name);
    await this.loadAll();
  }

  protected async loadAll(): Promise<void> {
    this.loading.set(true);
    this.errorMessage.set('');

    try {
      const [queuesData, workersData] = await Promise.all([
        this.operationsService.getJobsQueues(),
        this.operationsService.getJobsWorkers(),
      ]);

      const previewPages = this.syncDeadLetterPreviewPages(queuesData);
      const deadLetterPreviews = await this.loadDeadLetterPreviews(queuesData, previewPages);

      this.queues.set(queuesData);
      this.workers.set(workersData);
      this.deadLetterPreviews.set(deadLetterPreviews);
    } catch {
      this.errorMessage.set('Failed to load job control data.');
    } finally {
      this.loading.set(false);
    }
  }

  protected queueDisplayName(queue: Pick<QueueInfo, 'name'>): string {
    return this.queueDisplayNameFromName(queue.name);
  }

  protected queueDisplayNameFromName(queueName: string): string {
    if (queueName.startsWith('amq.gen-')) {
      return 'Notifications';
    }

    const baseName = this.humanizeQueueBaseName(queueName);
    if (queueName.endsWith('.DQ')) {
      return baseName === 'Default' ? 'Retry Queue' : `${baseName} Retry Queue`;
    }
    if (queueName.endsWith('.XQ')) {
      return baseName === 'Default' ? 'Failed' : `${baseName} Failed`;
    }
    return baseName === 'Default' ? 'Jobs' : `${baseName} Jobs`;
  }

  protected queueRoleSummary(queue: QueueDisplayMeta): string {
    if (queue.name.startsWith('amq.gen-')) {
      return 'Exclusive temporary queue created by the API WebSocket bridge so the fanout exchange can broadcast live job updates to connected operator sessions.';
    }
    if (queue.is_dlq) {
      const retention = this.formatDuration(queue.message_ttl_ms, 'no automatic expiry');
      return `Retains rejected messages for operator review. RabbitMQ keeps them here for about ${retention} before expiry and does not route them back automatically.`;
    }
    if (queue.is_retry) {
      return 'Holds scheduled jobs until their ETA arrives, then workers move them back onto the jobs queue.';
    }
    return 'Primary jobs queue that workers actively pull from.';
  }

  protected queueBadgeLabel(queue: Pick<QueueInfo, 'name' | 'is_dlq' | 'is_retry'>): string {
    if (queue.name.startsWith('amq.gen-')) {
      return 'Fanout Exchange';
    }
    if (queue.is_dlq) {
      return 'Dead Letter';
    }
    if (queue.is_retry) {
      return 'Delay';
    }
    return 'Work';
  }

  protected queueBadgeClass(queue: Pick<QueueInfo, 'name' | 'is_dlq' | 'is_retry'>): string {
    if (queue.name.startsWith('amq.gen-')) {
      return 'badge-live';
    }
    if (queue.is_dlq) {
      return 'badge-dlq';
    }
    if (queue.is_retry) {
      return 'badge-delayed';
    }
    return 'badge-work';
  }

  protected queueStatusLabel(queue: Pick<QueueInfo, 'name' | 'is_dlq' | 'is_retry'>): string {
    if (queue.name.startsWith('amq.gen-')) {
      return 'Notifications';
    }
    if (queue.is_dlq) {
      return 'Failed';
    }
    if (queue.is_retry) {
      return 'Retry Queue';
    }
    return 'Jobs';
  }

  protected queueTooltip(queue: QueueDisplayMeta): string {
    return `${this.queueRoleSummary(queue)}\nRabbitMQ name: ${queue.name}`;
  }

  protected queueDetailsLabel(queue: Pick<QueueInfo, 'name'>): string {
    return `Show details for ${this.queueDisplayName(queue)} (${queue.name})`;
  }

  protected purgeQueueLabel(queue: Pick<QueueInfo, 'name'>): string {
    return `Purge ${this.queueDisplayName(queue)} (${queue.name})`;
  }

  protected clearAllDeadLettersLabel(queue: Pick<QueueInfo, 'name'>): string {
    return `Clear all retained messages from ${this.queueDisplayName(queue)} (${queue.name})`;
  }

  protected formatDuration(
    messageTtlMs: number | null | undefined,
    missingLabel = 'No delay configured',
  ): string {
    if (messageTtlMs == null || messageTtlMs <= 0) {
      return missingLabel;
    }
    if (messageTtlMs % 3_600_000 === 0) {
      return `${messageTtlMs / 3_600_000}h`;
    }
    if (messageTtlMs % 60_000 === 0) {
      return `${messageTtlMs / 60_000}m`;
    }
    if (messageTtlMs % 1_000 === 0) {
      return `${messageTtlMs / 1_000}s`;
    }
    return `${messageTtlMs} ms`;
  }

  protected deadLetterQueueNeedsAttention(queue: Pick<QueueInfo, 'ready'>): boolean {
    return queue.ready > 0;
  }

  protected queueShowsUnacked(queue: Pick<QueueInfo, 'name' | 'is_dlq'>): boolean {
    return !queue.is_dlq && !queue.name.startsWith('amq.gen-');
  }

  protected queueShowsConsumers(queue: Pick<QueueInfo, 'is_dlq'>): boolean {
    return !queue.is_dlq;
  }

  protected queueShowsAckRate(queue: Pick<QueueInfo, 'name' | 'is_dlq' | 'is_retry'>): boolean {
    return !queue.is_dlq && !queue.is_retry && !queue.name.startsWith('amq.gen-');
  }

  protected queueReadyClass(queue: Pick<QueueInfo, 'is_dlq' | 'ready'>): string {
    return queue.is_dlq && queue.ready > 0 ? 'metric-attention' : '';
  }

  protected canPurgeQueueFromTable(queue: Pick<QueueInfo, 'ready' | 'is_dlq'>): boolean {
    return queue.ready > 0 && !queue.is_dlq;
  }

  protected deadLetterPreviewFor(queueName: string): QueueMessagePreview[] {
    return this.deadLetterPreviews()[queueName] ?? [];
  }

  protected deadLetterPreviewTitle(preview: QueueMessagePreview): string {
    if (preview.job_type && preview.job_id != null) {
      return `${preview.job_type} #${preview.job_id}`;
    }
    if (preview.job_type) {
      return preview.job_type;
    }
    if (preview.actor_name) {
      return preview.actor_name;
    }
    return 'Queued message';
  }

  protected deadLetterPreviewLabel(preview: QueueMessagePreview): string {
    return `Preview payload for ${this.deadLetterPreviewTitle(preview)}`;
  }

  protected deadLetterPreviewPage(queueName: string): number {
    return this.deadLetterPreviewPages()[queueName] ?? 1;
  }

  protected deadLetterPreviewPageCount(queue: Pick<QueueInfo, 'ready'>): number {
    return Math.max(1, Math.ceil(queue.ready / this.deadLetterPreviewPageSize));
  }

  protected deadLetterPreviewSummary(queue: Pick<QueueInfo, 'name' | 'ready'>): string {
    const page = this.deadLetterPreviewPage(queue.name);
    const totalPages = this.deadLetterPreviewPageCount(queue);
    const previews = this.deadLetterPreviewFor(queue.name);
    if (queue.ready === 0) {
      return 'Page 1 of 1';
    }
    if (previews.length === 0) {
      return `Page ${page} of ${totalPages}`;
    }

    const start = (page - 1) * this.deadLetterPreviewPageSize + 1;
    const end = start + previews.length - 1;
    return `Page ${page} of ${totalPages} · Showing ${start}-${end} of ${queue.ready}`;
  }

  protected canGoToPreviousDeadLetterPage(queue: Pick<QueueInfo, 'name'>): boolean {
    return this.deadLetterPreviewPage(queue.name) > 1;
  }

  protected canGoToNextDeadLetterPage(queue: Pick<QueueInfo, 'name' | 'ready'>): boolean {
    return this.deadLetterPreviewPage(queue.name) < this.deadLetterPreviewPageCount(queue);
  }

  protected previousDeadLetterPageLabel(queue: Pick<QueueInfo, 'name'>): string {
    return `Show the previous dead-letter page for ${this.queueDisplayName(queue)}`;
  }

  protected nextDeadLetterPageLabel(queue: Pick<QueueInfo, 'name'>): string {
    return `Show the next dead-letter page for ${this.queueDisplayName(queue)}`;
  }

  protected async goToPreviousDeadLetterPage(queue: QueueInfo): Promise<void> {
    if (!this.canGoToPreviousDeadLetterPage(queue)) {
      return;
    }
    await this.loadDeadLetterPreview(queue, this.deadLetterPreviewPage(queue.name) - 1);
  }

  protected async goToNextDeadLetterPage(queue: QueueInfo): Promise<void> {
    if (!this.canGoToNextDeadLetterPage(queue)) {
      return;
    }
    await this.loadDeadLetterPreview(queue, this.deadLetterPreviewPage(queue.name) + 1);
  }

  protected workerGroupToggleLabel(group: WorkerGroup): string {
    return `Show worker subscriptions for ${group.displayName}`;
  }

  private humanizeQueueBaseName(queueName: string): string {
    const baseName = queueName.replace(/\.(DQ|XQ)$/, '');
    return baseName
      .split(/[._-]+/)
      .filter((part) => part.length > 0 && !part.startsWith('amq'))
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  private compareQueues(left: QueueInfo, right: QueueInfo): number {
    const rankDifference = this.queueSortRank(left) - this.queueSortRank(right);
    if (rankDifference !== 0) {
      return rankDifference;
    }

    const displayNameDifference = this.queueDisplayName(left).localeCompare(
      this.queueDisplayName(right),
    );
    if (displayNameDifference !== 0) {
      return displayNameDifference;
    }

    return left.name.localeCompare(right.name);
  }

  private queueSortRank(queue: Pick<QueueInfo, 'name' | 'is_dlq' | 'is_retry'>): number {
    if (queue.name.startsWith('amq.gen-')) {
      return 4;
    }
    if (queue.is_dlq) {
      return 3;
    }
    if (queue.is_retry) {
      return 2;
    }
    return 1;
  }

  private buildWorkerGroups(workers: WorkerInfo[]): WorkerGroup[] {
    const groupedWorkers = new Map<string, WorkerInfo[]>();

    for (const worker of workers) {
      const key = worker.channel_details || worker.consumer_tag;
      const entries = groupedWorkers.get(key) ?? [];
      entries.push(worker);
      groupedWorkers.set(key, entries);
    }

    return Array.from(groupedWorkers.entries())
      .map(([key, groupWorkers]) => ({
        id: key,
        displayName: this.workerGroupDisplayName(groupWorkers),
        roleLabel: this.workerGroupRoleLabel(groupWorkers),
        subscriptionSummary:
          groupWorkers.length > 1 ? `${groupWorkers.length} queue subscriptions` : '',
        subscriptions: groupWorkers
          .map((worker) => ({
            consumerTag: worker.consumer_tag,
            queueName: worker.queue,
            queueDisplayName: this.queueDisplayNameFromName(worker.queue),
            prefetchCount: worker.prefetch_count,
          }))
          .sort((left, right) => left.queueDisplayName.localeCompare(right.queueDisplayName)),
      }))
      .sort((left, right) => left.displayName.localeCompare(right.displayName));
  }

  private workerGroupDisplayName(workers: WorkerInfo[]): string {
    if (workers.some((worker) => worker.queue.startsWith('amq.gen-'))) {
      return 'Fanout exchange bridge';
    }

    const baseNames = Array.from(
      new Set(
        workers
          .map((worker) => this.humanizeQueueBaseName(worker.queue))
          .filter((baseName) => baseName.length > 0),
      ),
    );

    if (baseNames.length === 1) {
      return baseNames[0] === 'Default' ? 'Worker' : `${baseNames[0]} worker`;
    }

    return 'Worker';
  }

  private workerGroupRoleLabel(workers: WorkerInfo[]): string {
    const hasFanout = workers.some((worker) => worker.queue.startsWith('amq.gen-'));
    const hasJobs = workers.some(
      (worker) =>
        !worker.queue.startsWith('amq.gen-') &&
        !worker.queue.endsWith('.DQ') &&
        !worker.queue.endsWith('.XQ'),
    );
    const hasRetry = workers.some((worker) => worker.queue.endsWith('.DQ'));
    const hasFailed = workers.some((worker) => worker.queue.endsWith('.XQ'));

    if (hasFanout) {
      return 'Notifications';
    }
    if (hasJobs && hasRetry) {
      return 'Jobs + Retry Queue';
    }
    if (hasJobs) {
      return 'Jobs';
    }
    if (hasRetry) {
      return 'Retry Queue';
    }
    if (hasFailed) {
      return 'Failed';
    }
    return 'Worker';
  }

  private syncDeadLetterPreviewPages(queues: QueueInfo[]): Record<string, number> {
    const currentPages = this.deadLetterPreviewPages();
    const nextPages = Object.fromEntries(
      queues
        .filter((queue) => queue.is_dlq)
        .map((queue) => [
          queue.name,
          Math.min(currentPages[queue.name] ?? 1, this.deadLetterPreviewPageCount(queue)),
        ]),
    );

    this.deadLetterPreviewPages.set(nextPages);
    return nextPages;
  }

  private async loadDeadLetterPreviews(
    queues: QueueInfo[],
    pages: Record<string, number>,
  ): Promise<Record<string, QueueMessagePreview[]>> {
    const previewEntries = await Promise.all(
      queues
        .filter((queue) => queue.is_dlq)
        .map(async (queue) => {
          try {
            const previews = await this.operationsService.getJobQueuePreview(
              queue.name,
              this.deadLetterPreviewPageSize,
              pages[queue.name] ?? 1,
            );
            return [queue.name, previews] as const;
          } catch {
            return [queue.name, []] as const;
          }
        }),
    );

    return Object.fromEntries(previewEntries);
  }

  private async loadDeadLetterPreview(queue: QueueInfo, page: number): Promise<void> {
    const normalizedPage = Math.min(Math.max(1, page), this.deadLetterPreviewPageCount(queue));
    this.deadLetterPreviewPages.update((pages) => ({
      ...pages,
      [queue.name]: normalizedPage,
    }));

    try {
      const previews = await this.operationsService.getJobQueuePreview(
        queue.name,
        this.deadLetterPreviewPageSize,
        normalizedPage,
      );
      this.deadLetterPreviews.update((current) => ({
        ...current,
        [queue.name]: previews,
      }));
    } catch {
      this.deadLetterPreviews.update((current) => ({
        ...current,
        [queue.name]: [],
      }));
    }
  }

  private startAutoRefresh(): void {
    this.stopAutoRefresh();
    this.refreshInterval = setInterval(() => {
      this.loadAll();
    }, 10_000);
  }

  private stopAutoRefresh(): void {
    if (this.refreshInterval !== null) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }
}
