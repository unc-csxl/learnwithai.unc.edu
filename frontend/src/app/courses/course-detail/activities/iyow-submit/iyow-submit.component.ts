import {
  Component,
  ChangeDetectionStrategy,
  computed,
  EffectRef,
  inject,
  signal,
  OnDestroy,
  effect,
  Injector,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DatePipe } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { PageTitleService } from '../../../../page-title.service';
import { SuccessSnackbarService } from '../../../../success-snackbar.service';
import { JobUpdateService } from '../../../../job-update.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { CourseService } from '../../../course.service';
import { ActivityService } from '../activity.service';
import { buildActivityContextNav } from '../activity-nav';
import { IyowActivity, IyowSubmission } from '../../../../api/models';
import { MarkdownToHtmlPipe } from '../../../../shared/markdown-to-html.pipe';

/** Student view for submitting an IYOW response and viewing feedback. */
@Component({
  selector: 'app-iyow-submit',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MarkdownToHtmlPipe,
  ],
  templateUrl: './iyow-submit.component.html',
  styleUrl: './iyow-submit.component.scss',
})
export class IyowSubmit implements OnDestroy {
  private activityService = inject(ActivityService);
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private titleService = inject(PageTitleService);
  private successSnackbar = inject(SuccessSnackbarService);
  private jobUpdateService = inject(JobUpdateService);
  private layoutNavigation = inject(LayoutNavigationService);
  private injector = inject(Injector);
  private jobWatcher: EffectRef | null = null;

  protected readonly courseId: number;
  protected readonly activityId: number;
  protected readonly dateTimeFormat = 'MMM d, y, h:mm a';
  protected readonly activity = signal<IyowActivity | null>(null);
  protected readonly activeSubmission = signal<IyowSubmission | null>(null);
  protected readonly editingSubmission = signal(false);
  protected readonly loaded = signal(false);
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly showSubmissionEditor = computed(
    () => this.editingSubmission() || this.activeSubmission() === null,
  );
  protected readonly feedbackPending = computed(() => {
    const submission = this.activeSubmission();
    const status = submission?.job?.status;
    return Boolean(
      submission && !submission.feedback && (status === 'pending' || status === 'processing'),
    );
  });

  protected readonly form = this.fb.nonNullable.group({
    response_text: ['', [Validators.required, Validators.minLength(10)]],
  });

  constructor() {
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.activityId = Number(this.route.snapshot.paramMap.get('activityId'));
    this.jobUpdateService.subscribe(this.courseId);
    this.loadData();
  }

  ngOnDestroy(): void {
    this.stopWatchingJob();
    this.jobUpdateService.unsubscribe(this.courseId);
  }

  protected startEditingSubmission(): void {
    const submission = this.activeSubmission();
    if (!submission) {
      return;
    }

    this.form.controls.response_text.setValue(submission.response_text);
    this.form.markAsPristine();
    this.form.markAsUntouched();
    this.errorMessage.set('');
    this.editingSubmission.set(true);
  }

  protected cancelEditingSubmission(): void {
    const submission = this.activeSubmission();
    if (!submission || !this.editingSubmission()) {
      return;
    }

    if (this.form.dirty && !globalThis.confirm('Discard your unsaved changes?')) {
      return;
    }

    this.form.reset({ response_text: submission.response_text });
    this.form.markAsPristine();
    this.form.markAsUntouched();
    this.errorMessage.set('');
    this.editingSubmission.set(false);
  }

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) return;

    this.submitting.set(true);
    this.errorMessage.set('');
    try {
      const { response_text } = this.form.getRawValue();
      const submission = await this.activityService.submitIyow(
        this.courseId,
        this.activityId,
        response_text,
      );
      this.setActiveSubmission(submission);
      this.editingSubmission.set(false);
      this.form.reset({ response_text: '' });
      this.successSnackbar.open('Response submitted!');
    } catch {
      this.errorMessage.set('Failed to submit response.');
    } finally {
      this.submitting.set(false);
    }
  }

  private async loadData(): Promise<void> {
    try {
      const [activity, active, courses] = await Promise.all([
        this.activityService.get(this.courseId, this.activityId),
        this.activityService.getActiveSubmission(this.courseId, this.activityId),
        this.courseService.getMyCourses(),
      ]);
      const course = courses.find((candidate) => candidate.id === this.courseId);
      const isStaff = course?.membership.type !== 'student';
      this.activity.set(activity);
      this.titleService.setTitle(activity.title);
      this.setActiveSubmission(active);
      this.layoutNavigation.setContextSection(
        buildActivityContextNav({
          courseId: this.courseId,
          activityId: this.activityId,
          role: isStaff ? 'staff' : 'student',
        }),
      );
    } catch {
      this.errorMessage.set('Failed to load activity.');
      this.layoutNavigation.clearContext();
    } finally {
      this.loaded.set(true);
    }
  }

  private watchJob(jobId: number): void {
    this.stopWatchingJob();
    const jobSignal = this.jobUpdateService.updateForJob(jobId);
    this.jobWatcher = effect(
      () => {
        const update = jobSignal();
        if (update?.status === 'completed' || update?.status === 'failed') {
          this.stopWatchingJob();
          void this.refreshActiveSubmission();
        }
      },
      { injector: this.injector },
    );
  }

  private async refreshActiveSubmission(): Promise<void> {
    try {
      const active = await this.activityService.getActiveSubmission(this.courseId, this.activityId);
      this.setActiveSubmission(active);
    } catch {
      /* swallow */
    }
  }

  private setActiveSubmission(submission: IyowSubmission | null): void {
    this.activeSubmission.set(submission);
    const status = submission?.job?.status;
    if (submission?.job && (status === 'pending' || status === 'processing')) {
      this.watchJob(submission.job.id);
      return;
    }

    this.stopWatchingJob();
  }

  private stopWatchingJob(): void {
    this.jobWatcher?.destroy();
    this.jobWatcher = null;
  }
}
