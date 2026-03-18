import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatTabsModule } from '@angular/material/tabs';
import { CourseService } from '../course.service';
import { Course } from '../../api/models';

/** Course detail shell with sub-navigation for instructor/student views. */
@Component({
  selector: 'app-course-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, MatTabsModule],
  templateUrl: './course-detail.component.html',
})
export class CourseDetail {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);

  protected readonly course = signal<Course | null>(null);
  protected readonly errorMessage = signal('');
  protected readonly courseId: number;

  constructor() {
    this.courseId = Number(this.route.snapshot.paramMap.get('id'));
    this.loadCourse();
  }

  private async loadCourse(): Promise<void> {
    try {
      const courses = await this.courseService.getMyCourses();
      const course = courses.find((c) => c.id === this.courseId);
      if (course) {
        this.course.set(course);
      } else {
        this.errorMessage.set('Course not found.');
      }
    } catch {
      this.errorMessage.set('Failed to load course details.');
    }
  }
}
