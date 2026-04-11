/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { operationsGuard } from './operations.guard';
import { AuthService } from './auth.service';

function setup(operator: { role: string; permissions: string[] } | null) {
  const mockAuth = {
    isAuthenticated: signal(!!operator),
    user: signal(operator ? { name: 'Test', operator } : { name: 'Test' }),
    whenReady: vi.fn().mockResolvedValue(undefined),
  };

  TestBed.configureTestingModule({
    providers: [
      provideRouter([
        { path: 'operations', canActivate: [operationsGuard], component: class {} as never },
        { path: 'courses', component: class {} as never },
      ]),
      { provide: AuthService, useValue: mockAuth },
    ],
  });

  return { router: TestBed.inject(Router), mockAuth };
}

describe('operationsGuard', () => {
  it('should allow access for operators', async () => {
    setup({ role: 'admin', permissions: ['manage_operators'] });
    const result = await TestBed.runInInjectionContext(() =>
      operationsGuard({} as never, { url: '/operations' } as never),
    );
    expect(result).toBe(true);
  });

  it('should redirect non-operators to courses', async () => {
    const { router } = setup(null);
    const result = await TestBed.runInInjectionContext(() =>
      operationsGuard({} as never, { url: '/operations' } as never),
    );
    expect(result).toEqual(router.createUrlTree(['/courses']));
  });
});
