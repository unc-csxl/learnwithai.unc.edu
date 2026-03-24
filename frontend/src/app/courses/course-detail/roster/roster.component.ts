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
import { CourseService } from '../../course.service';
import { RosterMember } from '../../../api/models';
import { PageTitleService } from '../../../page-title.service';

const DEBOUNCE_MS = 300;
const MIN_SEARCH_LENGTH = 3;

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
  ],
  templateUrl: './roster.component.html',
  styleUrl: './roster.component.scss',
})
export class Roster implements OnDestroy {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);
  private titleService = inject(PageTitleService);
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;

  protected readonly roster = signal<RosterMember[]>([]);
  protected readonly total = signal(0);
  protected readonly page = signal(1);
  protected readonly pageSize = signal(25);
  protected readonly searchQuery = signal('');
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
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
