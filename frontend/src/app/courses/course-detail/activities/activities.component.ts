import { Component, ChangeDetectionStrategy, inject, signal, computed } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { PageTitleService } from '../../../page-title.service';
import { CourseService } from '../../course.service';
import { ActivityService } from './activity.service';
import { Activity } from '../../../api/models';

/** Lists activities for a course. Role-aware: instructors see all, students see released. */
@Component({
  selector: 'app-activities',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, DatePipe, MatButtonModule, MatIconModule, MatTableModule],
  templateUrl: './activities.component.html',
})
export class Activities {
  private titleService = inject(PageTitleService);
  private courseService = inject(CourseService);
  private activityService = inject(ActivityService);
  private route = inject(ActivatedRoute);

  protected readonly courseId: number;
  protected readonly activities = signal<Activity[]>([]);
  protected readonly loaded = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly isStaff = signal(false);

  protected readonly hasActivities = computed(() => this.activities().length > 0);
  protected readonly studentColumns = ['title', 'status', 'release_date', 'due_date'];
  protected readonly instructorColumns = [
    'title',
    'release_date',
    'due_date',
    'active_submission_count',
  ];

  constructor() {
    this.titleService.setTitle('Student Activities');
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.loadData();
  }

  protected activityLink(activity: Activity): string[] {
    return this.isStaff() ? [String(activity.id)] : [String(activity.id), 'submit'];
  }

  private async loadData(): Promise<void> {
    try {
      const [courses, activities] = await Promise.all([
        this.courseService.getMyCourses(),
        this.activityService.list(this.courseId),
      ]);
      const course = courses.find((c) => c.id === this.courseId);
      this.isStaff.set(course?.membership.type !== 'student');
      this.activities.set(activities);
    } catch {
      this.errorMessage.set('Failed to load activities.');
    } finally {
      this.loaded.set(true);
    }
  }
}
