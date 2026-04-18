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
import { buildActivityContextNav } from '../../activity-nav';
import { activityDetailRouteParts } from '../../activity-types';
import { IyowActivity } from '../../../../../api/models';

/** Form for instructors to edit an existing In Your Own Words activity. */
@Component({
  selector: 'app-edit-iyow',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './edit-iyow.component.html',
})
export class EditIyow {
  private activityService = inject(ActivityService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private titleService = inject(PageTitleService);
  private successSnackbar = inject(SuccessSnackbarService);
  private layoutNavigation = inject(LayoutNavigationService);

  protected readonly courseId: number;
  protected readonly activityId: number;
  protected readonly loaded = signal(false);
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
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.activityId = Number(this.route.snapshot.paramMap.get('activityId'));
    this.titleService.setTitle('Edit Activity');
    this.loadActivity();
  }

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) return;

    this.submitting.set(true);
    this.errorMessage.set('');
    try {
      const values = this.form.getRawValue();
      const activity = await this.activityService.updateIyow(this.courseId, this.activityId, {
        title: values.title,
        prompt: values.prompt,
        rubric: values.rubric,
        release_date: values.release_date,
        due_date: values.due_date,
        late_date: values.late_date || null,
      });
      this.successSnackbar.open('Activity updated!');
      await this.router.navigate([
        'courses',
        this.courseId,
        'activities',
        ...activityDetailRouteParts(activity.type, this.activityId),
      ]);
    } catch {
      this.errorMessage.set('Failed to update activity.');
    } finally {
      this.submitting.set(false);
    }
  }

  private async loadActivity(): Promise<void> {
    try {
      const activity = await this.activityService.getIyow(this.courseId, this.activityId);
      this.populateForm(activity);
      this.titleService.setTitle(`Edit: ${activity.title}`);
      this.layoutNavigation.setContextSection(
        buildActivityContextNav({
          courseId: this.courseId,
          activityId: this.activityId,
          activityType: activity.type,
          role: 'staff',
        }),
      );
    } catch {
      this.errorMessage.set('Failed to load activity.');
      this.layoutNavigation.clearContext();
    } finally {
      this.loaded.set(true);
    }
  }

  private populateForm(activity: IyowActivity): void {
    this.form.patchValue({
      title: activity.title,
      prompt: activity.prompt,
      rubric: activity.rubric ?? '',
      release_date: this.toDatetimeLocal(activity.release_date),
      due_date: this.toDatetimeLocal(activity.due_date),
      late_date: activity.late_date ? this.toDatetimeLocal(activity.late_date) : '',
    });
  }

  private toDatetimeLocal(iso: string): string {
    const d = new Date(iso);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }
}
