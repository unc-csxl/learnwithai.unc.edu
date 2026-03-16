import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

/** Bootstraps the standalone Angular application. */
bootstrapApplication(App, appConfig).catch((err) => console.error(err));
