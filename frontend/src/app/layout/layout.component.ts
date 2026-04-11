/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, computed, viewChild } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule, MatSidenav } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { NgOptimizedImage } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';
import { AuthService } from '../auth.service';
import { ThemeService, ThemeMode } from '../theme.service';
import { PageTitleService } from '../page-title.service';
import { LayoutNavigationService } from './layout-navigation.service';
import { ImpersonationService } from '../admin/impersonation.service';
import { ImpersonationBanner } from '../admin/impersonation-banner/impersonation-banner.component';

/** App shell with a responsive toolbar and sidenav. */
@Component({
  selector: 'app-layout',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    NgOptimizedImage,
    ImpersonationBanner,
  ],
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.scss',
})
export class Layout {
  private breakpointObserver = inject(BreakpointObserver);
  protected auth = inject(AuthService);
  protected theme = inject(ThemeService);
  protected pageTitle = inject(PageTitleService);
  protected layoutNavigation = inject(LayoutNavigationService);
  protected impersonation = inject(ImpersonationService);
  protected readonly exactLinkActiveOptions = { exact: true };
  protected readonly subtreeLinkActiveOptions = { exact: false };

  protected readonly drawerRef = viewChild<MatSidenav>('drawer');

  private isHandset$ = this.breakpointObserver
    .observe(Breakpoints.Handset)
    .pipe(map((result) => result.matches));

  protected readonly isHandset = toSignal(this.isHandset$, { initialValue: false });
  protected readonly sidenavMode = computed(() => (this.isHandset() ? 'over' : 'side'));
  protected readonly sidenavOpened = computed(() => !this.isHandset());
  protected readonly logoAsset = computed(() =>
    this.theme.isDark() ? 'unc-dark.svg' : 'unc-light.svg',
  );

  protected readonly themeIcon = computed<string>(() => {
    const icons: Record<ThemeMode, string> = {
      system: 'computer',
      light: 'light_mode',
      dark: 'dark_mode',
    };
    return icons[this.theme.mode()];
  });

  protected readonly themeTooltip = computed<string>(() => {
    const labels: Record<ThemeMode, string> = {
      system: 'Theme: System',
      light: 'Theme: Light',
      dark: 'Theme: Dark',
    };
    return labels[this.theme.mode()];
  });

  /* v8 ignore start -- @preserve */
  protected toggleDrawer(): void {
    this.drawerRef()?.toggle();
  }

  protected closeMobileSidenav(): void {
    if (this.isHandset()) {
      this.drawerRef()?.close();
    }
  }
  /* v8 ignore stop -- @preserve */
}
