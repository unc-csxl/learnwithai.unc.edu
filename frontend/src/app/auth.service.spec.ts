/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthService } from './auth.service';
import { User } from './api/models';
import { authTokenInterceptor } from './auth-token.interceptor';
import { AUTH_TOKEN_KEY } from './auth-token.service';

const fakeUser: User = {
  pid: 999999999,
  name: 'Test User',
  given_name: 'Test',
  family_name: 'User',
  email: 'test@example.com',
  onyen: 'testuser',
};

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('AuthService', () => {
  let service: AuthService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authTokenInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(AuthService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should start unauthenticated when no token in localStorage', () => {
    expect(service.isAuthenticated()).toBe(false);
    expect(service.user()).toBeNull();
  });

  it('whenReady should resolve immediately without a persisted token', async () => {
    await expect(service.whenReady()).resolves.toBeUndefined();
  });

  it('login should redirect to auth endpoint', () => {
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
      configurable: true,
    });
    service.login();
    expect(window.location.href).toBe('/api/auth/onyen');
  });

  it('logout should clear token and user', () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'some-token');
    // Make `window.location.href` writable so logout can assign to it.
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
      configurable: true,
    });

    service.logout();

    // Token and user cleared
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
    expect(service.user()).toBeNull();
    expect(service.isAuthenticated()).toBe(false);

    // And navigation should return to the landing/login gate
    expect(window.location.href).toBe('/');
  });

  it('handleToken should store token and fetch profile', async () => {
    service.handleToken('my-jwt-token');
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe('my-jwt-token');

    const req = httpTesting.expectOne('/api/me');
    expect(req.request.headers.get('Authorization')).toBe('Bearer my-jwt-token');
    req.flush(fakeUser);
    await flush();

    expect(service.user()).toEqual(fakeUser);
    expect(service.isAuthenticated()).toBe(true);
  });

  it('fetchProfile should clear token on error', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'bad-token');
    service.fetchProfile();

    const req = httpTesting.expectOne('/api/me');
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });
    await flush();

    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
    expect(service.user()).toBeNull();
  });

  it('fetchProfile should do nothing without a token', () => {
    service.fetchProfile();
    httpTesting.expectNone('/api/me');
  });

  it('should fetch profile on construction when token exists', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'existing-token');

    // Recreate the injector so the constructor observes the persisted token.
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authTokenInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    const newService = TestBed.inject(AuthService);
    const newHttpTesting = TestBed.inject(HttpTestingController);
    const ready = newService.whenReady();

    const req = newHttpTesting.expectOne('/api/me');
    expect(req.request.headers.get('Authorization')).toBe('Bearer existing-token');
    req.flush(fakeUser);
    await ready;
    await flush();

    expect(newService.user()).toEqual(fakeUser);
    newHttpTesting.verify();
  });

  it('updateProfile should PUT to /api/me and update the user signal', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'my-token');
    const updatedUser = { ...fakeUser, given_name: 'New', family_name: 'Name', name: 'New Name' };
    const promise = service.updateProfile({ given_name: 'New', family_name: 'Name' });

    const req = httpTesting.expectOne('/api/me');
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ given_name: 'New', family_name: 'Name' });
    req.flush(updatedUser);
    const result = await promise;

    expect(result).toEqual(updatedUser);
    expect(service.user()).toEqual(updatedUser);
  });
});
