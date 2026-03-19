import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { authGuard, landingGuard } from './auth.guard';
import { AuthService } from './auth.service';

function setup(authenticated: boolean) {
  const mockAuth = {
    isAuthenticated: signal(authenticated),
  };

  TestBed.configureTestingModule({
    providers: [
      provideRouter([
        { path: '', component: class {} as never },
        { path: 'courses', component: class {} as never },
        { path: 'protected', canActivate: [authGuard], component: class {} as never },
      ]),
      { provide: AuthService, useValue: mockAuth },
    ],
  });

  return { router: TestBed.inject(Router), mockAuth };
}

describe('authGuard', () => {
  it('should allow access when authenticated', () => {
    setup(true);
    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as never, { url: '/protected' } as never),
    );
    expect(result).toBe(true);
  });

  it('should redirect to landing when not authenticated', () => {
    const { router } = setup(false);
    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as never, { url: '/protected' } as never),
    );
    expect(result).toEqual(router.createUrlTree(['/']));
  });
});

describe('landingGuard', () => {
  it('should redirect authenticated users to courses', () => {
    const { router } = setup(true);
    const result = TestBed.runInInjectionContext(() =>
      landingGuard({} as never, { url: '/' } as never),
    );
    expect(result).toEqual(router.createUrlTree(['/courses']));
  });

  it('should allow unauthenticated users to see landing', () => {
    setup(false);
    const result = TestBed.runInInjectionContext(() =>
      landingGuard({} as never, { url: '/' } as never),
    );
    expect(result).toBe(true);
  });
});
