/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { CourseService } from '../course.service';
import { PageTitleService } from '../../page-title.service';
import { CourseFormFields } from '../course-form-fields/course-form-fields.component';

/** Form for creating a new course. */
@Component({
  selector: 'app-create-course',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, MatButtonModule, CourseFormFields],
  templateUrl: './create-course.component.html',
})
export class CreateCourse {
  private courseService = inject(CourseService);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private titleService = inject(PageTitleService);

  protected readonly form = this.fb.nonNullable.group({
    course_number: ['', Validators.required],
    name: ['', Validators.required],
    description: [''],
    term: ['', Validators.required],
    year: [new Date().getFullYear(), [Validators.required, Validators.min(2026)]],
  });

  constructor() {
    this.titleService.setTitle('Create Course');
  }

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) {
      return;
    }
    const raw = this.form.getRawValue();
    const course = await this.courseService.createCourse({
      course_number: raw.course_number,
      name: raw.name,
      description: raw.description,
      term: raw.term as 'fall' | 'winter' | 'spring' | 'summer',
      year: raw.year,
    });
    await this.router.navigate(['/courses', course.id]);
  }
}
