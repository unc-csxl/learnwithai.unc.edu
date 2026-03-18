import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { CourseService } from '../course.service';
import { MembershipType } from '../../api/models';

/** Form for adding a member to a course by PID and role. */
@Component({
  selector: 'app-add-member',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule],
  templateUrl: './add-member.component.html',
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

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) {
      return;
    }
    const { pid, type } = this.form.getRawValue();
    await this.courseService.addMember(this.courseId, { pid, type });
    await this.router.navigate(['/courses', this.courseId]);
  }
}
