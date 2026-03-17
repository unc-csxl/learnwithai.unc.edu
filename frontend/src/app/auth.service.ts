import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { User } from './user.model';
import { AuthTokenService } from './auth-token.service';

/** Manages login state and the current authenticated user profile. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
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
    this.http.get<User>('/api/me').subscribe({
      next: (user) => this._user.set(user),
      error: () => {
        this.tokenService.clearToken();
        this._user.set(null);
      },
    });
  }
}
