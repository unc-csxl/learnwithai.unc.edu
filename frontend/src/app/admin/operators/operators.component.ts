/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, signal, computed } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AuthService } from '../../auth.service';
import { AdminService } from '../admin.service';
import { PageTitleService } from '../../page-title.service';
import { Operator, OperatorRole } from '../../api/models';
import { GrantOperatorDialog } from './grant-operator-dialog.component';

/** Lists and manages system operators. */
@Component({
  selector: 'app-operators',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatSelectModule,
    MatFormFieldModule,
    MatTooltipModule,
  ],
  templateUrl: './operators.component.html',
  styleUrl: './operators.component.scss',
})
export class Operators {
  private auth = inject(AuthService);
  private adminService = inject(AdminService);
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);
  private titleService = inject(PageTitleService);

  protected readonly operators = signal<Operator[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');
  protected readonly displayedColumns = ['name', 'pid', 'role', 'permissions', 'actions'];
  protected readonly availableRoles: OperatorRole[] = ['superadmin', 'admin', 'helpdesk'];

  protected readonly currentUserPid = computed(() => {
    const user = this.auth.user();
    return user ? user.pid : 0;
  });
  protected readonly canImpersonate = computed(() => {
    const user = this.auth.user();
    if (!user?.operator) return false;
    return user.operator.permissions.includes('impersonate');
  });

  constructor() {
    this.titleService.setTitle('Manage Operators');
    this.loadOperators();
  }

  protected openGrantDialog(): void {
    const dialogRef = this.dialog.open(GrantOperatorDialog, {
      width: '400px',
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.loadOperators();
      }
    });
  }

  protected async onRoleChange(op: Operator, newRole: OperatorRole): Promise<void> {
    try {
      await this.adminService.updateOperatorRole(op.user_pid, newRole);
      this.snackBar.open('Role updated', undefined, { duration: 3000 });
      await this.loadOperators();
    } catch {
      this.snackBar.open('Failed to update role', undefined, { duration: 5000 });
    }
  }

  protected async onRevoke(op: Operator): Promise<void> {
    try {
      await this.adminService.revokeOperator(op.user_pid);
      this.snackBar.open(`${op.user_name} removed as operator`, undefined, { duration: 3000 });
      await this.loadOperators();
    } catch {
      this.snackBar.open('Failed to remove operator', undefined, { duration: 5000 });
    }
  }

  protected async onImpersonate(pid: number): Promise<void> {
    try {
      await this.adminService.impersonate(pid);
    } catch {
      this.snackBar.open('Failed to start impersonation', undefined, { duration: 5000 });
    }
  }

  private async loadOperators(): Promise<void> {
    this.loading.set(true);
    this.errorMessage.set('');
    try {
      const ops = await this.adminService.listOperators();
      this.operators.set(ops);
    } catch {
      this.errorMessage.set('Failed to load operators.');
    } finally {
      this.loading.set(false);
    }
  }
}
