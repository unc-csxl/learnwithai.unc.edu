import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { CourseService } from '../course.service';
import { MembershipType } from '../../api/generated/models/membership-type';

/** Form for adding a member to a course by PID and role. */
@Component({
  selector: 'app-add-member',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule],
  template: `
    <main>
      <h1>Add Member</h1>
      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div>
          <label for="pid">PID</label>
          <input id="pid" formControlName="pid" type="number" inputmode="numeric" />
        </div>
        <div>
          <label for="type">Role</label>
          <select id="type" formControlName="type">
            <option value="student">Student</option>
            <option value="ta">TA</option>
          </select>
        </div>
        <button type="submit" [disabled]="form.invalid">Add</button>
      </form>
    </main>
  `,
})
export class AddMember {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);

  private readonly courseId = Number(this.route.snapshot.paramMap.get('id'));

  protected readonly form = this.fb.nonNullable.group({
    pid: [0, [Validators.required, Validators.min(1)]],
    type: ['student' as MembershipType, Validators.required],
  });

  protected onSubmit(): void {
    if (this.form.invalid) {
      return;
    }
    const { pid, type } = this.form.getRawValue();
    this.courseService.addMember(this.courseId, { pid, type }).subscribe({
      next: () => this.router.navigate(['/courses', this.courseId]),
    });
  }
}
