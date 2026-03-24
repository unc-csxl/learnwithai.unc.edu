import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { CourseService } from '../../course.service';
import { CourseFormFields } from '../../course-form-fields/course-form-fields.component';
import { PageTitleService } from '../../../page-title.service';
import { Course } from '../../../api/models';

/** Editable course settings form for instructors. */
@Component({
  selector: 'app-settings',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, MatButtonModule, CourseFormFields],
  templateUrl: './settings.component.html',
})
export class Settings {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private titleService = inject(PageTitleService);

  protected readonly saving = signal(false);
  protected readonly saved = signal(false);
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
    this.saved.set(false);
    const raw = this.form.getRawValue();
    try {
      await this.courseService.updateCourse(this.courseId, {
        course_number: raw.course_number,
        name: raw.name,
        description: raw.description,
        term: raw.term as 'fall' | 'winter' | 'spring' | 'summer',
        year: raw.year,
      });
      this.saving.set(false);
      this.saved.set(true);
    } catch {
      this.saving.set(false);
      this.errorMessage.set('Failed to save course settings.');
    }
  }
}
