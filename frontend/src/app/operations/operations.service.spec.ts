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

  it('getJobsOverview calls api.invoke', async () => {
    const { service, mockApi } = setup();
    const overview = { total_queued: 5 };
    mockApi.invoke.mockResolvedValue(overview);
    const result = await service.getJobsOverview();
    expect(result).toEqual(overview);
    expect(mockApi.invoke).toHaveBeenCalled();
  });

  it('getJobsQueues calls api.invoke', async () => {
    const { service, mockApi } = setup();
    const queues = [{ name: 'default' }];
    mockApi.invoke.mockResolvedValue(queues);
    const result = await service.getJobsQueues();
    expect(result).toEqual(queues);
    expect(mockApi.invoke).toHaveBeenCalled();
  });

  it('getJobsWorkers calls api.invoke', async () => {
    const { service, mockApi } = setup();
    const workers = [{ consumer_tag: 'w.1' }];
    mockApi.invoke.mockResolvedValue(workers);
    const result = await service.getJobsWorkers();
    expect(result).toEqual(workers);
    expect(mockApi.invoke).toHaveBeenCalled();
  });

  it('getJobsFailures calls api.invoke', async () => {
    const { service, mockApi } = setup();
    const failures = { dlq_messages: 0 };
    mockApi.invoke.mockResolvedValue(failures);
    const result = await service.getJobsFailures();
    expect(result).toEqual(failures);
    expect(mockApi.invoke).toHaveBeenCalled();
  });

  it('purgeQueue calls api.invoke with queue name', async () => {
    const { service, mockApi } = setup();
    mockApi.invoke.mockResolvedValue(undefined);
    await service.purgeQueue('default');
    expect(mockApi.invoke).toHaveBeenCalledWith(expect.any(Function), { queue_name: 'default' });
  });
});
