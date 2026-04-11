/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import {
  Component,
  ChangeDetectionStrategy,
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
  private dialog = inject(MatDialog);
  private refreshInterval: ReturnType<typeof setInterval> | null = null;

  protected readonly overview = signal<JobControlOverview | null>(null);
  protected readonly queues = signal<QueueInfo[]>([]);
  protected readonly workers = signal<WorkerInfo[]>([]);
  protected readonly failures = signal<JobFailures | null>(null);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');
  protected readonly autoRefresh = signal(true);

  protected readonly queueColumns = [
    'name',
    'ready',
    'unacked',
    'consumers',
    'ack_rate',
    'actions',
  ];
  protected readonly workerColumns = ['consumer_tag', 'queue', 'channel_details', 'prefetch_count'];

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
