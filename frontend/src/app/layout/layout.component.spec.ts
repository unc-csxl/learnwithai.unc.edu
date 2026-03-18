import { Component } from '@angular/core';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { BreakpointObserver, BreakpointState } from '@angular/cdk/layout';
import { Subject } from 'rxjs';
import { Layout } from './layout.component';
import { AuthService } from '../auth.service';
import { ThemeService } from '../theme.service';
import { User } from '../api/models';

@Component({ template: '' })
class DummyComponent {}

const fakeUser: User = {
  pid: 999999999,
  name: 'Test User',
  given_name: 'Test',
  family_name: 'User',
  email: 'test@example.com',
};

describe('Layout', () => {
  function setup(
    options: { authenticated: boolean; handset?: boolean } = { authenticated: false },
  ) {
    const userSignal = signal<User | null>(options.authenticated ? fakeUser : null);
    const mockAuth = {
      user: userSignal.asReadonly(),
      isAuthenticated: signal(options.authenticated).asReadonly(),
      login: vi.fn(),
      logout: vi.fn(),
    };

    const mockTheme = {
      mode: signal<'system' | 'light' | 'dark'>('system'),
      isDark: signal(false),
      toggle: vi.fn(),
    };

    const breakpoint$ = new Subject<BreakpointState>();
    const mockBreakpointObserver = {
      observe: () => breakpoint$,
    };

    TestBed.configureTestingModule({
      imports: [Layout, NoopAnimationsModule],
      providers: [
        provideRouter([{ path: 'courses', component: DummyComponent }]),
        { provide: AuthService, useValue: mockAuth },
        { provide: ThemeService, useValue: mockTheme },
        { provide: BreakpointObserver, useValue: mockBreakpointObserver },
      ],
    });

    const fixture = TestBed.createComponent(Layout);
    // Emit initial breakpoint state
    breakpoint$.next({
      matches: options.handset ?? false,
      breakpoints: {},
    });
    fixture.detectChanges();
    return { fixture, mockAuth, mockTheme, breakpoint$ };
  }

  it('should create', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should show app title in toolbar', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('mat-toolbar')?.textContent).toContain('LearnWithAI');
  });

  it('should show login button when unauthenticated', () => {
    const { fixture, mockAuth } = setup({ authenticated: false });
    const el: HTMLElement = fixture.nativeElement;
    const buttons = el.querySelectorAll('mat-toolbar button');
    const loginBtn = Array.from(buttons).find((b) =>
      b.textContent?.includes('Login'),
    ) as HTMLButtonElement;
    expect(loginBtn).toBeTruthy();
    loginBtn.click();
    expect(mockAuth.login).toHaveBeenCalled();
  });

  it('should show logout button when authenticated', () => {
    const { fixture, mockAuth } = setup({ authenticated: true });
    const el: HTMLElement = fixture.nativeElement;
    const buttons = el.querySelectorAll('mat-toolbar button');
    const logoutBtn = Array.from(buttons).find((b) =>
      b.textContent?.includes('Logout'),
    ) as HTMLButtonElement;
    expect(logoutBtn).toBeTruthy();
    logoutBtn.click();
    expect(mockAuth.logout).toHaveBeenCalled();
  });

  it('should have a theme toggle button', () => {
    const { fixture, mockTheme } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const themeBtn = el.querySelector('button[aria-label="Theme: System"]');
    expect(themeBtn).toBeTruthy();
    themeBtn?.dispatchEvent(new Event('click'));
    expect(mockTheme.toggle).toHaveBeenCalled();
  });

  it('should show courses nav link in sidenav', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('mat-sidenav')?.textContent).toContain('Courses');
  });

  it('should show hamburger menu on handset', () => {
    const { fixture } = setup({ authenticated: false, handset: true });
    const el: HTMLElement = fixture.nativeElement;
    const menuBtn = el.querySelector('button[aria-label="Toggle navigation"]') as HTMLButtonElement;
    expect(menuBtn).toBeTruthy();
    // Click the hamburger to toggle sidenav
    menuBtn.click();
    fixture.detectChanges();
  });

  it('should not show hamburger menu on desktop', () => {
    const { fixture } = setup({ authenticated: false, handset: false });
    const el: HTMLElement = fixture.nativeElement;
    const menuBtn = el.querySelector('button[aria-label="Toggle navigation"]');
    expect(menuBtn).toBeFalsy();
  });

  it('should close sidenav on nav click in handset mode', () => {
    const { fixture } = setup({ authenticated: false, handset: true });
    const el: HTMLElement = fixture.nativeElement;
    const navLink = el.querySelector('mat-nav-list a') as HTMLElement;
    expect(navLink).toBeTruthy();
    navLink.click();
    fixture.detectChanges();
  });
});
