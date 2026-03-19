import { Injectable, inject, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { Api } from './api/generated/api';
import { getCurrentSubjectProfile } from './api/generated/fn/authentication/get-current-subject-profile';
import { User } from './api/models';
import { AuthTokenService } from './auth-token.service';

/** Manages login state and the current authenticated user profile. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(Api);
  private tokenService = inject(AuthTokenService);
  private router = inject(Router);
  private _user = signal<User | null>(null);

  readonly user = this._user.asReadonly();
  readonly isAuthenticated = computed(() => this._user() !== null);

  /** Restores a previously persisted token when one is available. */
  constructor() {
    if (this.tokenService.hasToken()) {
      this.fetchProfile();
    }
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
    await this.fetchProfile();
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
}
