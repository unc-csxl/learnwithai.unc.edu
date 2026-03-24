import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  computed,
  OnDestroy,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { CourseService } from '../../course.service';
import { RosterMember, RosterUploadStatus } from '../../../api/models';
import { PageTitleService } from '../../../page-title.service';
import { RosterUploadResultDialog } from './roster-upload-result-dialog.component';

const DEBOUNCE_MS = 300;
const MIN_SEARCH_LENGTH = 3;
const POLL_INTERVAL_MS = 2000;

/** Displays the roster for a course. */
@Component({
  selector: 'app-roster',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatPaginatorModule,
    MatFormFieldModule,
    MatInputModule,
    MatSnackBarModule,
    MatDialogModule,
  ],
  templateUrl: './roster.component.html',
  styleUrl: './roster.component.scss',
})
export class Roster implements OnDestroy {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);
  private titleService = inject(PageTitleService);
  private snackBar = inject(MatSnackBar);
  private dialog = inject(MatDialog);
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private pollTimer: ReturnType<typeof setTimeout> | null = null;

  protected readonly roster = signal<RosterMember[]>([]);
  protected readonly total = signal(0);
  protected readonly page = signal(1);
  protected readonly pageSize = signal(25);
  protected readonly searchQuery = signal('');
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly uploading = signal(false);
  protected readonly courseId: number;
  protected readonly displayedColumns = ['given_name', 'family_name', 'user_pid', 'email'];
  protected readonly dataSource = computed(() => this.roster());

  constructor() {
    this.titleService.setTitle('Roster');
    this.courseId = Number(this.route.parent?.snapshot.paramMap.get('id'));
    this.loadRoster();
  }

  ngOnDestroy(): void {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
    }
    if (this.pollTimer !== null) {
      clearTimeout(this.pollTimer);
    }
  }

  protected onSearchInput(value: string): void {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      const query = value.length >= MIN_SEARCH_LENGTH ? value : '';
      if (query !== this.searchQuery()) {
        this.searchQuery.set(query);
        this.page.set(1);
        this.loadRoster();
      }
    }, DEBOUNCE_MS);
  }

  protected onPage(event: PageEvent): void {
    this.page.set(event.pageIndex + 1);
    this.pageSize.set(event.pageSize);
    this.loadRoster();
  }

  protected isInactive(member: RosterMember): boolean {
    return member.state !== 'enrolled';
  }

  protected async onFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    this.uploading.set(true);
    try {
      const result = await this.courseService.uploadRoster(this.courseId, file);
      this.snackBar.open('Roster upload processing…', undefined, {
        duration: 0,
      });
      this.pollUploadStatus(result.id);
    } catch {
      this.snackBar.open('Failed to upload roster CSV.', 'Dismiss', {
        duration: 5000,
      });
    } finally {
      this.uploading.set(false);
      input.value = '';
    }
  }

  private pollUploadStatus(jobId: number): void {
    this.pollTimer = setTimeout(async () => {
      try {
        const status = await this.courseService.getRosterUploadStatus(this.courseId, jobId);
        if (status.status === 'completed' || status.status === 'failed') {
          this.snackBar.dismiss();
          this.showUploadResult(status);
          await this.loadRoster();
        } else {
          this.pollUploadStatus(jobId);
        }
      } catch {
        this.snackBar.open('Failed to check upload status.', 'Dismiss', {
          duration: 5000,
        });
      }
    }, POLL_INTERVAL_MS);
  }

  private showUploadResult(status: RosterUploadStatus): void {
    this.dialog.open(RosterUploadResultDialog, {
      data: status,
      width: '400px',
    });
  }

  private async loadRoster(): Promise<void> {
    try {
      const result = await this.courseService.getRoster(this.courseId, {
        page: this.page(),
        pageSize: this.pageSize(),
        query: this.searchQuery() || undefined,
      });
      this.roster.set(result.items);
      this.total.set(result.total);
    } catch (err: unknown) {
      if (err != null && typeof err === 'object' && 'status' in err && err.status === 403) {
        this.errorMessage.set('You do not have permission to view this roster.');
      } else {
        this.errorMessage.set('Failed to load roster.');
      }
    } finally {
      this.loaded.set(true);
    }
  }
}
