import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { Jwt } from './jwt.component';
import { AuthService } from '../auth.service';

describe('Jwt', () => {
  function setup(queryParams: Record<string, string>) {
    const mockAuth = {
      handleToken: vi.fn(),
    };
    const mockRoute = {
      snapshot: {
        queryParamMap: {
          get: (key: string) => queryParams[key] ?? null,
        },
      },
    };
    const mockRouter = {
      navigate: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Jwt],
      providers: [
        { provide: AuthService, useValue: mockAuth },
        { provide: ActivatedRoute, useValue: mockRoute },
        { provide: Router, useValue: mockRouter },
      ],
    });

    const fixture = TestBed.createComponent(Jwt);
    fixture.detectChanges();
    return { fixture, mockAuth, mockRouter };
  }

  it('should handle token from query params and navigate home', () => {
    const { mockAuth, mockRouter } = setup({ token: 'my-jwt-token' });
    expect(mockAuth.handleToken).toHaveBeenCalledWith('my-jwt-token');
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/']);
  });

  it('should navigate home without calling handleToken when no token', () => {
    const { mockAuth, mockRouter } = setup({});
    expect(mockAuth.handleToken).not.toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/']);
  });

  it('should show authenticating message', () => {
    const { fixture } = setup({ token: 'test' });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Authenticating...');
  });
});
