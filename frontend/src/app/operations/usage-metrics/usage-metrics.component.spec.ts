/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { UsageMetricsComponent } from './usage-metrics.component';
import { OperationsService } from '../operations.service';
import { UsageMetrics } from '../../api/models';
import { PageTitleService } from '../../page-title.service';

const STUB_METRICS: UsageMetrics = {
  month_label: 'April 2026',
  active_users: 42,
  active_courses: 5,
  submissions: 128,
  jobs_run: 64,
};

function setup(opts: { metrics?: UsageMetrics; error?: boolean } = {}) {
  const mockTitle = {
    setTitle: vi.fn(),
    title: vi.fn(),
  };
  const mockService = {
    getUsageMetrics: opts.error
      ? vi.fn().mockRejectedValue(new Error('fail'))
      : vi.fn().mockResolvedValue(opts.metrics ?? STUB_METRICS),
  };

  TestBed.configureTestingModule({
    imports: [NoopAnimationsModule],
    providers: [
      { provide: OperationsService, useValue: mockService },
      { provide: PageTitleService, useValue: mockTitle },
    ],
  });

  const fixture = TestBed.createComponent(UsageMetricsComponent);
  fixture.detectChanges();

  return { fixture, mockService, mockTitle };
}

describe('UsageMetricsComponent', () => {
  it('should create the component', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should set the page title', () => {
    const { mockTitle } = setup();

    expect(mockTitle.setTitle).toHaveBeenCalledWith('Usage Metrics');
  });

  it('should display four metric cards after loading', async () => {
    const { fixture } = setup();
    await fixture.whenStable();
    fixture.detectChanges();

    const cards = fixture.nativeElement.querySelectorAll('.metric-card');
    expect(cards.length).toBe(4);
  });

  it('should display the month label', async () => {
    const { fixture } = setup();
    await fixture.whenStable();
    fixture.detectChanges();

    const period = fixture.nativeElement.querySelector('.metrics-period');
    expect(period.textContent).toContain('April 2026');
  });

  it('should display correct metric values', async () => {
    const { fixture } = setup();
    await fixture.whenStable();
    fixture.detectChanges();

    const values = fixture.nativeElement.querySelectorAll('.metric-value');
    expect(values[0].textContent.trim()).toBe('42');
    expect(values[1].textContent.trim()).toBe('5');
    expect(values[2].textContent.trim()).toBe('128');
    expect(values[3].textContent.trim()).toBe('64');
  });

  it('should display correct metric labels', async () => {
    const { fixture } = setup();
    await fixture.whenStable();
    fixture.detectChanges();

    const labels = fixture.nativeElement.querySelectorAll('.metric-label');
    expect(labels[0].textContent).toContain('Active Users');
    expect(labels[1].textContent).toContain('Active Courses');
    expect(labels[2].textContent).toContain('Submissions');
    expect(labels[3].textContent).toContain('Jobs Run');
  });

  it('should show error message on load failure', async () => {
    const { fixture } = setup({ error: true });
    await fixture.whenStable();
    fixture.detectChanges();

    const error = fixture.nativeElement.querySelector('.error-message');
    expect(error).toBeTruthy();
    expect(error.textContent).toContain('Failed to load usage metrics');
  });

  it('should show loading spinner initially', () => {
    const mockService = {
      getUsageMetrics: vi.fn().mockReturnValue(new Promise(() => {})),
    };

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [{ provide: OperationsService, useValue: mockService }],
    });

    const fixture = TestBed.createComponent(UsageMetricsComponent);
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector('mat-spinner');
    expect(spinner).toBeTruthy();
  });
});
