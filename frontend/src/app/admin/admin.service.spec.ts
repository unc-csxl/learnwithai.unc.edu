/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AdminService } from './admin.service';
import { Api } from '../api/generated/api';
import { ImpersonationService } from './impersonation.service';

describe('AdminService', () => {
  function setup() {
    const mockApi = {
      invoke: vi.fn(),
    };
    const mockImpersonation = {
      startImpersonation: vi.fn().mockResolvedValue(undefined),
    };

    TestBed.configureTestingModule({
      providers: [
        AdminService,
        { provide: Api, useValue: mockApi },
        { provide: ImpersonationService, useValue: mockImpersonation },
      ],
    });

    return {
      service: TestBed.inject(AdminService),
      mockApi,
      mockImpersonation,
    };
  }

  it('listOperators calls api.invoke', async () => {
    const { service, mockApi } = setup();
    const operators = [{ user_pid: 1 }];
    mockApi.invoke.mockResolvedValue(operators);
    const result = await service.listOperators();
    expect(result).toEqual(operators);
    expect(mockApi.invoke).toHaveBeenCalled();
  });

  it('grantOperator calls api.invoke with body', async () => {
    const { service, mockApi } = setup();
    mockApi.invoke.mockResolvedValue({ user_pid: 123 });
    await service.grantOperator(123, 'admin');
    expect(mockApi.invoke).toHaveBeenCalledWith(expect.any(Function), {
      body: { user_pid: 123, role: 'admin' },
    });
  });

  it('updateOperatorRole calls api.invoke with pid and body', async () => {
    const { service, mockApi } = setup();
    mockApi.invoke.mockResolvedValue({ user_pid: 123 });
    await service.updateOperatorRole(123, 'helpdesk');
    expect(mockApi.invoke).toHaveBeenCalledWith(expect.any(Function), {
      pid: 123,
      body: { role: 'helpdesk' },
    });
  });

  it('revokeOperator calls api.invoke with pid', async () => {
    const { service, mockApi } = setup();
    mockApi.invoke.mockResolvedValue(undefined);
    await service.revokeOperator(123);
    expect(mockApi.invoke).toHaveBeenCalledWith(expect.any(Function), { pid: 123 });
  });

  it('impersonate delegates to ImpersonationService', async () => {
    const { service, mockApi, mockImpersonation } = setup();
    mockApi.invoke.mockResolvedValue({ token: 'imp-jwt' });
    await service.impersonate(999);
    expect(mockImpersonation.startImpersonation).toHaveBeenCalledWith('imp-jwt');
  });
});
