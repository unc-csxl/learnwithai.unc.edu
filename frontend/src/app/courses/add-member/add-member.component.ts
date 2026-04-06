import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { CourseService } from '../course.service';
import { MembershipType } from '../../api/models';
import { PageTitleService } from '../../page-title.service';
import { LayoutNavigationService } from '../../layout/layout-navigation.service';

/** Form for adding a member to a course by PID and role. */
@Component({
  selector: 'app-add-member',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
  ],
  templateUrl: './add-member.component.html',
})
export class AddMember {
  private courseService = inject(CourseService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private titleService = inject(PageTitleService);
  private layoutNavigation = inject(LayoutNavigationService);

  private readonly courseId = Number(this.route.parent?.snapshot.paramMap.get('id'));

  constructor() {
    this.layoutNavigation.clearContext();
    this.titleService.setTitle('Add Member');
  }

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
    await this.router.navigate(['../roster'], { relativeTo: this.route });
  }
}
