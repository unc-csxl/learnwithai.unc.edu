/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { ImpersonationBanner } from './impersonation-banner.component';
import { ImpersonationService } from '../impersonation.service';
import { AuthService } from '../../auth.service';

describe('ImpersonationBanner', () => {
  function setup() {
    const mockImpersonation = {
      isImpersonating: signal(true),
      stopImpersonation: vi.fn().mockResolvedValue(undefined),
    };
    const mockAuth = {
      user: signal({ name: 'Impersonated User', pid: 123 }),
    };

    TestBed.configureTestingModule({
      providers: [
        { provide: ImpersonationService, useValue: mockImpersonation },
        { provide: AuthService, useValue: mockAuth },
      ],
    });

    const fixture = TestBed.createComponent(ImpersonationBanner);
    fixture.detectChanges();

    return { fixture, mockImpersonation, mockAuth };
  }

  it('should display user name and PID', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Impersonated User');
    expect(el.textContent).toContain('123');
  });

  it('should call stopImpersonation on button click', () => {
    const { fixture, mockImpersonation } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const button = el.querySelector('button') as HTMLButtonElement;
    expect(button).toBeTruthy();
    button.click();
    expect(mockImpersonation.stopImpersonation).toHaveBeenCalled();
  });

  it('should handle null user gracefully', () => {
    const mockImpersonation = {
      isImpersonating: signal(true),
      stopImpersonation: vi.fn(),
    };
    const mockAuth = {
      user: signal(null),
    };

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        { provide: ImpersonationService, useValue: mockImpersonation },
        { provide: AuthService, useValue: mockAuth },
      ],
    });

    const fixture = TestBed.createComponent(ImpersonationBanner);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.impersonation-banner')).toBeTruthy();
  });
});
