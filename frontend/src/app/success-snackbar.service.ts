/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { inject, Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';

/**
 * Shared service for showing brief success notifications using Angular Material
 * snack bars. Components that save data should use this service rather than
 * injecting MatSnackBar directly so that the duration and dismiss behavior stay
 * consistent across the app.
 */
@Injectable({ providedIn: 'root' })
export class SuccessSnackbarService {
  private snackBar = inject(MatSnackBar);

  /** Open a success snack bar. Defaults to a 5-second auto-dismiss. */
  open(message: string, duration = 5000): void {
    this.snackBar.open(message, undefined, { duration, politeness: 'polite' });
  }
}
