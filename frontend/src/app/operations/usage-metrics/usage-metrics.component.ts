/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, signal, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { UsageMetrics } from '../../api/models';
import { OperationsService } from '../operations.service';

@Component({
  selector: 'app-usage-metrics',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCardModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './usage-metrics.component.html',
  styleUrl: './usage-metrics.component.scss',
})
export class UsageMetricsComponent implements OnInit {
  private operationsService = inject(OperationsService);

  protected readonly metrics = signal<UsageMetrics | null>(null);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');

  async ngOnInit(): Promise<void> {
    await this.loadMetrics();
  }

  private async loadMetrics(): Promise<void> {
    this.loading.set(true);
    this.errorMessage.set('');
    try {
      const data = await this.operationsService.getUsageMetrics();
      this.metrics.set(data);
    } catch {
      this.errorMessage.set('Failed to load usage metrics.');
    } finally {
      this.loading.set(false);
    }
  }
}
