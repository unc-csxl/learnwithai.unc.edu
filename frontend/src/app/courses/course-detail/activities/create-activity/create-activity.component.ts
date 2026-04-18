/*
 * Copyright (c) 2026 Chandon Jarrett
 * SPDX-License-Identifier: MIT
 */

import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { PageTitleService } from '../../../../page-title.service';
import { ACTIVITY_TYPE_OPTIONS } from '../activity-types';

/** Lists the activity types an instructor can choose from to create a new activity. */
@Component({
  selector: 'app-create-activity',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, MatButtonModule],
  templateUrl: './create-activity.component.html',
})
export class CreateActivity {
  private route = inject(ActivatedRoute);
  private titleService = inject(PageTitleService);
  private layoutNavigation = inject(LayoutNavigationService);

  protected readonly courseId: number;
  protected readonly activityTypes = ACTIVITY_TYPE_OPTIONS;

  constructor() {
    this.courseId = Number(this.route.parent?.parent?.snapshot.paramMap.get('id'));
    this.titleService.setTitle('Create Activity');
    this.layoutNavigation.setContextSection({
      visibleBaseRoutes: [
        `/courses/${this.courseId}/dashboard`,
        `/courses/${this.courseId}/activities`,
      ],
      groups: [
        {
          label: 'Choose activity type',
          items: this.activityTypes.map((activityType) => ({
            route: `/courses/${this.courseId}/activities/create/${activityType.routeSegment}`,
            label: `Create ${activityType.label}`,
            description: activityType.description,
            icon: 'add_circle',
          })),
        },
      ],
    });
  }
}
