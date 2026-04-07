/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { authTokenInterceptor } from './auth-token.interceptor';
import { AUTH_TOKEN_KEY } from './auth-token.service';

describe('authTokenInterceptor', () => {
  let http: HttpClient;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authTokenInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    http = TestBed.inject(HttpClient);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
    localStorage.clear();
  });

  it('adds the bearer token to API requests', () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'api-token');

    http.get('/api/me').subscribe();

    const request = httpTesting.expectOne('/api/me');
    expect(request.request.headers.get('Authorization')).toBe('Bearer api-token');
    request.flush({});
  });

  it('does not add the bearer token to non-API requests', () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'api-token');

    http.get('/assets/config.json').subscribe();

    const request = httpTesting.expectOne('/assets/config.json');
    expect(request.request.headers.has('Authorization')).toBe(false);
    request.flush({});
  });

  it('preserves an explicit authorization header', () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'api-token');

    http
      .get('/api/me', {
        headers: {
          Authorization: 'Basic supplied-header',
        },
      })
      .subscribe();

    const request = httpTesting.expectOne('/api/me');
    expect(request.request.headers.get('Authorization')).toBe('Basic supplied-header');
    request.flush({});
  });
});
