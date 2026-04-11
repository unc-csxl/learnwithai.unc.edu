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

/** Operations area shell — sets up operations sidenav navigation. */
@Component({
  selector: 'app-operations-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet],
  templateUrl: './operations-shell.component.html',
})
export class OperationsShell implements OnDestroy {
  private auth = inject(AuthService);
  private titleService = inject(PageTitleService);
  private layoutNavigation = inject(LayoutNavigationService);

  protected readonly errorMessage = signal('');

  constructor() {
    this.titleService.setTitle('Operations');
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

    if (permSet.has('view_metrics')) {
      items.push({
        route: '/operations/metrics',
        label: 'Usage Metrics',
        description: 'View platform usage statistics',
        icon: 'analytics',
      });
    }

    if (permSet.has('impersonate')) {
      items.push({
        route: '/operations/impersonate',
        label: 'Impersonate',
        description: 'Act as another user',
        icon: 'swap_horiz',
      });
    }

    if (permSet.has('view_jobs')) {
      items.push({
        route: '/operations/jobs',
        label: 'Job Control',
        description: 'View background job status',
        icon: 'work',
      });
    }

    if (permSet.has('manage_operators')) {
      items.push({
        route: '/operations/operators',
        label: 'Operators',
        description: 'Manage system operators',
        icon: 'admin_panel_settings',
      });
    }

    return {
      groups: [
        {
          label: 'Operations',
          items,
        },
      ],
    };
  }
}
