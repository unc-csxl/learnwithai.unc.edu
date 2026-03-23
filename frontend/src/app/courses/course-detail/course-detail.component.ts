import { Component, ChangeDetectionStrategy, inject, OnDestroy, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterOutlet } from '@angular/router';
import { CourseService } from '../course.service';
import { Course } from '../../api/models';
import { PageTitleService } from '../../page-title.service';
import {
  LayoutNavigationSection,
  LayoutNavigationService,
} from '../../layout/layout-navigation.service';

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
  private router = inject(Router);
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
        this.layoutNavigation.setSection(this.buildNavigationSection(course));
        await this.redirectStudentFromDashboard(course);
      } else {
        this.errorMessage.set('Course not found.');
        this.layoutNavigation.clear();
      }
    } catch {
      this.errorMessage.set('Failed to load course details.');
      this.layoutNavigation.clear();
    }
  }

  private buildNavigationSection(course: Course): LayoutNavigationSection {
    const baseSection = {
      title: course.name,
      subtitle: `${course.term} - Section ${course.section}`,
    };

    if (course.membership.type === 'student') {
      return {
        ...baseSection,
        label: 'Student view',
        items: [
          {
            route: `/courses/${this.courseId}/activities`,
            label: 'Student Activities',
            description: 'Review your course activities and assigned work',
            icon: 'assignment',
          },
          {
            route: `/courses/${this.courseId}/student`,
            label: 'Student Tools',
            description: 'Open student-facing tools and workflows',
            icon: 'build',
          },
        ],
      };
    }

    return {
      ...baseSection,
      label: 'Instructor view',
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
    };
  }

  private async redirectStudentFromDashboard(course: Course): Promise<void> {
    const activeChildPath = this.route.firstChild?.routeConfig?.path;
    if (course.membership.type !== 'student' || activeChildPath !== 'dashboard') {
      return;
    }

    await this.router.navigate(['/courses', this.courseId, 'activities']);
  }
}
