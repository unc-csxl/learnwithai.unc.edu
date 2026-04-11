/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Injectable, inject } from '@angular/core';
import { Api } from '../api/generated/api';
import { listOperators } from '../api/generated/fn/operations/list-operators';
import { grantOperator } from '../api/generated/fn/operations/grant-operator';
import { updateOperatorRole } from '../api/generated/fn/operations/update-operator-role';
import { revokeOperator } from '../api/generated/fn/operations/revoke-operator';
import { impersonateUser } from '../api/generated/fn/operations/impersonate-user';
import { searchUsers } from '../api/generated/fn/operations/search-users';
import { getUsageMetrics } from '../api/generated/fn/operations/get-usage-metrics';
import { getJobsOverview } from '../api/generated/fn/operations/get-jobs-overview';
import { getJobsQueues } from '../api/generated/fn/operations/get-jobs-queues';
import { getJobsWorkers } from '../api/generated/fn/operations/get-jobs-workers';
import { getJobsFailures } from '../api/generated/fn/operations/get-jobs-failures';
import { purgeQueue } from '../api/generated/fn/operations/purge-queue';
import {
  Operator,
  OperatorRole,
  ImpersonationTokenResponse,
  UsageMetrics,
  UserSearchResult,
  JobControlOverview,
  QueueInfo,
  WorkerInfo,
  JobFailures,
} from '../api/models';
import { ImpersonationService } from './impersonation.service';

/** Wraps operations API calls for operator management and impersonation. */
@Injectable({ providedIn: 'root' })
export class OperationsService {
  private api = inject(Api);
  private impersonation = inject(ImpersonationService);

  /** Fetches all operator records. */
  async listOperators(): Promise<Operator[]> {
    return this.api.invoke(listOperators);
  }

  /** Grants operator access to a user. */
  async grantOperator(userPid: number, role: OperatorRole): Promise<Operator> {
    return this.api.invoke(grantOperator, {
      body: { user_pid: userPid, role },
    });
  }

  /** Updates the role of an existing operator. */
  async updateOperatorRole(pid: number, role: OperatorRole): Promise<Operator> {
    return this.api.invoke(updateOperatorRole, {
      pid,
      body: { role },
    });
  }

  /** Revokes operator access from a user. */
  async revokeOperator(pid: number): Promise<void> {
    return this.api.invoke(revokeOperator, { pid });
  }

  /** Impersonates a user by PID. */
  async impersonate(pid: number): Promise<void> {
    const response: ImpersonationTokenResponse = await this.api.invoke(impersonateUser, { pid });
    await this.impersonation.startImpersonation(response.token);
  }

  /** Searches users by name, PID, or email. */
  async searchUsers(query: string): Promise<UserSearchResult[]> {
    return this.api.invoke(searchUsers, { q: query });
  }

  /** Fetches monthly usage metrics. */
  async getUsageMetrics(): Promise<UsageMetrics> {
    return this.api.invoke(getUsageMetrics);
  }

  /** Fetches broker health overview. */
  async getJobsOverview(): Promise<JobControlOverview> {
    return this.api.invoke(getJobsOverview);
  }

  /** Fetches per-queue statistics. */
  async getJobsQueues(): Promise<QueueInfo[]> {
    return this.api.invoke(getJobsQueues);
  }

  /** Fetches active workers. */
  async getJobsWorkers(): Promise<WorkerInfo[]> {
    return this.api.invoke(getJobsWorkers);
  }

  /** Fetches failure summary. */
  async getJobsFailures(): Promise<JobFailures> {
    return this.api.invoke(getJobsFailures);
  }

  /** Purges all messages from a queue. */
  async purgeQueue(queueName: string): Promise<void> {
    return this.api.invoke(purgeQueue, { queue_name: queueName });
  }
}
