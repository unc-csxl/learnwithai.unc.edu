/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { PageTitleService } from '../../../../../page-title.service';
import { SuccessSnackbarService } from '../../../../../success-snackbar.service';
import { LayoutNavigationService } from '../../../../../layout/layout-navigation.service';
import { ActivityService } from '../../activity.service';
import { ACTIVITY_TYPE_OPTIONS } from '../../activity-types';

/** Form for instructors to create an In Your Own Words activity. */
@Component({
  selector: 'app-create-iyow',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './create-iyow.component.html',
})
export class CreateIyow {
  private activityService = inject(ActivityService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private titleService = inject(PageTitleService);
  private successSnackbar = inject(SuccessSnackbarService);
  private layoutNavigation = inject(LayoutNavigationService);

  protected readonly courseId: number;
  protected readonly activityType =
    ACTIVITY_TYPE_OPTIONS.find((activityType) =>
      this.route.routeConfig?.path?.endsWith(activityType.routeSegment),
    ) ?? ACTIVITY_TYPE_OPTIONS[0];
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');

  protected readonly form = this.fb.nonNullable.group({
    title: ['', [Validators.required]],
    prompt: ['', [Validators.required]],
    rubric: ['', [Validators.required]],
    release_date: ['', [Validators.required]],
    due_date: ['', [Validators.required]],
    late_date: [''],
  });

  constructor() {
    this.titleService.setTitle(`Create ${this.activityType.label}`);
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.layoutNavigation.setContextSection({
      visibleBaseRoutes: [
        `/courses/${this.courseId}/dashboard`,
        `/courses/${this.courseId}/activities`,
      ],
      groups: [
        {
          label: 'Choose activity type',
          items: [
            {
              route: `/courses/${this.courseId}/activities/create`,
              label: 'Choose Activity Type',
              description: 'Select the type of activity you want to create',
              icon: 'list',
            },
            {
              route: `/courses/${this.courseId}/activities/create/${this.activityType.routeSegment}`,
              label: `Create ${this.activityType.label}`,
              description: this.activityType.description,
              icon: 'add_circle',
            },
          ],
        },
      ],
    });
  }

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) return;

    this.submitting.set(true);
    this.errorMessage.set('');
    try {
      const values = this.form.getRawValue();
      await this.activityService.createIyow(this.courseId, {
        title: values.title,
        prompt: values.prompt,
        rubric: values.rubric,
        release_date: values.release_date,
        due_date: values.due_date,
        late_date: values.late_date || null,
      });
      this.successSnackbar.open('IYOW activity created!');
      await this.router.navigate(['courses', this.courseId, 'activities']);
    } catch {
      this.errorMessage.set('Failed to create activity.');
    } finally {
      this.submitting.set(false);
    }
  }
}
