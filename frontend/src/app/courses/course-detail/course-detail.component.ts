import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CourseService } from '../course.service';
import { Membership } from '../../api/models';

/** Displays the roster for a course. Instructors see all members. */
@Component({
  selector: 'app-course-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  templateUrl: './course-detail.component.html',
  styles: `
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }
  `,
})
export class CourseDetail {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);

  protected readonly roster = signal<Membership[]>([]);
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly courseId: number;

  constructor() {
    this.courseId = Number(this.route.snapshot.paramMap.get('id'));
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
