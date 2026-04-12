/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { ImpersonationService } from './impersonation.service';
import { AuthService } from '../auth.service';
import { AuthTokenService } from '../auth-token.service';
import { Router } from '@angular/router';

describe('ImpersonationService', () => {
  function setup(originalTokenInStorage = false) {
    if (originalTokenInStorage) {
      localStorage.setItem('impersonation_original_token', 'original-jwt');
    } else {
      localStorage.removeItem('impersonation_original_token');
    }

    const mockAuth = {
      fetchProfile: vi.fn().mockResolvedValue(undefined),
    };
    const mockTokenService = {
      getToken: vi.fn().mockReturnValue('current-jwt'),
      setToken: vi.fn(),
    };
    const mockRouter = {
      navigate: vi.fn().mockResolvedValue(true),
    };

    TestBed.configureTestingModule({
      providers: [
        ImpersonationService,
        { provide: AuthService, useValue: mockAuth },
        { provide: AuthTokenService, useValue: mockTokenService },
        { provide: Router, useValue: mockRouter },
      ],
    });

    return {
      service: TestBed.inject(ImpersonationService),
      mockAuth,
      mockTokenService,
      mockRouter,
    };
  }

  afterEach(() => {
    localStorage.removeItem('impersonation_original_token');
  });

  it('should report not impersonating when no stored token', () => {
    const { service } = setup(false);
    expect(service.isImpersonating()).toBe(false);
  });

  it('should report impersonating when stored token exists', () => {
    const { service } = setup(true);
    expect(service.isImpersonating()).toBe(true);
  });

  it('startImpersonation should save current token and set new one', async () => {
    const { service, mockTokenService, mockRouter } = setup(false);
    await service.startImpersonation('new-impersonation-jwt');

    expect(localStorage.getItem('impersonation_original_token')).toBe('current-jwt');
    expect(mockTokenService.setToken).toHaveBeenCalledWith('new-impersonation-jwt');
    expect(service.isImpersonating()).toBe(true);
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/courses']);
  });

  it('stopImpersonation should restore original token', async () => {
    const { service, mockTokenService, mockRouter } = setup(true);
    await service.stopImpersonation();

    expect(localStorage.getItem('impersonation_original_token')).toBeNull();
    expect(mockTokenService.setToken).toHaveBeenCalledWith('original-jwt');
    expect(service.isImpersonating()).toBe(false);
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/operations']);
  });

  it('startImpersonation should skip saving when no current token', async () => {
    const { service, mockTokenService, mockRouter } = setup(false);
    mockTokenService.getToken.mockReturnValue(null);
    await service.startImpersonation('new-jwt');

    expect(localStorage.getItem('impersonation_original_token')).toBeNull();
    expect(mockTokenService.setToken).toHaveBeenCalledWith('new-jwt');
    expect(service.isImpersonating()).toBe(true);
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/courses']);
  });

  it('stopImpersonation should handle missing original token', async () => {
    const { service, mockTokenService, mockRouter } = setup(false);
    await service.stopImpersonation();

    expect(mockTokenService.setToken).not.toHaveBeenCalled();
    expect(service.isImpersonating()).toBe(false);
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/operations']);
  });
});
