import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { CourseService } from '../course.service';
import { Course } from '../../api/models';

/** Displays a list of courses the current user is enrolled in. */
@Component({
  selector: 'app-course-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, MatButtonModule, MatCardModule, MatIconModule],
  templateUrl: './course-list.component.html',
})
export class CourseList {
  private courseService = inject(CourseService);

  protected readonly courses = signal<Course[]>([]);
  protected readonly loaded = signal(false);

  constructor() {
    this.loadCourses();
  }

  private async loadCourses(): Promise<void> {
    try {
      const courses = await this.courseService.getMyCourses();
      this.courses.set(courses);
    } catch {
      // Courses remain empty on failure.
    } finally {
      this.loaded.set(true);
    }
  }
}
