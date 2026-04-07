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
  OnDestroy,
  effect,
  Injector,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { DatePipe } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import {
  MatAutocompleteModule,
  MatAutocompleteSelectedEvent,
} from '@angular/material/autocomplete';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { PageTitleService } from '../../../../page-title.service';
import { JobUpdateService } from '../../../../job-update.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { ActivityService } from '../activity.service';
import { buildActivityContextNav } from '../activity-nav';
import { IyowActivity, IyowSubmission, StudentSubmissionRow } from '../../../../api/models';
import { MarkdownToHtmlPipe } from '../../../../shared/markdown-to-html.pipe';

/** Instructor view showing a single student's submission detail. */
@Component({
  selector: 'app-submission-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    ReactiveFormsModule,
    MatAutocompleteModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MarkdownToHtmlPipe,
  ],
  templateUrl: './submission-detail.component.html',
})
export class SubmissionDetail implements OnDestroy {
  private activityService = inject(ActivityService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private titleService = inject(PageTitleService);
  private jobUpdateService = inject(JobUpdateService);
  private layoutNavigation = inject(LayoutNavigationService);
  private injector = inject(Injector);
  private readonly routeParamMap = toSignal(this.route.paramMap, {
    initialValue: this.route.snapshot.paramMap,
  });
  private readonly watchedJobIds = new Set<number>();

  protected readonly courseId: number;
  protected readonly activityId: number;
  protected readonly dateTimeFormat = 'MMM d, y, h:mm a';
  protected readonly studentPid = computed(() => Number(this.routeParamMap().get('studentPid')));
  protected readonly activity = signal<IyowActivity | null>(null);
  protected readonly rosterRows = signal<StudentSubmissionRow[]>([]);
  protected readonly submissions = signal<IyowSubmission[]>([]);
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly selectedPriorSub = signal<IyowSubmission | null>(null);
  protected readonly jumpControl = new FormControl<string | StudentSubmissionRow>('', {
    nonNullable: true,
  });
  private readonly jumpValue = toSignal(this.jumpControl.valueChanges, {
    initialValue: this.jumpControl.value,
  });
  protected readonly submittedRows = computed(() =>
    [...this.rosterRows()]
      .filter((row) => row.submission !== null)
      .sort((left, right) =>
        this.studentSortValue(left).localeCompare(this.studentSortValue(right)),
      ),
  );
  protected readonly currentStudentRow = computed(
    () => this.rosterRows().find((row) => row.student_pid === this.studentPid()) ?? null,
  );
  protected readonly currentSubmission = computed(
    () =>
      this.currentStudentRow()?.submission ??
      this.submissions().find((submission) => submission.is_active) ??
      this.submissions()[0] ??
      null,
  );
  protected readonly currentSubmissionId = computed(() => this.currentSubmission()?.id ?? null);
  protected readonly currentSubmissionLabel = computed(() => {
    const submissionId = this.currentSubmissionId();
    return submissionId === null ? `Student ${this.studentPid()}` : `Submission ${submissionId}`;
  });
  protected readonly currentStudentName = computed(() =>
    this.formatStudentName(this.currentStudentRow()),
  );
  protected readonly currentStudentDescription = computed(() => {
    const studentName = this.currentStudentName();
    return studentName ? `Submitted by ${studentName}` : `Student PID ${this.studentPid()}`;
  });
  protected readonly currentSubmittedIndex = computed(() =>
    this.submittedRows().findIndex((row) => row.student_pid === this.studentPid()),
  );
  protected readonly currentSubmittedPosition = computed(() => {
    const index = this.currentSubmittedIndex();
    const total = this.submittedRows().length;
    if (index === -1 || total === 0) {
      return '';
    }

    return `Submitted student ${index + 1} of ${total}`;
  });
  protected readonly previousSubmissionRow = computed(() => {
    const index = this.currentSubmittedIndex();
    return index > 0 ? (this.submittedRows()[index - 1] ?? null) : null;
  });
  protected readonly nextSubmissionRow = computed(() => {
    const index = this.currentSubmittedIndex();
    const rows = this.submittedRows();
    return index !== -1 && index < rows.length - 1 ? (rows[index + 1] ?? null) : null;
  });
  protected readonly jumpOptions = computed(() => {
    const rawValue = this.jumpValue();
    const query = (typeof rawValue === 'string' ? rawValue : this.jumpDisplay(rawValue))
      .trim()
      .toLowerCase();

    return this.submittedRows().filter((row) => {
      if (row.student_pid === this.studentPid()) {
        return false;
      }

      if (query === '') {
        return true;
      }

      return this.matchesJumpQuery(row, query);
    });
  });

  constructor() {
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.activityId = Number(this.route.snapshot.paramMap.get('activityId'));
    this.jobUpdateService.subscribe(this.courseId);
    effect(
      () => {
        const studentPid = this.studentPid();
        if (!Number.isFinite(studentPid)) {
          return;
        }

        void this.loadData(studentPid);
      },
      { injector: this.injector },
    );
  }

  ngOnDestroy(): void {
    this.jobUpdateService.unsubscribe(this.courseId);
  }

  protected statusIcon(status: string | undefined): string {
    const icons: Record<string, string> = {
      pending: 'schedule',
      processing: 'sync',
      completed: 'check_circle',
      failed: 'error',
    };
    return (status && icons[status]) ?? 'help';
  }

  protected selectPriorSubmission(sub: IyowSubmission): void {
    this.selectedPriorSub.set(sub);
  }

  protected clearSelectedPrior(): void {
    this.selectedPriorSub.set(null);
  }

  protected jumpDisplay(value: string | StudentSubmissionRow | null): string {
    if (value === null || value === '') {
      return '';
    }

    if (typeof value === 'string') {
      return value;
    }

    return this.jumpOptionLabel(value);
  }

  protected async onJumpSelection(event: MatAutocompleteSelectedEvent): Promise<void> {
    const targetRow = event.option.value as StudentSubmissionRow;
    this.jumpControl.setValue('', { emitEvent: false });
    await this.navigateToStudentSubmission(targetRow.student_pid);
  }

  protected async goToPreviousSubmission(): Promise<void> {
    await this.navigateToSubmissionRow(this.previousSubmissionRow());
  }

  protected async goToNextSubmission(): Promise<void> {
    await this.navigateToSubmissionRow(this.nextSubmissionRow());
  }

  protected jumpOptionLabel(row: StudentSubmissionRow): string {
    const studentName = this.formatStudentName(row);
    const submissionId = row.submission?.id;
    const baseLabel = studentName || `Student ${row.student_pid}`;
    const submissionLabel =
      submissionId === undefined ? 'Unknown submission' : `Submission ${submissionId}`;
    return `${baseLabel} - ${submissionLabel}`;
  }

  private async loadData(studentPid: number): Promise<void> {
    this.loaded.set(false);
    this.errorMessage.set('');
    this.activity.set(null);
    this.rosterRows.set([]);
    this.submissions.set([]);
    this.selectedPriorSub.set(null);

    try {
      const [activity, roster, history] = await Promise.all([
        this.activityService.get(this.courseId, this.activityId),
        this.activityService.listSubmissionsRoster(this.courseId, this.activityId),
        this.activityService.getStudentHistory(this.courseId, this.activityId, studentPid),
      ]);
      this.activity.set(activity);
      this.rosterRows.set(roster);
      this.submissions.set(history);
      const currentRow = roster.find((row) => row.student_pid === studentPid) ?? null;
      const currentSubmissionId =
        currentRow?.submission?.id ??
        history.find((sub) => sub.is_active)?.id ??
        history[0]?.id ??
        null;
      const submissionLabel =
        currentSubmissionId === null
          ? `Student ${studentPid}`
          : `Submission ${currentSubmissionId}`;
      const currentStudentName = this.formatStudentName(currentRow);

      this.titleService.setTitle(`${activity.title} — ${submissionLabel}`);
      this.jumpControl.setValue('', { emitEvent: false });
      this.watchPendingJobs(history);
      this.layoutNavigation.setContextSection(
        buildActivityContextNav({
          courseId: this.courseId,
          activityId: this.activityId,
          role: 'staff',
          extraGroups: [
            {
              label: 'Submission',
              items: [
                {
                  route: `/courses/${this.courseId}/activities/${this.activityId}/submissions/${studentPid}`,
                  label: submissionLabel,
                  description:
                    currentStudentName === ''
                      ? 'Review this student submission history'
                      : `Submitted by ${currentStudentName}`,
                  icon: 'assignment',
                },
              ],
            },
          ],
        }),
      );
    } catch {
      this.errorMessage.set('Failed to load submission details.');
      this.layoutNavigation.clearContext();
    } finally {
      this.loaded.set(true);
    }
  }

  private watchPendingJobs(submissions: IyowSubmission[]): void {
    for (const sub of submissions) {
      if (sub.job && (sub.job.status === 'pending' || sub.job.status === 'processing')) {
        this.watchJob(sub.job.id);
      }
    }
  }

  private watchJob(jobId: number): void {
    if (this.watchedJobIds.has(jobId)) {
      return;
    }

    this.watchedJobIds.add(jobId);
    const jobSignal = this.jobUpdateService.updateForJob(jobId);
    effect(
      () => {
        const update = jobSignal();
        if (update?.status === 'completed' || update?.status === 'failed') {
          this.refreshSubmissions();
        }
      },
      { injector: this.injector },
    );
  }

  private async refreshSubmissions(): Promise<void> {
    try {
      const history = await this.activityService.getStudentHistory(
        this.courseId,
        this.activityId,
        this.studentPid(),
      );
      this.submissions.set(history);
    } catch {
      /* swallow — stale data is still visible */
    }
  }

  private formatStudentName(row: StudentSubmissionRow | null): string {
    if (row === null) {
      return '';
    }

    const parts = [row.given_name ?? '', row.family_name ?? ''].filter(
      (part) => part.trim() !== '',
    );
    if (parts.length > 0) {
      return parts.join(' ');
    }

    return row.email ?? '';
  }

  private studentSortValue(row: StudentSubmissionRow): string {
    return `${row.family_name ?? ''} ${row.given_name ?? ''} ${row.email}`.trim().toLowerCase();
  }

  private matchesJumpQuery(row: StudentSubmissionRow, query: string): boolean {
    const submissionId = row.submission?.id;
    return [
      this.formatStudentName(row).toLowerCase(),
      (row.email ?? '').toLowerCase(),
      String(row.student_pid),
      submissionId === undefined ? '' : String(submissionId),
    ].some((value) => value.includes(query));
  }

  private async navigateToSubmissionRow(row: StudentSubmissionRow | null): Promise<void> {
    if (row === null) {
      return;
    }

    await this.navigateToStudentSubmission(row.student_pid);
  }

  private async navigateToStudentSubmission(studentPid: number): Promise<void> {
    await this.router.navigate([
      '/courses',
      this.courseId,
      'activities',
      this.activityId,
      'submissions',
      studentPid,
    ]);
  }
}
