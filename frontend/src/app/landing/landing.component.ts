import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { AuthService } from '../auth.service';
import { environment } from '../../environments/environment';
import { User } from '../api/models';
import { MatPane } from '../shared/mat-pane/mat-pane';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

/** Landing page shown to unauthenticated users. */
@Component({
  selector: 'app-landing',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatButtonModule, MatCardModule, MatIconModule, MatMenuModule, MatPane],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
})
export class Landing {
  protected auth = inject(AuthService);
  private http = inject(HttpClient);

  protected readonly isDev = !environment.production;
  protected readonly devUsers = signal<User[]>([]);
  protected readonly currentYear = new Date().getFullYear();

  constructor() {
    /* v8 ignore start -- isDev is a compile-time constant; only one branch runs per build */
    if (this.isDev) {
      /* v8 ignore stop */
      this.loadDevUsers();
    }
  }

  private async loadDevUsers(): Promise<void> {
    try {
      const users = await firstValueFrom(this.http.get<User[]>('/api/dev/users'));
      this.devUsers.set(users);
    } catch {
      // Dev endpoint not available; leave list empty.
    }
  }

  protected devLoginAs(user: User): void {
    window.location.href = `/api/auth/as/${user.pid}`;
  }
}
