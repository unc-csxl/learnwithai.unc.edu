/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { PageTitleService } from '../../../page-title.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';

/** Landing view for instructor course navigation. */
@Component({
  selector: 'app-dashboard',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCardModule],
  templateUrl: './dashboard.component.html',
})
export class Dashboard {
  private titleService = inject(PageTitleService);
  private layoutNavigation = inject(LayoutNavigationService);

  constructor() {
    this.layoutNavigation.clearContext();
    this.titleService.setTitle('Dashboard');
  }
}
