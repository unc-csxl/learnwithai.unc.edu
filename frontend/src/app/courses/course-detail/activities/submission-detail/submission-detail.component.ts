import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  OnDestroy,
  effect,
  Injector,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatMenuModule } from '@angular/material/menu';
import { MatButtonModule } from '@angular/material/button';
import { PageTitleService } from '../../../../page-title.service';
import { JobUpdateService } from '../../../../job-update.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { ActivityService } from '../activity.service';
import { buildActivityContextNav } from '../activity-nav';
import { IyowActivity, IyowSubmission } from '../../../../api/models';
import { MarkdownToHtmlPipe } from '../../../../shared/markdown-to-html.pipe';

/** Instructor view showing a single student's submission detail. */
@Component({
  selector: 'app-submission-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatMenuModule,
    MatButtonModule,
    MarkdownToHtmlPipe,
  ],
  templateUrl: './submission-detail.component.html',
})
export class SubmissionDetail implements OnDestroy {
  private activityService = inject(ActivityService);
  private route = inject(ActivatedRoute);
  private titleService = inject(PageTitleService);
  private jobUpdateService = inject(JobUpdateService);
  private layoutNavigation = inject(LayoutNavigationService);
  private injector = inject(Injector);

  protected readonly courseId: number;
  protected readonly activityId: number;
  protected readonly studentPid: number;
  protected readonly dateTimeFormat = 'MMM d, y, h:mm a';
  protected readonly activity = signal<IyowActivity | null>(null);
  protected readonly submissions = signal<IyowSubmission[]>([]);
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly selectedPriorSub = signal<IyowSubmission | null>(null);

  constructor() {
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.activityId = Number(this.route.snapshot.paramMap.get('activityId'));
    this.studentPid = Number(this.route.snapshot.paramMap.get('studentPid'));
    this.jobUpdateService.subscribe(this.courseId);
    this.loadData();
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

  private async loadData(): Promise<void> {
    try {
      const [activity, history] = await Promise.all([
        this.activityService.get(this.courseId, this.activityId),
        this.activityService.getStudentHistory(this.courseId, this.activityId, this.studentPid),
      ]);
      this.activity.set(activity);
      this.titleService.setTitle(`${activity.title} — Student ${this.studentPid}`);
      this.submissions.set(history);
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
                  route: `/courses/${this.courseId}/activities/${this.activityId}/submissions/${this.studentPid}`,
                  label: `Student ${this.studentPid}`,
                  description: 'Review this student submission history',
                  icon: 'person',
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
    const jobSignal = this.jobUpdateService.updateForJob(jobId);
    effect(
      () => {
        const update = jobSignal();
        if (update?.status === 'completed' || update?.status === 'failed') {
          this.refreshSubmissions();
        }
      },
      { injector: this.injector, manualCleanup: true },
    );
  }

  private async refreshSubmissions(): Promise<void> {
    try {
      const history = await this.activityService.getStudentHistory(
        this.courseId,
        this.activityId,
        this.studentPid,
      );
      this.submissions.set(history);
    } catch {
      /* swallow — stale data is still visible */
    }
  }
}
