/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Injectable, inject, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { Api } from './api/generated/api';
import { getCurrentSubjectProfile } from './api/generated/fn/authentication/get-current-subject-profile';
import { updateCurrentSubjectProfile } from './api/generated/fn/authentication/update-current-subject-profile';
import { User, UpdateProfile } from './api/models';
import { AuthTokenService } from './auth-token.service';

/** Manages login state and the current authenticated user profile. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(Api);
  private tokenService = inject(AuthTokenService);
  private router = inject(Router);
  private _user = signal<User | null>(null);
  private restorePromise: Promise<void> = Promise.resolve();

  readonly user = this._user.asReadonly();
  readonly isAuthenticated = computed(() => this._user() !== null);

  /** Restores a previously persisted token when one is available. */
  constructor() {
    if (this.tokenService.hasToken()) {
      this.restorePromise = this.fetchProfile();
    }
  }

  /** Resolves once the initial persisted-session restoration has completed. */
  whenReady(): Promise<void> {
    return this.restorePromise;
  }

  /** Redirects the browser to the server-side login flow. */
  login(): void {
    window.location.href = '/api/auth/onyen';
  }

  /** Clears the persisted token and resets local authentication state. */
  logout(): void {
    this.tokenService.clearToken();
    this._user.set(null);
    // Ensure the app navigates back to the landing/login gate after logout.
    // Use a full navigation to the root so the landing gate is shown reliably.
    window.location.href = '/';
  }

  /** Persists a freshly issued token and refreshes the current user profile. */
  async handleToken(token: string): Promise<void> {
    this.tokenService.setToken(token);
    this.restorePromise = this.fetchProfile();
    await this.restorePromise;
  }

  /** Loads the current user profile for the persisted authentication token. */
  async fetchProfile(): Promise<void> {
    if (!this.tokenService.hasToken()) {
      return;
    }
    try {
      const user = await this.api.invoke(getCurrentSubjectProfile);
      this._user.set(user);
    } catch {
      this.tokenService.clearToken();
      this._user.set(null);
    }
  }

  /** Updates the authenticated user's profile and refreshes the local state. */
  async updateProfile(request: UpdateProfile): Promise<User> {
    const updated = await this.api.invoke(updateCurrentSubjectProfile, {
      body: request,
    });
    this._user.set(updated);
    return updated;
  }
}
