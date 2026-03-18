import { Injectable, inject, signal, computed } from '@angular/core';
import { Api } from './api/generated/api';
import { getCurrentSubjectProfile } from './api/generated/fn/authentication/get-current-subject-profile';
import { User } from './api/models';
import { AuthTokenService } from './auth-token.service';

/** Manages login state and the current authenticated user profile. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(Api);
  private tokenService = inject(AuthTokenService);
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
  }

  /** Persists a freshly issued token and refreshes the current user profile. */
  handleToken(token: string): void {
    this.tokenService.setToken(token);
    this.fetchProfile();
  }

  /** Loads the current user profile for the persisted authentication token. */
  fetchProfile(): void {
    if (!this.tokenService.hasToken()) {
      return;
    }
    this.api.invoke(getCurrentSubjectProfile).then(
      (user) => this._user.set(user),
      () => {
        this.tokenService.clearToken();
        this._user.set(null);
      },
    );
  }
}
