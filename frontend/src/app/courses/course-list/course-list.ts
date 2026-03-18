import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CourseService } from '../course.service';
import { Course } from '../course.model';

/** Displays a list of courses the current user is enrolled in. */
@Component({
  selector: 'app-course-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <main>
      <header>
        <h1>My Courses</h1>
        <a routerLink="/courses/create" role="button">Create Course</a>
      </header>
      @if (courses().length > 0) {
        <ul>
          @for (course of courses(); track course.id) {
            <li>
              <a [routerLink]="['/courses', course.id]">
                {{ course.name }} — {{ course.term }} ({{ course.section }})
              </a>
            </li>
          }
        </ul>
      } @else if (loaded()) {
        <p>You are not enrolled in any courses.</p>
      }
    </main>
  `,
})
export class CourseList {
  private courseService = inject(CourseService);

  protected readonly courses = signal<Course[]>([]);
  protected readonly loaded = signal(false);

  constructor() {
    this.courseService.getMyCourses().subscribe({
      next: (courses) => {
        this.courses.set(courses);
        this.loaded.set(true);
      },
      error: () => this.loaded.set(true),
    });
  }
}
