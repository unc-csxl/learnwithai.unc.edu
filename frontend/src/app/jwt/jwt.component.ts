/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../auth.service';

/** Handles the post-authentication redirect and persists the issued JWT. */
@Component({
  selector: 'app-jwt',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<p>Authenticating...</p>`,
})
export class Jwt implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private auth = inject(AuthService);

  /** Extracts the token from the callback URL and routes the user home. */
  async ngOnInit(): Promise<void> {
    const token = this.route.snapshot.queryParamMap.get('token');
    if (token) {
      await this.auth.handleToken(token);
    }
    this.router.navigate(['/courses']);
  }
}
