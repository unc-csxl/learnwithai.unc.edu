import { Component, ChangeDetectionStrategy, inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-jwt',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<p>Authenticating...</p>`,
})
export class Jwt implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private auth = inject(AuthService);

  ngOnInit(): void {
    const token = this.route.snapshot.queryParamMap.get('token');
    if (token) {
      this.auth.handleToken(token);
    }
    this.router.navigate(['/']);
  }
}
