import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { User } from './user.model';

const TOKEN_KEY = 'auth_token';

/** Manages login state and the current authenticated user profile. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private _user = signal<User | null>(null);

  readonly user = this._user.asReadonly();
  readonly isAuthenticated = computed(() => this._user() !== null);

  /** Restores a previously persisted token when one is available. */
  constructor() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      this.fetchProfile();
    }
  }

  /** Redirects the browser to the server-side login flow. */
  login(): void {
    window.location.href = '/api/auth/onyen';
  }

  /** Clears the persisted token and resets local authentication state. */
  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    this._user.set(null);
  }

  /** Persists a freshly issued token and refreshes the current user profile. */
  handleToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
    this.fetchProfile();
  }

  /** Loads the current user profile for the persisted authentication token. */
  fetchProfile(): void {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      return;
    }
    this.http
      .get<User>('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      .subscribe({
        next: (user) => this._user.set(user),
        error: () => {
          localStorage.removeItem(TOKEN_KEY);
          this._user.set(null);
        },
      });
  }
}
