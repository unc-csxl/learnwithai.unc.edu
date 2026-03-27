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
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { PageTitleService } from '../../../../page-title.service';
import { SuccessSnackbarService } from '../../../../success-snackbar.service';
import { JobUpdateService } from '../../../../job-update.service';
import { JokeGeneratorService } from '../joke-generator.service';
import { AsyncJobInfo, JokeRequest } from '../../../../api/models';

/** Lets instructors generate AI-powered jokes for their course. */
@Component({
  selector: 'app-joke-generator',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatCardModule,
    MatProgressSpinnerModule,
    MatChipsModule,
  ],
  templateUrl: './joke-generator.component.html',
  styleUrl: './joke-generator.component.scss',
})
export class JokeGenerator implements OnDestroy {
  private jokeService = inject(JokeGeneratorService);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private titleService = inject(PageTitleService);
  private successSnackbar = inject(SuccessSnackbarService);
  private jobUpdateService = inject(JobUpdateService);
  private injector = inject(Injector);
  private destroyRef = inject(DestroyRef);

  protected readonly courseId: number;
  protected readonly requests = signal<JokeRequest[]>([]);
  protected readonly loaded = signal(false);
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');

  protected readonly form = this.fb.nonNullable.group({
    prompt: ['', [Validators.required, Validators.minLength(3)]],
  });

  protected readonly hasRequests = computed(() => this.requests().length > 0);

  constructor() {
    this.titleService.setTitle('Joke Generator');
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.jobUpdateService.subscribe(this.courseId);
    this.loadRequests();
  }

  ngOnDestroy(): void {
    this.jobUpdateService.unsubscribe(this.courseId);
  }

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) return;

    this.submitting.set(true);
    try {
      const { prompt } = this.form.getRawValue();
      const created = await this.jokeService.create(this.courseId, prompt);
      this.form.reset();
      this.successSnackbar.open('Joke request submitted!');
      this.requests.update((prev) => [created, ...prev]);
      if (created.job) {
        this.watchJob(created.job.id, created.id);
      }
    } catch {
      this.errorMessage.set('Failed to submit joke request.');
    } finally {
      this.submitting.set(false);
    }
  }

  protected async onDelete(jobId: number): Promise<void> {
    try {
      await this.jokeService.delete(this.courseId, jobId);
      this.requests.update((prev) => prev.filter((r) => r.id !== jobId));
      this.successSnackbar.open('Joke request deleted.');
    } catch {
      this.errorMessage.set('Failed to delete joke request.');
    }
  }

  protected statusLabel(status: string | undefined): string {
    const labels: Record<string, string> = {
      pending: 'Pending',
      processing: 'Processing',
      completed: 'Completed',
      failed: 'Failed',
    };
    return (status && labels[status]) ?? 'Unknown';
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

  protected requestSubtitle(job: AsyncJobInfo | null | undefined): string {
    if (!job) return 'Unknown';
    if (job.status === 'completed') {
      return job.completed_at ? this.formatCompletedAt(job.completed_at) : '';
    }
    return this.statusLabel(job.status);
  }

  // ------------------------------------------------------------------
  // Private helpers
  // ------------------------------------------------------------------

  private formatCompletedAt(completedAt: string): string {
    const completedDate = new Date(completedAt);
    if (Number.isNaN(completedDate.getTime())) return '';

    const month = new Intl.DateTimeFormat('en-US', { month: 'long' }).format(completedDate);
    const day = completedDate.getDate();
    const year = completedDate.getFullYear();
    const hours = completedDate.getHours();
    const minutes = completedDate.getMinutes();
    const displayHour = hours % 12 || 12;
    const meridiem = hours >= 12 ? 'pm' : 'am';
    const time =
      minutes === 0
        ? `${displayHour}${meridiem}`
        : `${displayHour}:${minutes.toString().padStart(2, '0')}${meridiem}`;

    return `${month} ${day}${this.ordinalSuffix(day)}, ${year} at ${time}`;
  }

  private ordinalSuffix(day: number): string {
    if (day >= 11 && day <= 13) return 'th';

    switch (day % 10) {
      case 1:
        return 'st';
      case 2:
        return 'nd';
      case 3:
        return 'rd';
      default:
        return 'th';
    }
  }

  private async loadRequests(): Promise<void> {
    try {
      const items = await this.jokeService.list(this.courseId);
      this.requests.set(items);
      this.loaded.set(true);
      for (const item of items) {
        if (item.job && (item.job.status === 'pending' || item.job.status === 'processing')) {
          this.watchJob(item.job.id, item.id);
        }
      }
    } catch {
      this.errorMessage.set('Failed to load joke requests.');
      this.loaded.set(true);
    }
  }

  private watchJob(asyncJobId: number, jokeId: number): void {
    const jobSignal = this.jobUpdateService.updateForJob(asyncJobId);
    const effectRef = effect(
      async () => {
        const update = jobSignal();
        if (update === null) return;
        if (update.status !== 'completed' && update.status !== 'failed') return;

        effectRef.destroy();
        await this.refreshJob(jokeId);
      },
      { injector: this.injector },
    );
    this.destroyRef.onDestroy(() => effectRef.destroy());
  }

  private async refreshJob(jokeId: number): Promise<void> {
    try {
      const updated = await this.jokeService.get(this.courseId, jokeId);
      this.requests.update((prev) => prev.map((r) => (r.id === jokeId ? updated : r)));
    } catch {
      /* Silently ignore refresh errors; the list still shows the old state. */
    }
  }
}
