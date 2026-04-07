/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RosterUploadResultDialog } from './roster-upload-result-dialog.component';
import { RosterUploadStatus } from '../../../api/models';

describe('RosterUploadResultDialog', () => {
  function setup(data: RosterUploadStatus) {
    TestBed.configureTestingModule({
      imports: [RosterUploadResultDialog, NoopAnimationsModule],
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: data },
        { provide: MatDialogRef, useValue: { close: vi.fn() } },
      ],
    });

    const fixture = TestBed.createComponent(RosterUploadResultDialog);
    fixture.detectChanges();
    return { fixture };
  }

  it('should show created and updated counts for completed upload', () => {
    const { fixture } = setup({
      id: 1,
      status: 'completed',
      created_count: 5,
      updated_count: 3,
      error_count: 0,
      error_details: null,
      created_at: '2025-01-01T00:00:00',
      completed_at: '2025-01-01T00:00:05',
    });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Created');
    expect(el.textContent).toContain('5');
    expect(el.textContent).toContain('Updated');
    expect(el.textContent).toContain('3');
  });

  it('should show error details when errors exist', () => {
    const { fixture } = setup({
      id: 1,
      status: 'completed',
      created_count: 3,
      updated_count: 1,
      error_count: 2,
      error_details: 'Row 3: invalid PID\nRow 5: missing name',
      created_at: '2025-01-01T00:00:00',
      completed_at: '2025-01-01T00:00:05',
    });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Errors');
    expect(el.textContent).toContain('2');
    expect(el.textContent).toContain('Row 3: invalid PID');
    expect(el.textContent).toContain('Row 5: missing name');
  });

  it('should not show error section when error_count is 0', () => {
    const { fixture } = setup({
      id: 1,
      status: 'completed',
      created_count: 5,
      updated_count: 3,
      error_count: 0,
      error_details: null,
      created_at: '2025-01-01T00:00:00',
      completed_at: '2025-01-01T00:00:05',
    });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).not.toContain('Errors');
    expect(el.querySelector('.error-details')).toBeNull();
  });

  it('should show failure message for failed upload', () => {
    const { fixture } = setup({
      id: 1,
      status: 'failed',
      created_count: 0,
      updated_count: 0,
      error_count: 0,
      error_details: 'Internal error',
      created_at: '2025-01-01T00:00:00',
      completed_at: null,
    });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('upload failed');
    expect(el.textContent).toContain('Internal error');
  });

  it('should show failure message without error details', () => {
    const { fixture } = setup({
      id: 1,
      status: 'failed',
      created_count: 0,
      updated_count: 0,
      error_count: 0,
      error_details: null,
      created_at: '2025-01-01T00:00:00',
      completed_at: null,
    });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('upload failed');
    expect(el.querySelector('.error-details')).toBeNull();
  });

  it('should have a close button', () => {
    const { fixture } = setup({
      id: 1,
      status: 'completed',
      created_count: 0,
      updated_count: 0,
      error_count: 0,
      error_details: null,
      created_at: '2025-01-01T00:00:00',
      completed_at: '2025-01-01T00:00:05',
    });
    const el: HTMLElement = fixture.nativeElement;
    const closeBtn = el.querySelector('button');
    expect(closeBtn?.textContent).toContain('Close');
  });
});
