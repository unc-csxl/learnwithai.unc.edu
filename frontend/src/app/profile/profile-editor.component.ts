/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../auth.service';
import { PageTitleService } from '../page-title.service';
import { SuccessSnackbarService } from '../success-snackbar.service';

/** Form for editing the authenticated user's profile. */
@Component({
  selector: 'app-profile-editor',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  templateUrl: './profile-editor.component.html',
})
export class ProfileEditor {
  private auth = inject(AuthService);
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private titleService = inject(PageTitleService);
  private successSnackbar = inject(SuccessSnackbarService);

  protected readonly user = this.auth.user;
  protected readonly saving = signal(false);
  protected readonly errorMessage = signal('');

  protected readonly form = this.fb.nonNullable.group({
    given_name: [this.user()?.given_name ?? '', Validators.required],
    family_name: [this.user()?.family_name ?? '', Validators.required],
  });

  constructor() {
    this.titleService.setTitle('Profile');
  }

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) {
      return;
    }
    this.saving.set(true);
    const raw = this.form.getRawValue();
    try {
      await this.auth.updateProfile({
        given_name: raw.given_name,
        family_name: raw.family_name,
      });
      this.successSnackbar.open('Profile updated.');
      await this.router.navigate(['/courses']);
    } catch {
      this.saving.set(false);
      this.errorMessage.set('Failed to save profile.');
    }
  }
}
