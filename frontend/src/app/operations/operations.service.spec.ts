/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { OperationsService } from './operations.service';
import { Api } from '../api/generated/api';
import { ImpersonationService } from './impersonation.service';

describe('OperationsService', () => {
  function setup() {
    const mockApi = {
      invoke: vi.fn(),
    };
    const mockImpersonation = {
      startImpersonation: vi.fn().mockResolvedValue(undefined),
    };

    TestBed.configureTestingModule({
      providers: [
        OperationsService,
        { provide: Api, useValue: mockApi },
        { provide: ImpersonationService, useValue: mockImpersonation },
      ],
    });

    return {
      service: TestBed.inject(OperationsService),
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

  it('searchUsers calls api.invoke with query', async () => {
    const { service, mockApi } = setup();
    const results = [{ pid: 1, name: 'Alice', email: 'alice@unc.edu' }];
    mockApi.invoke.mockResolvedValue(results);
    const result = await service.searchUsers('alice');
    expect(result).toEqual(results);
    expect(mockApi.invoke).toHaveBeenCalledWith(expect.any(Function), { q: 'alice' });
  });

  it('getUsageMetrics calls api.invoke', async () => {
    const { service, mockApi } = setup();
    const metrics = {
      month_label: 'April 2026',
      active_users: 10,
      active_courses: 3,
      submissions: 50,
      jobs_run: 20,
    };
    mockApi.invoke.mockResolvedValue(metrics);
    const result = await service.getUsageMetrics();
    expect(result).toEqual(metrics);
    expect(mockApi.invoke).toHaveBeenCalled();
  });
});
