import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-home',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main>
      @if (auth.isAuthenticated()) {
        <h1>Hello, {{ auth.user()!.name }}</h1>
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
