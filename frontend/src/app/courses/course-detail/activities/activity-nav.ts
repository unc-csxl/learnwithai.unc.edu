/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import {
  LayoutNavigationGroup,
  LayoutNavigationSection,
} from '../../../layout/layout-navigation.service';
import { activityBasePathForTypeId } from './activity-types';

/**
 * Builds the sidebar navigation context for an existing activity's sub-pages.
 *
 * Enforces the sidenav sibling axiom: every leaf page shows all its siblings
 * plus ancestral parents back to the root. Centralising the group here means
 * individual activity pages cannot accidentally omit a sibling link.
 */
export function buildActivityContextNav(options: {
  courseId: number;
  activityId: number;
  activityType?: string;
  role: 'staff' | 'student';
  extraGroups?: LayoutNavigationGroup[];
}): LayoutNavigationSection {
  const { courseId, activityId, activityType, role, extraGroups } = options;
  const base = activityBasePathForTypeId(courseId, activityId, activityType);
  const isStaff = role === 'staff';

  const activityGroup: LayoutNavigationGroup = {
    label: 'Current activity',
    items: isStaff
      ? [
          {
            route: base,
            label: 'Submissions',
            description: 'Open this activity submissions view',
            icon: 'assignment',
          },
          {
            route: `${base}/edit`,
            label: 'Activity Editor',
            description: 'Edit this activity',
            icon: 'edit',
          },
          {
            route: `${base}/submit`,
            label: 'Preview & Test',
            description: 'Preview and test this activity',
            icon: 'preview',
          },
        ]
      : [
          {
            route: `${base}/submit`,
            label: 'Submissions',
            description: 'Open your submission view',
            icon: 'assignment',
          },
        ],
  };

  const dashboardRoute = isStaff
    ? `/courses/${courseId}/dashboard`
    : `/courses/${courseId}/student`;

  return {
    visibleBaseRoutes: [dashboardRoute, `/courses/${courseId}/activities`],
    groups: [activityGroup, ...(extraGroups ?? [])],
  };
}
