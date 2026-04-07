/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { authGuard, landingGuard } from './auth.guard';
import { AuthService } from './auth.service';

function setup(authenticated: boolean) {
  const mockAuth = {
    isAuthenticated: signal(authenticated),
    whenReady: vi.fn().mockResolvedValue(undefined),
  };

  TestBed.configureTestingModule({
    providers: [
      provideRouter([
        { path: '', component: class {} as never },
        { path: 'courses', component: class {} as never },
        { path: 'protected', canActivate: [authGuard], component: class {} as never },
      ]),
      { provide: AuthService, useValue: mockAuth },
    ],
  });

  return { router: TestBed.inject(Router), mockAuth };
}

describe('authGuard', () => {
  it('should allow access when authenticated', async () => {
    setup(true);
    const result = await TestBed.runInInjectionContext(() =>
      authGuard({} as never, { url: '/protected' } as never),
    );
    expect(result).toBe(true);
  });

  it('should redirect to landing when not authenticated', async () => {
    const { router } = setup(false);
    const result = await TestBed.runInInjectionContext(() =>
      authGuard({} as never, { url: '/protected' } as never),
    );
    expect(result).toEqual(router.createUrlTree(['/']));
  });
});

describe('landingGuard', () => {
  it('should redirect authenticated users to courses', async () => {
    const { router } = setup(true);
    const result = await TestBed.runInInjectionContext(() =>
      landingGuard({} as never, { url: '/' } as never),
    );
    expect(result).toEqual(router.createUrlTree(['/courses']));
  });

  it('should allow unauthenticated users to see landing', async () => {
    setup(false);
    const result = await TestBed.runInInjectionContext(() =>
      landingGuard({} as never, { url: '/' } as never),
    );
    expect(result).toBe(true);
  });
});
