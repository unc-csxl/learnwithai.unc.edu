import { Injectable } from '@angular/core';

export const AUTH_TOKEN_KEY = 'auth_token';

/** Centralizes persistence for the SPA bearer token. */
@Injectable({ providedIn: 'root' })
export class AuthTokenService {
  /** Returns the persisted bearer token when one is available. */
  getToken(): string | null {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  }

  /** Indicates whether a bearer token is currently persisted. */
  hasToken(): boolean {
    return this.getToken() !== null;
  }

  /** Persists a bearer token for future API requests. */
  setToken(token: string): void {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  }

  /** Removes the persisted bearer token. */
  clearToken(): void {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}
