import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../auth.service';

/** Landing page that renders the authenticated and anonymous home states. */
@Component({
  selector: 'app-home',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  templateUrl: './home.component.html',
})
export class Home {
  protected readonly auth = inject(AuthService);
}
