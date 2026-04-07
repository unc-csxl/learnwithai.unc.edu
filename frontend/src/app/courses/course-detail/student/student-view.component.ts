/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { PageTitleService } from '../../../page-title.service';
import { LayoutNavigationService } from '../../../layout/layout-navigation.service';

/** Placeholder for student-facing course tools. */
@Component({
  selector: 'app-student-view',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="space-y-3">
      <p class="text-sm opacity-75">Student Dashboard</p>
      <p>
        Your course home will live here. Use the sidebar to move between activities and future
        student tools.
      </p>
    </section>
  `,
})
export class StudentView {
  private titleService = inject(PageTitleService);
  private layoutNavigation = inject(LayoutNavigationService);

  constructor() {
    this.layoutNavigation.clearContext();
    this.titleService.setTitle('Student Dashboard');
  }
}
