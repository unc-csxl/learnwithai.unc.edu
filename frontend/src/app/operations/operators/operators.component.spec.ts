/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { By } from '@angular/platform-browser';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Operators } from './operators.component';
import { OperationsService } from '../operations.service';
import { AuthService } from '../../auth.service';
import { PageTitleService } from '../../page-title.service';
import { of } from 'rxjs';
import { Operator } from '../../api/models';

const STUB_OPERATORS: Operator[] = [
  {
    user_pid: 111,
    user_name: 'Admin One',
    user_email: 'admin1@unc.edu',
    role: 'superadmin',
    permissions: ['manage_operators', 'impersonate'],
    created_at: '2026-01-01T00:00:00Z',
    created_by_pid: 111,
  },
];

function setup(
  opts: {
    operators?: Operator[];
    noOperator?: boolean;
    nullUser?: boolean;
  } = {},
) {
  const mockAdmin = {
    listOperators: vi.fn().mockResolvedValue(opts.operators ?? STUB_OPERATORS),
    updateOperatorRole: vi.fn().mockResolvedValue({}),
    revokeOperator: vi.fn().mockResolvedValue(undefined),
  };

  const mockAuth = {
    user: signal(
      opts.nullUser
        ? null
        : opts.noOperator
          ? { pid: 999, name: 'Op' }
          : {
              pid: 999,
              name: 'Op',
              operator: { role: 'superadmin', permissions: ['manage_operators'] },
            },
    ),
  };

  const mockDialog = { open: vi.fn().mockReturnValue({ afterClosed: () => of(true) }) };
  const mockSnackBar = { open: vi.fn() };
  const mockTitle = { setTitle: vi.fn() };

  TestBed.configureTestingModule({
    imports: [NoopAnimationsModule],
    providers: [
      { provide: OperationsService, useValue: mockAdmin },
      { provide: AuthService, useValue: mockAuth },
      { provide: MatDialog, useValue: mockDialog },
      { provide: MatSnackBar, useValue: mockSnackBar },
      { provide: PageTitleService, useValue: mockTitle },
    ],
  });

  const fixture = TestBed.createComponent(Operators);
  fixture.detectChanges();

  return {
    fixture,
    component: fixture.componentInstance,
    mockAdmin,
    mockDialog,
    mockSnackBar,
    mockTitle,
  };
}

async function setupLoaded(
  opts: {
    operators?: Operator[];
    noOperator?: boolean;
    nullUser?: boolean;
  } = {},
) {
  const result = setup(opts);
  await vi.waitFor(() => {
    expect(result.mockAdmin.listOperators).toHaveBeenCalled();
  });
  result.fixture.detectChanges();
  return result;
}

describe('Operators', () => {
  it('should set page title', () => {
    const { mockTitle } = setup();
    expect(mockTitle.setTitle).toHaveBeenCalledWith('Manage Operators');
  });

  it('should load operators on init', async () => {
    const { mockAdmin } = setup();
    await vi.waitFor(() => {
      expect(mockAdmin.listOperators).toHaveBeenCalled();
    });
  });

  it('should open grant dialog via Add Operator button', async () => {
    const { fixture, mockDialog } = await setupLoaded();
    const el: HTMLElement = fixture.nativeElement;
    const addButton = el.querySelector('.operators-actions button') as HTMLButtonElement;
    expect(addButton).toBeTruthy();
    addButton.click();
    expect(mockDialog.open).toHaveBeenCalled();
  });

  it('should update role via onRoleChange', async () => {
    const { fixture, mockAdmin, mockSnackBar } = await setupLoaded();
    const roleSelect = fixture.debugElement.query(By.css('.role-select mat-select'));
    expect(roleSelect).toBeTruthy();
    roleSelect.triggerEventHandler('selectionChange', { value: 'helpdesk' });
    await vi.waitFor(() => {
      expect(mockAdmin.updateOperatorRole).toHaveBeenCalledWith(111, 'helpdesk');
    });
    expect(mockSnackBar.open).toHaveBeenCalled();
  });

  it('should handle onRoleChange error', async () => {
    const { fixture, mockAdmin, mockSnackBar } = await setupLoaded();
    mockAdmin.updateOperatorRole.mockRejectedValue(new Error('fail'));
    const roleSelect = fixture.debugElement.query(By.css('.role-select mat-select'));
    roleSelect.triggerEventHandler('selectionChange', { value: 'helpdesk' });
    await vi.waitFor(() => {
      expect(mockSnackBar.open).toHaveBeenCalledWith('Failed to update role', undefined, {
        duration: 5000,
      });
    });
  });

  it('should revoke operator via delete button click', async () => {
    const { fixture, mockAdmin, mockSnackBar } = await setupLoaded();
    const el: HTMLElement = fixture.nativeElement;
    const deleteButton = el.querySelector(
      'button[matTooltip="Remove operator"]',
    ) as HTMLButtonElement;
    expect(deleteButton).toBeTruthy();
    deleteButton.click();
    await vi.waitFor(() => {
      expect(mockAdmin.revokeOperator).toHaveBeenCalledWith(111);
    });
    expect(mockSnackBar.open).toHaveBeenCalled();
  });

  it('should handle onRevoke error via delete button', async () => {
    const { fixture, mockAdmin, mockSnackBar } = await setupLoaded();
    mockAdmin.revokeOperator.mockRejectedValue(new Error('fail'));
    const el: HTMLElement = fixture.nativeElement;
    const deleteButton = el.querySelector(
      'button[matTooltip="Remove operator"]',
    ) as HTMLButtonElement;
    deleteButton.click();
    await vi.waitFor(() => {
      expect(mockSnackBar.open).toHaveBeenCalledWith('Failed to remove operator', undefined, {
        duration: 5000,
      });
    });
  });

  it('should show error message when loadOperators fails', async () => {
    const { fixture, mockAdmin } = setup();
    mockAdmin.listOperators.mockRejectedValue(new Error('fail'));
    const comp = fixture.componentInstance as unknown as {
      loadOperators: () => Promise<void>;
      errorMessage: () => string;
    };
    await comp.loadOperators();
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(comp.errorMessage()).toBe('Failed to load operators.');
    expect(el.querySelector('.error-message')?.textContent).toContain('Failed to load operators.');
  });

  it('should render table with operator data', async () => {
    const { fixture } = await setupLoaded();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('table')).toBeTruthy();
  });

  it('should default currentUserPid to 0 when user is null', async () => {
    const { fixture } = await setupLoaded({ nullUser: true });
    const el: HTMLElement = fixture.nativeElement;
    // All delete buttons should be visible since no operator matches pid 0
    const deleteButtons = el.querySelectorAll('button[matTooltip="Remove operator"]');
    expect(deleteButtons.length).toBe(1);
  });

  it('should hide delete button for current user', async () => {
    const selfOperator: Operator[] = [
      {
        user_pid: 999,
        user_name: 'Self',
        user_email: 'self@unc.edu',
        role: 'superadmin',
        permissions: ['manage_operators', 'impersonate'],
        created_at: '2026-01-01T00:00:00Z',
        created_by_pid: 111,
      },
    ];
    const { fixture } = await setupLoaded({ operators: selfOperator });
    const el: HTMLElement = fixture.nativeElement;
    const deleteButtons = el.querySelectorAll('button[matTooltip="Remove operator"]');
    expect(deleteButtons.length).toBe(0);
  });

  it('should not reload when dialog is dismissed without granting', async () => {
    const { fixture, mockDialog, mockAdmin } = await setupLoaded();
    mockDialog.open.mockReturnValue({ afterClosed: () => of(undefined) });
    mockAdmin.listOperators.mockClear();
    const el: HTMLElement = fixture.nativeElement;
    const addButton = el.querySelector('.operators-actions button') as HTMLButtonElement;
    addButton.click();
    expect(mockAdmin.listOperators).not.toHaveBeenCalled();
  });
});
