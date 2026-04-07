/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app.component';

/** Bootstraps the standalone Angular application. */
bootstrapApplication(App, appConfig).catch((err) => console.error(err));
