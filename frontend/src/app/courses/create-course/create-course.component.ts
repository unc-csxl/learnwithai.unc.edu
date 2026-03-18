import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { CourseService } from '../course.service';

/** Form for creating a new course. */
@Component({
  selector: 'app-create-course',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  templateUrl: './create-course.component.html',
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

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) {
      return;
    }
    const { name, term, section } = this.form.getRawValue();
    const course = await this.courseService.createCourse({ name, term, section });
    await this.router.navigate(['/courses', course.id]);
  }
}
