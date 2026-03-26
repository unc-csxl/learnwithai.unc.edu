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
import { JokeRequest } from '../../../../api/models';

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
      this.watchJob(created.id);
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

  protected statusLabel(status: string): string {
    const labels: Record<string, string> = {
      pending: 'Pending',
      processing: 'Processing',
      completed: 'Completed',
      failed: 'Failed',
    };
    return labels[status] ?? status;
  }

  protected statusIcon(status: string): string {
    const icons: Record<string, string> = {
      pending: 'schedule',
      processing: 'sync',
      completed: 'check_circle',
      failed: 'error',
    };
    return icons[status] ?? 'help';
  }

  // ------------------------------------------------------------------
  // Private helpers
  // ------------------------------------------------------------------

  private async loadRequests(): Promise<void> {
    try {
      const items = await this.jokeService.list(this.courseId);
      this.requests.set(items);
      this.loaded.set(true);
      for (const item of items) {
        if (item.status === 'pending' || item.status === 'processing') {
          this.watchJob(item.id);
        }
      }
    } catch {
      this.errorMessage.set('Failed to load joke requests.');
      this.loaded.set(true);
    }
  }

  private watchJob(jobId: number): void {
    const jobSignal = this.jobUpdateService.updateForJob(jobId);
    const effectRef = effect(
      async () => {
        const update = jobSignal();
        if (update === null) return;
        if (update.status !== 'completed' && update.status !== 'failed') return;

        effectRef.destroy();
        await this.refreshJob(jobId);
      },
      { injector: this.injector },
    );
    this.destroyRef.onDestroy(() => effectRef.destroy());
  }

  private async refreshJob(jobId: number): Promise<void> {
    try {
      const updated = await this.jokeService.get(this.courseId, jobId);
      this.requests.update((prev) => prev.map((r) => (r.id === jobId ? updated : r)));
    } catch {
      /* Silently ignore refresh errors; the list still shows the old state. */
    }
  }
}
