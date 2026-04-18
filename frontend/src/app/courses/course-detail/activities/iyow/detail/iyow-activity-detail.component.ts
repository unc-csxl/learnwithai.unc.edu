/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  computed,
  OnDestroy,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { PageTitleService } from '../../../../../page-title.service';
import { JobUpdateService } from '../../../../../job-update.service';
import { LayoutNavigationService } from '../../../../../layout/layout-navigation.service';
import { ActivityService } from '../../activity.service';
import { buildActivityContextNav } from '../../activity-nav';
import { activitySubmissionRouteParts } from '../../activity-types';
import { IyowActivity, IyowStudentSubmissionRow } from '../../../../../api/models';

const DEBOUNCE_MS = 300;
const MIN_SEARCH_LENGTH = 3;

/** Instructor view showing IYOW activity info and a sortable table of student submissions. */
@Component({
  selector: 'app-iyow-activity-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    DatePipe,
    MatTableModule,
    MatSortModule,
    MatCardModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
  ],
  templateUrl: './iyow-activity-detail.component.html',
})
export class IyowActivityDetail implements OnDestroy {
  private activityService = inject(ActivityService);
  private route = inject(ActivatedRoute);
  private titleService = inject(PageTitleService);
  private jobUpdateService = inject(JobUpdateService);
  private layoutNavigation = inject(LayoutNavigationService);
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;

  protected readonly courseId: number;
  protected readonly activityId: number;
  protected readonly dateTimeFormat = 'MMM d, y, h:mm a';
  protected readonly activity = signal<IyowActivity | null>(null);
  protected readonly allRows = signal<IyowStudentSubmissionRow[]>([]);
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly searchQuery = signal('');
  protected readonly sortActive = signal('family_name');
  protected readonly sortDirection = signal<'asc' | 'desc' | ''>('asc');

  protected readonly displayedColumns = ['student_name', 'submitted_at', 'status'];

  protected readonly filteredRows = computed(() => {
    const query = this.searchQuery().toLowerCase();
    let rows = this.allRows();
    if (query) {
      rows = rows.filter((r) => {
        const name = `${r.given_name ?? ''} ${r.family_name ?? ''}`.toLowerCase();
        return name.includes(query);
      });
    }
    return this.sortRows(rows, this.sortActive(), this.sortDirection());
  });

  protected readonly submittedCount = computed(
    () => this.allRows().filter((r) => r.submission !== null).length,
  );

  protected readonly totalCount = computed(() => this.allRows().length);

  constructor() {
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.activityId = Number(this.route.snapshot.paramMap.get('activityId'));
    this.jobUpdateService.subscribe(this.courseId);
    this.loadData();
  }

  ngOnDestroy(): void {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
    }
    this.jobUpdateService.unsubscribe(this.courseId);
  }

  protected onSearchInput(value: string): void {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      const query = value.length >= MIN_SEARCH_LENGTH ? value : '';
      if (query !== this.searchQuery()) {
        this.searchQuery.set(query);
      }
    }, DEBOUNCE_MS);
  }

  protected onSortChange(sort: Sort): void {
    this.sortActive.set(sort.active);
    this.sortDirection.set(sort.direction);
  }

  protected statusLabel(row: IyowStudentSubmissionRow): string {
    if (!row.submission) return 'Not submitted';
    const status = row.submission.job?.status;
    if (status === 'pending' || status === 'processing') return 'Processing';
    if (row.submission.feedback) return 'Graded';
    return 'Submitted';
  }

  protected submissionLink(studentPid: number): Array<string | number> {
    const activityType = this.activity()?.type ?? '';
    return [
      '/courses',
      this.courseId,
      'activities',
      ...activitySubmissionRouteParts(activityType, this.activityId, studentPid),
    ];
  }

  private async loadData(): Promise<void> {
    try {
      const [activity, roster] = await Promise.all([
        this.activityService.getIyow(this.courseId, this.activityId),
        this.activityService.listIyowSubmissionsRoster(this.courseId, this.activityId),
      ]);
      this.activity.set(activity);
      this.titleService.setTitle(activity.title);
      this.allRows.set(roster);
      this.layoutNavigation.setContextSection(
        buildActivityContextNav({
          courseId: this.courseId,
          activityId: this.activityId,
          activityType: activity.type,
          role: 'staff',
        }),
      );
    } catch {
      this.errorMessage.set('Failed to load activity details.');
      this.layoutNavigation.clearContext();
    } finally {
      this.loaded.set(true);
    }
  }

  private sortRows(
    rows: IyowStudentSubmissionRow[],
    active: string,
    direction: 'asc' | 'desc' | '',
  ): IyowStudentSubmissionRow[] {
    if (!direction) return rows;
    const sorted = [...rows];
    const dir = direction === 'asc' ? 1 : -1;
    sorted.sort((a, b) => {
      let cmp = 0;
      switch (active) {
        case 'student_name':
        case 'family_name': {
          const nameA = `${a.family_name ?? ''} ${a.given_name ?? ''}`.toLowerCase();
          const nameB = `${b.family_name ?? ''} ${b.given_name ?? ''}`.toLowerCase();
          cmp = nameA.localeCompare(nameB);
          break;
        }
        case 'submitted_at': {
          const tA = a.submission?.submitted_at ?? '';
          const tB = b.submission?.submitted_at ?? '';
          cmp = tA.localeCompare(tB);
          break;
        }
        case 'status': {
          cmp = this.statusLabel(a).localeCompare(this.statusLabel(b));
          break;
        }
      }
      return cmp * dir;
    });
    return sorted;
  }
}
