import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../auth.service';

/** Landing page that renders the authenticated and anonymous home states. */
@Component({
  selector: 'app-home',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <main>
      @if (auth.isAuthenticated()) {
        <h1>Hello, {{ auth.user()!.name }}</h1>
        <p>
          <a routerLink="/courses">View courses</a>
        </p>
        <p>
          <a routerLink="/courses/create">Create course</a>
        </p>
        <button (click)="auth.logout()">Logout</button>
      } @else {
        <h1>Welcome to LearnWithAI</h1>
        <p>Please log in to continue.</p>
        <button (click)="auth.login()">Login</button>
      }
    </main>
  `,
})
export class Home {
  protected readonly auth = inject(AuthService);
}
