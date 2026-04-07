/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Injectable, signal, effect, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

export type ThemeMode = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'theme-mode';

/** Manages light/dark theme preference with localStorage persistence. */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private platformId = inject(PLATFORM_ID);
  private isBrowser = isPlatformBrowser(this.platformId);

  /** The user's explicit preference (or 'system' for OS default). */
  readonly mode = signal<ThemeMode>(this.loadPreference());

  /** Whether the resolved theme is dark. */
  readonly isDark = signal(false);

  constructor() {
    effect(() => {
      this.applyTheme(this.mode());
    });

    this.listenForSystemChanges();
  }

  /** Cycles through system -> light -> dark -> system. */
  toggle(): void {
    const next: Record<ThemeMode, ThemeMode> = {
      system: 'light',
      light: 'dark',
      dark: 'system',
    };
    this.mode.set(next[this.mode()]);
  }

  private listenForSystemChanges(): void {
    if (!this.isBrowser) return;
    const mq = window.matchMedia?.('(prefers-color-scheme: dark)');
    if (!mq) return;
    mq.addEventListener('change', () => {
      if (this.mode() === 'system') {
        this.isDark.set(mq.matches);
      }
    });
  }

  private applyTheme(mode: ThemeMode): void {
    if (!this.isBrowser) return;

    localStorage.setItem(STORAGE_KEY, mode);
    const html = document.documentElement;
    html.classList.remove('light', 'dark');

    if (mode === 'system') {
      const mq = window.matchMedia?.('(prefers-color-scheme: dark)');
      this.isDark.set(mq?.matches ?? false);
    } else {
      html.classList.add(mode);
      this.isDark.set(mode === 'dark');
    }
  }

  private loadPreference(): ThemeMode {
    if (!this.isBrowser) return 'system';
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored;
    }
    return 'system';
  }
}
