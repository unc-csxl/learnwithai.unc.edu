/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject, OnDestroy, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from '../../auth.service';
import { PageTitleService } from '../../page-title.service';
import {
  LayoutNavigationSection,
  LayoutNavigationService,
} from '../../layout/layout-navigation.service';

/** Admin area shell — sets up admin sidenav navigation. */
@Component({
  selector: 'app-admin-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet],
  templateUrl: './admin-shell.component.html',
})
export class AdminShell implements OnDestroy {
  private auth = inject(AuthService);
  private titleService = inject(PageTitleService);
  private layoutNavigation = inject(LayoutNavigationService);

  protected readonly errorMessage = signal('');

  constructor() {
    this.titleService.setTitle('Admin Tools');
    const user = this.auth.user();
    if (!user?.operator) {
      this.errorMessage.set('Operator access required.');
      return;
    }
    this.layoutNavigation.setSection(this.buildNavigation(user.operator.permissions));
  }

  ngOnDestroy(): void {
    this.layoutNavigation.clear();
  }

  private buildNavigation(permissions: string[]): LayoutNavigationSection {
    const permSet = new Set(permissions);

    const items = [];

    if (permSet.has('manage_operators')) {
      items.push({
        route: '/admin/operators',
        label: 'Operators',
        description: 'Manage system operators',
        icon: 'admin_panel_settings',
      });
    }

    if (permSet.has('view_jobs')) {
      items.push({
        route: '/admin/jobs',
        label: 'Job Control',
        description: 'View background job status',
        icon: 'work',
      });
    }

    if (permSet.has('view_metrics')) {
      items.push({
        route: '/admin/metrics',
        label: 'Usage Metrics',
        description: 'View platform usage statistics',
        icon: 'analytics',
      });
    }

    return {
      groups: [
        {
          label: 'Admin',
          items,
        },
      ],
    };
  }
}
