import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthService } from './auth.service';
import { User } from './user.model';

const fakeUser: User = {
  id: '123',
  name: 'Test User',
  pid: '999999999',
  onyen: 'testuser',
  email: 'test@example.com',
};

describe('AuthService', () => {
  let service: AuthService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
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
    localStorage.setItem('auth_token', 'some-token');
    service.logout();
    expect(localStorage.getItem('auth_token')).toBeNull();
    expect(service.user()).toBeNull();
    expect(service.isAuthenticated()).toBe(false);
  });

  it('handleToken should store token and fetch profile', () => {
    service.handleToken('my-jwt-token');
    expect(localStorage.getItem('auth_token')).toBe('my-jwt-token');

    const req = httpTesting.expectOne('/api/me');
    expect(req.request.headers.get('Authorization')).toBe('Bearer my-jwt-token');
    req.flush(fakeUser);

    expect(service.user()).toEqual(fakeUser);
    expect(service.isAuthenticated()).toBe(true);
  });

  it('fetchProfile should clear token on error', () => {
    localStorage.setItem('auth_token', 'bad-token');
    service.fetchProfile();

    const req = httpTesting.expectOne('/api/me');
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    expect(localStorage.getItem('auth_token')).toBeNull();
    expect(service.user()).toBeNull();
  });

  it('fetchProfile should do nothing without a token', () => {
    service.fetchProfile();
    httpTesting.expectNone('/api/me');
  });

  it('should fetch profile on construction when token exists', () => {
    localStorage.setItem('auth_token', 'existing-token');

    // Recreate the injector so the constructor observes the persisted token.
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    const newService = TestBed.inject(AuthService);
    const newHttpTesting = TestBed.inject(HttpTestingController);

    const req = newHttpTesting.expectOne('/api/me');
    expect(req.request.headers.get('Authorization')).toBe('Bearer existing-token');
    req.flush(fakeUser);

    expect(newService.user()).toEqual(fakeUser);
    newHttpTesting.verify();
  });
});
