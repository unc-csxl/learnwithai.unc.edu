import { Component, ChangeDetectionStrategy, inject, signal, computed } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { CourseService } from '../../course.service';
import { Membership } from '../../../api/models';

/** Displays the roster for a course. */
@Component({
  selector: 'app-roster',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, MatTableModule, MatButtonModule, MatIconModule],
  templateUrl: './roster.component.html',
})
export class Roster {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);

  protected readonly roster = signal<Membership[]>([]);
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly courseId: number;
  protected readonly displayedColumns = ['user_pid', 'type', 'state'];
  protected readonly dataSource = computed(() => this.roster());

  constructor() {
    this.courseId = Number(this.route.parent?.snapshot.paramMap.get('id'));
    this.loadRoster();
  }

  private async loadRoster(): Promise<void> {
    try {
      const roster = await this.courseService.getRoster(this.courseId);
      this.roster.set(roster);
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
