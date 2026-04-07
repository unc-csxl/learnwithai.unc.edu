/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/* v8 ignore start -- @preserve */
/** Shell component that hosts the application router outlet. */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class App {}
/* v8 ignore stop -- @preserve */
