/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { GrantOperatorDialog } from './grant-operator-dialog.component';
import { OperationsService } from '../operations.service';

describe('GrantOperatorDialog', () => {
  function setup() {
    const mockAdmin = {
      grantOperator: vi.fn().mockResolvedValue({ user_pid: 123 }),
    };
    const mockDialogRef = {
      close: vi.fn(),
    };
    const mockSnackBar = {
      open: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [
        { provide: OperationsService, useValue: mockAdmin },
        { provide: MatDialogRef, useValue: mockDialogRef },
        { provide: MatSnackBar, useValue: mockSnackBar },
      ],
    });

    const fixture = TestBed.createComponent(GrantOperatorDialog);
    fixture.detectChanges();

    return {
      fixture,
      component: fixture.componentInstance,
      mockAdmin,
      mockDialogRef,
      mockSnackBar,
    };
  }

  it('should create the dialog', () => {
    const { component } = setup();
    expect(component).toBeTruthy();
  });

  it('should render form fields', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('input[formControlName="pid"]')).toBeTruthy();
    expect(el.querySelector('mat-select[formControlName="role"]')).toBeTruthy();
  });

  it('should disable submit button when form is invalid', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const button = el.querySelector('button[disabled]') as HTMLButtonElement;
    expect(button?.textContent).toContain('Grant Access');
  });

  it('should call grantOperator and close on successful submit', async () => {
    const { fixture, mockAdmin, mockDialogRef, mockSnackBar } = setup();
    const component = fixture.componentInstance as unknown as {
      form: {
        value: { pid: number; role: string };
        invalid: boolean;
        patchValue: (v: unknown) => void;
      };
    };

    component.form.patchValue({ pid: 123, role: 'admin' });
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const submitButton = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Grant Access'),
    ) as HTMLButtonElement;
    submitButton.click();
    await vi.waitFor(() => {
      expect(mockAdmin.grantOperator).toHaveBeenCalledWith(123, 'admin');
    });
    expect(mockSnackBar.open).toHaveBeenCalled();
    expect(mockDialogRef.close).toHaveBeenCalledWith(true);
  });

  it('should show error message on failure', async () => {
    const { fixture, mockAdmin } = setup();
    mockAdmin.grantOperator.mockRejectedValue({ error: { detail: 'Already exists' } });

    const component = fixture.componentInstance as unknown as {
      form: { patchValue: (v: unknown) => void };
      submit: () => Promise<void>;
      errorMessage: () => string;
    };

    component.form.patchValue({ pid: 456, role: 'helpdesk' });
    fixture.detectChanges();

    await component.submit();
    fixture.detectChanges();

    expect(component.errorMessage()).toBe('Already exists');
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.error')?.textContent).toContain('Already exists');
  });

  it('should show fallback error message when error has no detail', async () => {
    const { fixture, mockAdmin } = setup();
    mockAdmin.grantOperator.mockRejectedValue(new Error('network'));

    const component = fixture.componentInstance as unknown as {
      form: { patchValue: (v: unknown) => void };
      submit: () => Promise<void>;
      errorMessage: () => string;
    };

    component.form.patchValue({ pid: 789, role: 'admin' });
    fixture.detectChanges();

    await component.submit();
    fixture.detectChanges();

    expect(component.errorMessage()).toBe('Failed to grant operator access');
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.error')?.textContent).toContain('Failed to grant operator access');
  });

  it('should not show error message initially', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.error')).toBeNull();
  });

  it('should not submit when form is invalid', async () => {
    const { mockAdmin } = setup();
    // form starts invalid (no pid)
    const fixture = TestBed.createComponent(GrantOperatorDialog);
    fixture.detectChanges();
    const component = fixture.componentInstance as unknown as {
      submit: () => Promise<void>;
    };

    await component.submit();
    expect(mockAdmin.grantOperator).not.toHaveBeenCalled();
  });

  it('should close dialog when cancel button is clicked', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const cancelButton = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Cancel'),
    ) as HTMLButtonElement;
    expect(cancelButton).toBeTruthy();
    cancelButton.click();
  });
  it('should disable submit button while submitting', async () => {
    const { fixture, mockAdmin } = setup();
    let resolveGrant!: (v: unknown) => void;
    mockAdmin.grantOperator.mockReturnValue(
      new Promise((r) => {
        resolveGrant = r;
      }),
    );

    const component = fixture.componentInstance as unknown as {
      form: { patchValue: (v: unknown) => void };
      submit: () => Promise<void>;
      submitting: () => boolean;
    };

    component.form.patchValue({ pid: 456, role: 'admin' });
    fixture.detectChanges();

    const submitPromise = component.submit();
    fixture.detectChanges();
    expect(component.submitting()).toBe(true);

    resolveGrant({});
    await submitPromise;
    fixture.detectChanges();
    expect(component.submitting()).toBe(false);
  });
});
