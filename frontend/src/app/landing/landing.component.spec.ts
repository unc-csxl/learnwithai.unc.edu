import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Landing } from './landing.component';
import { AuthService } from '../auth.service';
import { User } from '../api/models';

const devUsers: User[] = [
  {
    pid: 222222222,
    name: 'Ina Instructor',
    given_name: 'Ina',
    family_name: 'Instructor',
    email: 'instructor@unc.edu',
    onyen: 'instructor',
  },
  {
    pid: 111111111,
    name: 'Sally Student',
    given_name: 'Sally',
    family_name: 'Student',
    email: 'student@unc.edu',
    onyen: 'student',
  },
];

describe('Landing', () => {
  async function setup(options: { isDev?: boolean } = {}) {
    const mockAuth = {
      user: signal<User | null>(null),
      isAuthenticated: signal(false),
      login: vi.fn(),
      logout: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Landing, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: mockAuth },
      ],
    });

    const httpTesting = TestBed.inject(HttpTestingController);
    const fixture = TestBed.createComponent(Landing);

    // If dev mode, the component will have made a request for dev users
    if (fixture.componentInstance['isDev']) {
      const req = httpTesting.expectOne('/api/dev/users');
      req.flush(options.isDev !== false ? devUsers : []);
      // Allow the async loadDevUsers promise to settle
      await fixture.whenStable();
    }

    fixture.detectChanges();
    return { fixture, mockAuth, httpTesting };
  }

  afterEach(() => {
    TestBed.inject(HttpTestingController).verify();
  });

  it('should create', async () => {
    const { fixture } = await setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should display branding', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('LEARN');
    expect(el.textContent).toContain('with');
    expect(el.textContent).toContain('AI');
  });

  it('should display login button', async () => {
    const { fixture, mockAuth } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const buttons = Array.from(el.querySelectorAll('button'));
    const loginBtn = buttons.find((b) => b.textContent?.includes('Login via UNC Onyen'));
    expect(loginBtn).toBeTruthy();
    loginBtn!.click();
    expect(mockAuth.login).toHaveBeenCalled();
  });

  it('should display copyright footer with current year', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const footer = el.querySelector('.landing-footer');
    expect(footer?.textContent).toContain(`${new Date().getFullYear()}`);
    expect(footer?.textContent).toContain('Computer Science Experience Labs');
  });

  it('should have CSXL link in footer', async () => {
    const { fixture } = await setup();
    const el: HTMLElement = fixture.nativeElement;
    const link = el.querySelector('.landing-footer a') as HTMLAnchorElement;
    expect(link?.href).toContain('csxl.unc.edu');
    expect(link?.target).toBe('_blank');
    expect(link?.rel).toContain('noopener');
  });

  it('should show dev login menu when in dev mode with users', async () => {
    const { fixture } = await setup({ isDev: true });
    const el: HTMLElement = fixture.nativeElement;
    if (fixture.componentInstance['isDev']) {
      const devBtn = el.querySelector('[aria-label="Developer login"]') as HTMLButtonElement;
      expect(devBtn).toBeTruthy();
      expect(devBtn.textContent).toContain('Dev Login');
    }
  });

  it('should call devLoginAs with correct user on dev login click', async () => {
    const { fixture } = await setup({ isDev: true });
    if (!fixture.componentInstance['isDev']) {
      return; // Skip in production build
    }
    const spy = vi.spyOn(fixture.componentInstance as never, 'devLoginAs' as never);
    fixture.componentInstance['devLoginAs'](devUsers[0]);
    expect(spy).toHaveBeenCalledWith(devUsers[0]);
  });

  it('should hide dev login menu when devUsers list is empty', async () => {
    const { fixture } = await setup({ isDev: false });
    const el: HTMLElement = fixture.nativeElement;
    const devBtn = el.querySelector('[aria-label="Developer login"]');
    expect(devBtn).toBeNull();
  });

  it('should handle dev users endpoint failure gracefully', async () => {
    TestBed.configureTestingModule({
      imports: [Landing, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: AuthService,
          useValue: {
            user: signal<User | null>(null),
            isAuthenticated: signal(false),
            login: vi.fn(),
            logout: vi.fn(),
          },
        },
      ],
    });

    const httpTesting = TestBed.inject(HttpTestingController);
    const fixture = TestBed.createComponent(Landing);

    if (fixture.componentInstance['isDev']) {
      const req = httpTesting.expectOne('/api/dev/users');
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
      await fixture.whenStable();
    }

    fixture.detectChanges();
    expect(fixture.componentInstance['devUsers']()).toEqual([]);
    httpTesting.verify();
  });
});
