/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { Jwt } from './jwt.component';
import { AuthService } from '../auth.service';

describe('Jwt', () => {
  async function setup(queryParams: Record<string, string>) {
    const mockAuth = {
      handleToken: vi.fn().mockResolvedValue(undefined),
    };
    const mockRoute = {
      snapshot: {
        queryParamMap: {
          get: (key: string) => queryParams[key] ?? null,
        },
      },
    };
    const mockRouter = {
      navigate: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Jwt],
      providers: [
        { provide: AuthService, useValue: mockAuth },
        { provide: ActivatedRoute, useValue: mockRoute },
        { provide: Router, useValue: mockRouter },
      ],
    });

    const fixture = TestBed.createComponent(Jwt);
    fixture.detectChanges();
    await fixture.whenStable();
    return { fixture, mockAuth, mockRouter };
  }

  it('should handle token from query params and navigate to courses', async () => {
    const { mockAuth, mockRouter } = await setup({ token: 'my-jwt-token' });
    expect(mockAuth.handleToken).toHaveBeenCalledWith('my-jwt-token');
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/courses']);
  });

  it('should navigate to courses without calling handleToken when no token', async () => {
    const { mockAuth, mockRouter } = await setup({});
    expect(mockAuth.handleToken).not.toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/courses']);
  });

  it('should show authenticating message', async () => {
    const { fixture } = await setup({ token: 'test' });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Authenticating...');
  });
});
