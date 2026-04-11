/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ConfirmPurgeDialogComponent } from './confirm-purge-dialog.component';

describe('ConfirmPurgeDialogComponent', () => {
  function setup() {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: { queueName: 'default' } },
        { provide: MatDialogRef, useValue: {} },
      ],
    });

    const fixture = TestBed.createComponent(ConfirmPurgeDialogComponent);
    fixture.detectChanges();
    return { fixture };
  }

  it('should create the dialog', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should display the queue name', () => {
    const { fixture } = setup();
    const content = fixture.nativeElement.textContent;
    expect(content).toContain('default');
  });

  it('should have cancel and purge buttons', () => {
    const { fixture } = setup();
    const buttons = fixture.nativeElement.querySelectorAll('button');
    expect(buttons.length).toBe(2);
    expect(buttons[0].textContent).toContain('Cancel');
    expect(buttons[1].textContent).toContain('Purge');
  });
});
