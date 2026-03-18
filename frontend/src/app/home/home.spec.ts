import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Home } from './home';
import { AuthService } from '../auth.service';
import { User } from '../user.model';

const fakeUser: User = {
  pid: 999999999,
  name: 'Test User',
  onyen: 'testuser',
  email: 'test@example.com',
};

describe('Home', () => {
  function setup(options: { authenticated: boolean }) {
    const userSignal = signal<User | null>(options.authenticated ? fakeUser : null);
    const mockAuth = {
      user: userSignal.asReadonly(),
      isAuthenticated: signal(options.authenticated).asReadonly(),
      login: vi.fn(),
      logout: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Home],
      providers: [provideRouter([]), { provide: AuthService, useValue: mockAuth }],
    });

    const fixture = TestBed.createComponent(Home);
    fixture.detectChanges();
    return { fixture, mockAuth };
  }

  it('should show login button when unauthenticated', () => {
    const { fixture } = setup({ authenticated: false });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('h1')?.textContent).toContain('Welcome to LearnWithAI');
    expect(el.querySelector('button')?.textContent).toContain('Login');
  });

  it('should call login on button click when unauthenticated', () => {
    const { fixture, mockAuth } = setup({ authenticated: false });
    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    button.click();
    expect(mockAuth.login).toHaveBeenCalled();
  });

  it('should show greeting when authenticated', () => {
    const { fixture } = setup({ authenticated: true });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('h1')?.textContent).toContain('Hello, Test User');
  });

  it('should show course navigation when authenticated', () => {
    const { fixture } = setup({ authenticated: true });
    const el: HTMLElement = fixture.nativeElement;

    expect(el.querySelector('a[href="/courses"]')?.textContent).toContain('View courses');
    expect(el.querySelector('a[href="/courses/create"]')?.textContent).toContain('Create course');
  });

  it('should call logout on button click when authenticated', () => {
    const { fixture, mockAuth } = setup({ authenticated: true });
    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    button.click();
    expect(mockAuth.logout).toHaveBeenCalled();
  });
});
