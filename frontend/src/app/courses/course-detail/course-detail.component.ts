import { Component, ChangeDetectionStrategy, inject, OnDestroy, signal } from '@angular/core';
import { ActivatedRoute, RouterOutlet } from '@angular/router';
import { CourseService } from '../course.service';
import { Course } from '../../api/models';
import { PageTitleService } from '../../page-title.service';
import { LayoutNavigationService } from '../../layout/layout-navigation.service';

/** Course detail shell with sub-navigation for instructor/student views. */
@Component({
  selector: 'app-course-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet],
  templateUrl: './course-detail.component.html',
})
export class CourseDetail implements OnDestroy {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);
  private titleService = inject(PageTitleService);
  private layoutNavigation = inject(LayoutNavigationService);

  protected readonly course = signal<Course | null>(null);
  protected readonly errorMessage = signal('');
  protected readonly courseId: number;

  constructor() {
    this.courseId = Number(this.route.snapshot.paramMap.get('id'));
    this.loadCourse();
  }

  ngOnDestroy(): void {
    this.layoutNavigation.clear();
  }

  private async loadCourse(): Promise<void> {
    try {
      const courses = await this.courseService.getMyCourses();
      const course = courses.find((c) => c.id === this.courseId);
      if (course) {
        this.course.set(course);
        this.titleService.setTitle(course.name);
        this.layoutNavigation.setSection({
          label: 'Instructor view',
          title: course.name,
          subtitle: `${course.term} - Section ${course.section}`,
          items: [
            {
              route: `/courses/${this.courseId}/dashboard`,
              label: 'Dashboard',
              description: 'Course overview and quick links',
              icon: 'dashboard',
            },
            {
              route: `/courses/${this.courseId}/activities`,
              label: 'Student Activities',
              description: 'Review student-facing work and participation',
              icon: 'assignment',
            },
            {
              route: `/courses/${this.courseId}/tools`,
              label: 'Instructor Tools',
              description: 'Manage instructional workflows and tools',
              icon: 'build',
            },
            {
              route: `/courses/${this.courseId}/roster`,
              label: 'Roster',
              description: 'See current course membership',
              icon: 'groups',
            },
            {
              route: `/courses/${this.courseId}/settings`,
              label: 'Course Settings',
              description: 'Adjust course-level options and setup',
              icon: 'settings',
            },
          ],
        });
      } else {
        this.errorMessage.set('Course not found.');
        this.layoutNavigation.clear();
      }
    } catch {
      this.errorMessage.set('Failed to load course details.');
      this.layoutNavigation.clear();
    }
  }
}
