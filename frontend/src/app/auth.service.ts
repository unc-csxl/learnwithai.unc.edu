import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { User } from './user.model';

const TOKEN_KEY = 'auth_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private _user = signal<User | null>(null);

  readonly user = this._user.asReadonly();
  readonly isAuthenticated = computed(() => this._user() !== null);

  constructor() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      this.fetchProfile();
    }
  }

  login(): void {
    window.location.href = '/api/auth/onyen';
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    this._user.set(null);
  }

  handleToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
    this.fetchProfile();
  }

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
