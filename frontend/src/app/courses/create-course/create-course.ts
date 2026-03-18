import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { CourseService } from '../course.service';

/** Form for creating a new course. */
@Component({
  selector: 'app-create-course',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule],
  template: `
    <main>
      <h1>Create Course</h1>
      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div>
          <label for="name">Course Name</label>
          <input id="name" formControlName="name" type="text" />
        </div>
        <div>
          <label for="term">Term</label>
          <input id="term" formControlName="term" type="text" />
        </div>
        <div>
          <label for="section">Section</label>
          <input id="section" formControlName="section" type="text" />
        </div>
        <button type="submit" [disabled]="form.invalid">Create</button>
      </form>
    </main>
  `,
})
export class CreateCourse {
  private courseService = inject(CourseService);
  private router = inject(Router);
  private fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', Validators.required],
    term: ['', Validators.required],
    section: ['', Validators.required],
  });

  protected onSubmit(): void {
    if (this.form.invalid) {
      return;
    }
    const { name, term, section } = this.form.getRawValue();
    this.courseService
      .createCourse({ name, term, section })
      .then((course) => this.router.navigate(['/courses', course.id]));
  }
}
