/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import {
  Component,
  ChangeDetectionStrategy,
  computed,
  inject,
  signal,
  OnInit,
  OnDestroy,
} from '@angular/core';
import { DatePipe, DecimalPipe, KeyValuePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { JobControlOverview, QueueInfo, WorkerInfo, JobFailures } from '../../api/models';
import { PageTitleService } from '../../page-title.service';
import { OperationsService } from '../operations.service';
import { ConfirmPurgeDialogComponent } from './confirm-purge-dialog.component';

@Component({
  selector: 'app-job-control',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    DecimalPipe,
    KeyValuePipe,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTableModule,
    MatButtonModule,
    MatSlideToggleModule,
    MatDialogModule,
  ],
  templateUrl: './job-control.component.html',
  styleUrl: './job-control.component.scss',
})
export class JobControlComponent implements OnInit, OnDestroy {
  private operationsService = inject(OperationsService);
  private pageTitle = inject(PageTitleService);
  private dialog = inject(MatDialog);
  private refreshInterval: ReturnType<typeof setInterval> | null = null;

  protected readonly overview = signal<JobControlOverview | null>(null);
  protected readonly queues = signal<QueueInfo[]>([]);
  protected readonly workers = signal<WorkerInfo[]>([]);
  protected readonly failures = signal<JobFailures | null>(null);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');
  protected readonly autoRefresh = signal(true);
  protected readonly retryQueues = computed(() => this.queues().filter((queue) => queue.is_retry));

  protected readonly queueColumns = [
    'name',
    'ready',
    'unacked',
    'consumers',
    'ack_rate',
    'actions',
  ];
  protected readonly workerColumns = ['consumer_tag', 'queue', 'channel_details', 'prefetch_count'];

  constructor() {
    this.pageTitle.setTitle('Job Control');
  }

  async ngOnInit(): Promise<void> {
    await this.loadAll();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  protected toggleAutoRefresh(): void {
    this.autoRefresh.update((v) => !v);
    if (this.autoRefresh()) {
      this.startAutoRefresh();
    } else {
      this.stopAutoRefresh();
    }
  }

  protected async confirmPurge(queue: QueueInfo): Promise<void> {
    const dialogRef = this.dialog.open(ConfirmPurgeDialogComponent, {
      data: { queueName: queue.name },
    });

    const confirmed = await dialogRef.afterClosed().toPromise();
    if (confirmed) {
      await this.operationsService.purgeQueue(queue.name);
      await this.loadAll();
    }
  }

  protected async loadAll(): Promise<void> {
    this.loading.set(true);
    this.errorMessage.set('');
    try {
      const [overviewData, queuesData, workersData, failuresData] = await Promise.all([
        this.operationsService.getJobsOverview(),
        this.operationsService.getJobsQueues(),
        this.operationsService.getJobsWorkers(),
        this.operationsService.getJobsFailures(),
      ]);
      this.overview.set(overviewData);
      this.queues.set(queuesData);
      this.workers.set(workersData);
      this.failures.set(failuresData);
    } catch {
      this.errorMessage.set('Failed to load job control data.');
    } finally {
      this.loading.set(false);
    }
  }

  protected queueDisplayName(queue: Pick<QueueInfo, 'name' | 'is_dlq' | 'is_retry'>): string {
    return this.queueDisplayNameFromName(queue.name);
  }

  protected queueDisplayNameFromName(queueName: string): string {
    const baseName = this.humanizeQueueBaseName(queueName);
    if (queueName.endsWith('.DQ')) {
      return `${baseName} dead-letter queue`;
    }
    if (queueName.endsWith('.XQ')) {
      return `${baseName} retry delay queue`;
    }
    return `${baseName} work queue`;
  }

  protected queueRoleSummary(queue: Pick<QueueInfo, 'is_dlq' | 'is_retry'>): string {
    if (queue.is_dlq) {
      return 'Keeps messages that could not be completed and need operator attention.';
    }
    if (queue.is_retry) {
      return 'Temporarily parks messages between retry attempts before routing them back to work.';
    }
    return 'Primary queue that workers actively pull from.';
  }

  protected purgeQueueLabel(queue: Pick<QueueInfo, 'name' | 'is_dlq' | 'is_retry'>): string {
    return `Purge ${this.queueDisplayName(queue)} (${queue.name})`;
  }

  protected queueStatusLabel(queue: Pick<QueueInfo, 'is_dlq' | 'is_retry'>): string {
    if (queue.is_dlq) {
      return 'Needs review';
    }
    if (queue.is_retry) {
      return 'Waiting to retry';
    }
    return 'Active';
  }

  protected formatRetryDelay(messageTtlMs: number | null | undefined): string {
    if (messageTtlMs == null || messageTtlMs <= 0) {
      return 'No delay configured';
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

  protected retryReturnDestination(
    queue: Pick<QueueInfo, 'dead_letter_exchange' | 'dead_letter_routing_key'>,
  ): string {
    if (queue.dead_letter_routing_key) {
      return queue.dead_letter_routing_key;
    }
    if (queue.dead_letter_exchange === '') {
      return 'the default exchange';
    }
    if (queue.dead_letter_exchange) {
      return queue.dead_letter_exchange;
    }
    return 'no return route configured';
  }

  protected retryQueueInsight(
    queue: Pick<
      QueueInfo,
      'ready' | 'message_ttl_ms' | 'dead_letter_exchange' | 'dead_letter_routing_key'
    >,
  ): string {
    if (queue.ready === 0) {
      return 'No messages are waiting in this retry queue right now.';
    }

    const delay = this.formatRetryDelay(queue.message_ttl_ms);
    if (queue.message_ttl_ms == null || queue.message_ttl_ms <= 0) {
      return 'Messages are waiting here, but no retry delay is configured, so they will not move on their own.';
    }

    if (queue.dead_letter_exchange == null && queue.dead_letter_routing_key == null) {
      return `Messages are waiting out a ${delay} retry delay, but this queue does not declare where expired messages should go next.`;
    }

    const messageLabel = queue.ready === 1 ? 'message is' : 'messages are';
    return `${queue.ready} ${messageLabel} waiting about ${delay} before RabbitMQ routes ${queue.ready === 1 ? 'it' : 'them'} back to ${this.retryReturnDestination(queue)}.`;
  }

  protected retryQueueNeedsAttention(
    queue: Pick<
      QueueInfo,
      'ready' | 'message_ttl_ms' | 'dead_letter_exchange' | 'dead_letter_routing_key'
    >,
  ): boolean {
    return (
      queue.ready > 0 &&
      (queue.message_ttl_ms == null ||
        queue.message_ttl_ms <= 0 ||
        (queue.dead_letter_exchange == null && queue.dead_letter_routing_key == null))
    );
  }

  private humanizeQueueBaseName(queueName: string): string {
    const baseName = queueName.replace(/\.(DQ|XQ)$/, '');
    return baseName
      .split(/[._-]+/)
      .filter((part) => part.length > 0)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
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
