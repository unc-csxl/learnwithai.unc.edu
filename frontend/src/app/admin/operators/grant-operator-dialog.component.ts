/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AdminService } from '../admin.service';
import { OperatorRole } from '../../api/models';

/** Dialog for granting operator access to an existing user. */
@Component({
  selector: 'app-grant-operator-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
  ],
  templateUrl: './grant-operator-dialog.component.html',
  styleUrl: './grant-operator-dialog.component.scss',
})
export class GrantOperatorDialog {
  private adminService = inject(AdminService);
  private dialogRef = inject(MatDialogRef<GrantOperatorDialog>);
  private snackBar = inject(MatSnackBar);

  protected readonly availableRoles: OperatorRole[] = ['superadmin', 'admin', 'helpdesk'];
  protected readonly errorMessage = signal('');
  protected readonly submitting = signal(false);

  protected readonly form = new FormGroup({
    pid: new FormControl<number | null>(null, [Validators.required]),
    role: new FormControl<OperatorRole>('admin', [Validators.required]),
  });

  protected async submit(): Promise<void> {
    if (this.form.invalid) return;
    const pid = this.form.value.pid!;
    const role = this.form.value.role!;

    this.submitting.set(true);
    this.errorMessage.set('');
    try {
      await this.adminService.grantOperator(pid, role);
      this.snackBar.open('Operator access granted', undefined, { duration: 3000 });
      this.dialogRef.close(true);
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'error' in err
          ? String((err as { error: { detail: string } }).error.detail)
          : 'Failed to grant operator access';
      this.errorMessage.set(message);
    } finally {
      this.submitting.set(false);
    }
  }
}
