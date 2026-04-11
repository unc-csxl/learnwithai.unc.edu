/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';
import { AuthTokenService } from '../auth-token.service';

const ORIGINAL_TOKEN_KEY = 'impersonation_original_token';

/** Manages impersonation state by swapping JWT tokens. */
@Injectable({ providedIn: 'root' })
export class ImpersonationService {
  private auth = inject(AuthService);
  private tokenService = inject(AuthTokenService);
  private router = inject(Router);

  private readonly _isImpersonating = signal<boolean>(
    localStorage.getItem(ORIGINAL_TOKEN_KEY) !== null,
  );

  /** Whether the current session is impersonating another user. */
  readonly isImpersonating = this._isImpersonating.asReadonly();

  /** Starts impersonating a user with the given token. */
  async startImpersonation(token: string): Promise<void> {
    const currentToken = this.tokenService.getToken();
    if (currentToken) {
      localStorage.setItem(ORIGINAL_TOKEN_KEY, currentToken);
    }
    this.tokenService.setToken(token);
    this._isImpersonating.set(true);
    await this.auth.fetchProfile();
    await this.router.navigate(['/courses']);
  }

  /** Stops impersonation and restores the original operator session. */
  async stopImpersonation(): Promise<void> {
    const originalToken = localStorage.getItem(ORIGINAL_TOKEN_KEY);
    if (originalToken) {
      this.tokenService.setToken(originalToken);
      localStorage.removeItem(ORIGINAL_TOKEN_KEY);
    }
    this._isImpersonating.set(false);
    await this.auth.fetchProfile();
    await this.router.navigate(['/operations']);
  }
}
