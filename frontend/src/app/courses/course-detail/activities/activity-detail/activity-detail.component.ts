import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  computed,
  OnDestroy,
  effect,
  DestroyRef,
  Injector,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { PageTitleService } from '../../../../page-title.service';
import { JobUpdateService } from '../../../../job-update.service';
import { ActivityService } from '../activity.service';
import { IyowActivity, IyowSubmission } from '../../../../api/models';

/** Instructor view showing activity details and student submissions. */
@Component({
  selector: 'app-activity-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DatePipe, MatCardModule, MatIconModule, MatChipsModule, MatProgressSpinnerModule],
  templateUrl: './activity-detail.component.html',
})
export class ActivityDetail implements OnDestroy {
  private activityService = inject(ActivityService);
  private route = inject(ActivatedRoute);
  private titleService = inject(PageTitleService);
  private jobUpdateService = inject(JobUpdateService);
  private injector = inject(Injector);
  private destroyRef = inject(DestroyRef);

  protected readonly courseId: number;
  protected readonly activityId: number;
  protected readonly activity = signal<IyowActivity | null>(null);
  protected readonly submissions = signal<IyowSubmission[]>([]);
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');

  protected readonly hasSubmissions = computed(() => this.submissions().length > 0);

  constructor() {
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.activityId = Number(this.route.snapshot.paramMap.get('activityId'));
    this.jobUpdateService.subscribe(this.courseId);
    this.loadData();
  }

  ngOnDestroy(): void {
    this.jobUpdateService.unsubscribe(this.courseId);
  }

  private async loadData(): Promise<void> {
    try {
      const [activity, submissions] = await Promise.all([
        this.activityService.get(this.courseId, this.activityId),
        this.activityService.listSubmissions(this.courseId, this.activityId),
      ]);
      this.activity.set(activity);
      this.titleService.setTitle(activity.title);
      this.submissions.set(submissions);
      this.watchAllJobs(submissions);
    } catch {
      this.errorMessage.set('Failed to load activity details.');
    } finally {
      this.loaded.set(true);
    }
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

  private watchAllJobs(submissions: IyowSubmission[]): void {
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
          this.refreshSubmission();
        }
      },
      { injector: this.injector, manualCleanup: true },
    );
  }

  private async refreshSubmission(): Promise<void> {
    try {
      const fresh = await this.activityService.listSubmissions(this.courseId, this.activityId);
      this.submissions.set(fresh);
    } catch {
      /* swallow — the list is still visible with stale data */
    }
  }
}
