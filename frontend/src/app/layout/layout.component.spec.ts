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
import { PageTitleService } from '../page-title.service';
import { User } from '../api/models';
import { LayoutNavigationSection, LayoutNavigationService } from './layout-navigation.service';

@Component({ template: '' })
class DummyComponent {}

const fakeUser: User = {
  pid: 999999999,
  name: 'Test User',
  given_name: 'Test',
  family_name: 'User',
  email: 'test@example.com',
  onyen: 'testuser',
};

describe('Layout', () => {
  function setup(
    options: {
      authenticated: boolean;
      handset?: boolean;
      section?: LayoutNavigationSection | null;
    } = { authenticated: false },
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

    const mockPageTitle = {
      title: signal('Test Page'),
      setTitle: vi.fn(),
    };

    const mockLayoutNavigation = {
      section: signal(options.section ?? null).asReadonly(),
      setSection: vi.fn(),
      clear: vi.fn(),
    };

    const breakpoint$ = new Subject<BreakpointState>();
    const mockBreakpointObserver = {
      observe: () => breakpoint$,
    };

    TestBed.configureTestingModule({
      imports: [Layout, NoopAnimationsModule],
      providers: [
        provideRouter([
          { path: 'courses', component: DummyComponent },
          { path: 'profile', component: DummyComponent },
        ]),
        { provide: AuthService, useValue: mockAuth },
        { provide: ThemeService, useValue: mockTheme },
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
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
    return { fixture, mockAuth, mockTheme, mockPageTitle, mockLayoutNavigation, breakpoint$ };
  }

  it('should create', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should show app title in sidenav on desktop', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const brand = el.querySelector('.sidenav-brand');
    expect(brand?.textContent).toContain('LEARN');
    expect(brand?.textContent).toContain('with');
    expect(brand?.textContent).toContain('AI');
  });

  it('should show page title in toolbar', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const toolbar = el.querySelector('mat-sidenav-content mat-toolbar');
    expect(toolbar?.textContent).toContain('Test Page');
  });

  it('should show login button when unauthenticated', () => {
    const { fixture, mockAuth } = setup({ authenticated: false });
    const el: HTMLElement = fixture.nativeElement;
    const footer = el.querySelector('.sidenav-footer')!;
    const loginBtn = footer.querySelector('button') as HTMLButtonElement;
    expect(loginBtn?.textContent).toContain('Login');
    loginBtn.click();
    expect(mockAuth.login).toHaveBeenCalled();
  });

  it('should show logout button when authenticated', () => {
    const { fixture, mockAuth } = setup({ authenticated: true });
    const el: HTMLElement = fixture.nativeElement;
    const logoutBtn = el.querySelector(
      '.sidenav-footer button[aria-label="Logout"]',
    ) as HTMLButtonElement;
    expect(logoutBtn).toBeTruthy();
    logoutBtn.click();
    expect(mockAuth.logout).toHaveBeenCalled();
  });

  it('should show user profile link when authenticated', () => {
    const { fixture } = setup({ authenticated: true });
    const el: HTMLElement = fixture.nativeElement;
    const profileLink = el.querySelector('.user-profile-link') as HTMLAnchorElement;
    expect(profileLink).toBeTruthy();
    expect(profileLink.textContent).toContain('Test User');
  });

  it('should have a theme toggle button', () => {
    const { fixture, mockTheme } = setup();
    const el: HTMLElement = fixture.nativeElement;
    const themeBtn = el.querySelector('button[aria-label="Theme: System"]');
    expect(themeBtn).toBeTruthy();
    themeBtn?.dispatchEvent(new Event('click'));
    expect(mockTheme.toggle).toHaveBeenCalled();
  });

  it('should update theme icon and tooltip for light and dark modes', () => {
    const { fixture, mockTheme } = setup();
    const component = fixture.componentInstance;

    expect(component['themeIcon']()).toBe('computer');
    expect(component['themeTooltip']()).toBe('Theme: System');
    expect(component['logoAsset']()).toBe('unc-light.svg');

    mockTheme.mode.set('light');
    fixture.detectChanges();
    expect(component['themeIcon']()).toBe('light_mode');
    expect(component['themeTooltip']()).toBe('Theme: Light');

    mockTheme.mode.set('dark');
    mockTheme.isDark.set(true);
    fixture.detectChanges();
    expect(component['themeIcon']()).toBe('dark_mode');
    expect(component['themeTooltip']()).toBe('Theme: Dark');
    expect(component['logoAsset']()).toBe('unc-dark.svg');
  });

  it('should show courses nav link in sidenav', () => {
    const { fixture } = setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('mat-sidenav')?.textContent).toContain('Courses');
  });

  it('should show contextual course navigation in the shared sidebar', () => {
    const { fixture } = setup({
      authenticated: true,
      section: {
        groups: [
          {
            label: 'Course',
            items: [
              {
                route: '/courses/1/dashboard',
                label: 'COMP423',
                subtitle: 'Spring 2026 - Section 001',
                description: 'Course overview and quick links',
                icon: 'dashboard',
              },
            ],
          },
        ],
      },
    });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('mat-sidenav')?.textContent).toContain('Course');
    expect(el.querySelector('mat-sidenav')?.textContent).toContain('COMP423');
    expect(el.querySelector('mat-sidenav')?.textContent).toContain('Spring 2026 - Section 001');
  });

  it('should render contextual navigation items without optional metadata', () => {
    const { fixture } = setup({
      authenticated: true,
      section: {
        groups: [
          {
            items: [
              {
                route: '/courses/1/settings',
                label: 'Course Settings',
                icon: 'settings',
              },
            ],
          },
        ],
      },
    });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.context-nav-label')).toBeFalsy();
    expect(el.querySelector('.context-nav-item-subtitle')).toBeFalsy();
    expect(el.querySelector('mat-sidenav')?.textContent).toContain('Course Settings');
  });

  it('should render subtree course links for nested routes', () => {
    const { fixture } = setup({
      authenticated: true,
      section: {
        groups: [
          {
            label: 'Course',
            items: [
              {
                route: '/courses/1/activities',
                label: 'Student Activities',
                description: 'Review student-facing work and participation',
                icon: 'assignment',
                exact: false,
              },
            ],
          },
        ],
      },
    });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('mat-sidenav')?.textContent).toContain('Student Activities');
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

  it('should show close button in sidenav on handset', () => {
    const { fixture } = setup({ authenticated: false, handset: true });
    const el: HTMLElement = fixture.nativeElement;
    const closeBtn = el.querySelector('button[aria-label="Close navigation"]') as HTMLButtonElement;
    expect(closeBtn).toBeTruthy();
    closeBtn.click();
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

  it('should close sidenav on contextual nav click in handset mode', () => {
    const { fixture } = setup({
      authenticated: true,
      handset: true,
      section: {
        groups: [
          {
            label: 'Course',
            items: [
              {
                route: '/courses/1/roster',
                label: 'Roster',
                description: 'See current course membership',
                icon: 'groups',
              },
            ],
          },
        ],
      },
    });
    const el: HTMLElement = fixture.nativeElement;
    const navLists = el.querySelectorAll('mat-nav-list');
    const contextualLink = navLists[1]?.querySelector('a') as HTMLElement | null;
    expect(contextualLink).toBeTruthy();
    contextualLink?.click();
    fixture.detectChanges();
  });

  it('should close sidenav on profile link click in handset mode', () => {
    const { fixture } = setup({ authenticated: true, handset: true });
    const el: HTMLElement = fixture.nativeElement;
    const profileLink = el.querySelector('.user-profile-link') as HTMLElement;
    expect(profileLink).toBeTruthy();
    profileLink.click();
    fixture.detectChanges();
  });
});
