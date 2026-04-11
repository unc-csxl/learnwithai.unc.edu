/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Injectable, inject } from '@angular/core';
import { Api } from '../api/generated/api';
import { listOperators } from '../api/generated/fn/admin/list-operators';
import { grantOperator } from '../api/generated/fn/admin/grant-operator';
import { updateOperatorRole } from '../api/generated/fn/admin/update-operator-role';
import { revokeOperator } from '../api/generated/fn/admin/revoke-operator';
import { impersonateUser } from '../api/generated/fn/admin/impersonate-user';
import { Operator, OperatorRole, ImpersonationTokenResponse } from '../api/models';
import { ImpersonationService } from './impersonation.service';

/** Wraps admin API calls for operator management and impersonation. */
@Injectable({ providedIn: 'root' })
export class AdminService {
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
}
