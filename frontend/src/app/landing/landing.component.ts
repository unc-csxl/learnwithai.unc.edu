import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  computed,
  InjectionToken,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { NgOptimizedImage } from '@angular/common';
import { AuthService } from '../auth.service';
import { ThemeService } from '../theme.service';
import { environment } from '../../environments/environment';
import { User } from '../api/models';
import { MatPane } from '../shared/mat-pane/mat-pane';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export const IS_DEV_MODE = new InjectionToken<boolean>('IS_DEV_MODE', {
  factory: () => !environment.production,
});

/** Landing page shown to unauthenticated users. */
@Component({
  selector: 'app-landing',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatMenuModule,
    MatPane,
    NgOptimizedImage,
  ],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
})
export class Landing {
  protected auth = inject(AuthService);
  protected theme = inject(ThemeService);
  private http = inject(HttpClient);

  protected readonly isDev = inject(IS_DEV_MODE);
  protected readonly devUsers = signal<User[]>([]);
  protected readonly currentYear = new Date().getFullYear();
  protected readonly logoAsset = computed(() =>
    this.theme.isDark() ? 'unc-dark.svg' : 'unc-light.svg',
  );

  constructor() {
    if (this.isDev) {
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
