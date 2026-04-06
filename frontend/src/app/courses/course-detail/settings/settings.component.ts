import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { CourseService } from '../../course.service';
import { CourseFormFields } from '../../course-form-fields/course-form-fields.component';
import { PageTitleService } from '../../../page-title.service';
import { SuccessSnackbarService } from '../../../success-snackbar.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';
import { Course } from '../../../api/models';

/** Editable course settings form for instructors. */
@Component({
  selector: 'app-settings',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, MatButtonModule, MatSnackBarModule, CourseFormFields],
  templateUrl: './settings.component.html',
})
export class Settings {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private titleService = inject(PageTitleService);
  private successSnackbar = inject(SuccessSnackbarService);
  private layoutNavigation = inject(LayoutNavigationService);

  protected readonly saving = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly loaded = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    course_number: ['', Validators.required],
    name: ['', Validators.required],
    description: [''],
    term: ['', Validators.required],
    year: [0, [Validators.required, Validators.min(2026)]],
  });

  private courseId = 0;

  constructor() {
    this.layoutNavigation.clearContext();
    this.titleService.setTitle('Course Settings');
    this.courseId = Number(this.route.parent!.snapshot.paramMap.get('id'));
    this.loadCourse();
  }

  private async loadCourse(): Promise<void> {
    try {
      const courses = await this.courseService.getMyCourses();
      const course = courses.find((c: Course) => c.id === this.courseId);
      if (course) {
        this.form.setValue({
          course_number: course.course_number,
          name: course.name,
          description: course.description,
          term: course.term,
          year: course.year,
        });
        this.loaded.set(true);
      } else {
        this.errorMessage.set('Course not found.');
      }
    } catch {
      this.errorMessage.set('Failed to load course.');
    }
  }

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) {
      return;
    }
    this.saving.set(true);
    const raw = this.form.getRawValue();
    try {
      const updated = await this.courseService.updateCourse(this.courseId, {
        course_number: raw.course_number,
        name: raw.name,
        description: raw.description,
        term: raw.term as 'fall' | 'winter' | 'spring' | 'summer',
        year: raw.year,
      });
      const term = updated.term.charAt(0).toUpperCase() + updated.term.slice(1);
      this.layoutNavigation.updateSection((currentSection) => {
        if (currentSection.groups.length === 0 || currentSection.groups[0].items.length === 0) {
          return currentSection;
        }

        const [firstGroup, ...remainingGroups] = currentSection.groups;
        const [courseHomeItem, ...remainingItems] = firstGroup.items;

        return {
          ...currentSection,
          groups: [
            {
              ...firstGroup,
              items: [
                {
                  ...courseHomeItem,
                  label: updated.course_number,
                  subtitle: `${term} ${updated.year}`,
                  description: courseHomeItem.route.endsWith('/student')
                    ? `${updated.name} student dashboard`
                    : `${updated.name} dashboard`,
                },
                ...remainingItems,
              ],
            },
            ...remainingGroups,
          ],
        };
      });
      this.successSnackbar.open('Course settings updated.');
      await this.router.navigate(['/courses', this.courseId, 'dashboard']);
    } catch {
      this.saving.set(false);
      this.errorMessage.set('Failed to save course settings.');
    }
  }
}
