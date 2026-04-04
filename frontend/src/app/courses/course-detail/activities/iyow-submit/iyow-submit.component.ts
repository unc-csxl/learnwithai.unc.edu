import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  OnDestroy,
  effect,
  DestroyRef,
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
import { IyowActivity, IyowSubmission } from '../../../../api/models';

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
  ],
  templateUrl: './iyow-submit.component.html',
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
  private destroyRef = inject(DestroyRef);

  protected readonly courseId: number;
  protected readonly activityId: number;
  protected readonly activity = signal<IyowActivity | null>(null);
  protected readonly activeSubmission = signal<IyowSubmission | null>(null);
  protected readonly loaded = signal(false);
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');

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
    this.jobUpdateService.unsubscribe(this.courseId);
    this.layoutNavigation.clearContext();
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
      this.activeSubmission.set(submission);
      this.form.reset();
      this.successSnackbar.open('Response submitted!');
      if (submission.job && submission.job.status !== 'completed') {
        this.watchJob(submission.job.id);
      }
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
      this.activeSubmission.set(active);
      this.layoutNavigation.setContextSection({
        visibleBaseRoutes: [
          isStaff ? `/courses/${this.courseId}/dashboard` : `/courses/${this.courseId}/student`,
          `/courses/${this.courseId}/activities`,
        ],
        groups: [
          {
            label: 'Current activity',
            items: [
              {
                route: isStaff
                  ? `/courses/${this.courseId}/activities/${this.activityId}`
                  : `/courses/${this.courseId}/activities/${this.activityId}/submit`,
                label: activity.title,
                description: isStaff ? 'Open this activity overview' : 'Open this student activity',
                icon: 'assignment',
              },
              ...(isStaff
                ? [
                    {
                      route: `/courses/${this.courseId}/activities/${this.activityId}/submit`,
                      label: 'Preview & Test',
                      description: 'Preview and test this activity',
                      icon: 'preview',
                    },
                  ]
                : []),
            ],
          },
        ],
      });
      if (active?.job && (active.job.status === 'pending' || active.job.status === 'processing')) {
        this.watchJob(active.job.id);
      }
    } catch {
      this.errorMessage.set('Failed to load activity.');
      this.layoutNavigation.clearContext();
    } finally {
      this.loaded.set(true);
    }
  }

  private watchJob(jobId: number): void {
    const jobSignal = this.jobUpdateService.updateForJob(jobId);
    effect(
      () => {
        const update = jobSignal();
        if (update?.status === 'completed' || update?.status === 'failed') {
          this.refreshActiveSubmission();
        }
      },
      { injector: this.injector, manualCleanup: true },
    );
  }

  private async refreshActiveSubmission(): Promise<void> {
    try {
      const active = await this.activityService.getActiveSubmission(this.courseId, this.activityId);
      this.activeSubmission.set(active);
    } catch {
      /* swallow */
    }
  }
}
