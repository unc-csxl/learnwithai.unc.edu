/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../auth.service';
import { ImpersonationService } from '../impersonation.service';

/** Fixed banner shown when an operator is impersonating another user. */
@Component({
  selector: 'app-impersonation-banner',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './impersonation-banner.component.html',
  styleUrl: './impersonation-banner.component.scss',
})
export class ImpersonationBanner {
  protected auth = inject(AuthService);
  private impersonation = inject(ImpersonationService);

  protected exitImpersonation(): void {
    this.impersonation.stopImpersonation();
  }
}
