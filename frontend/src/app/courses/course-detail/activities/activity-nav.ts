import {
  LayoutNavigationGroup,
  LayoutNavigationSection,
} from '../../../layout/layout-navigation.service';

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
  activityTitle: string;
  role: 'staff' | 'student';
  extraGroups?: LayoutNavigationGroup[];
}): LayoutNavigationSection {
  const { courseId, activityId, activityTitle, role, extraGroups } = options;
  const base = `/courses/${courseId}/activities/${activityId}`;
  const isStaff = role === 'staff';

  const activityGroup: LayoutNavigationGroup = {
    label: 'Current activity',
    items: isStaff
      ? [
          {
            route: base,
            label: activityTitle,
            description: 'Open this activity overview',
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
            label: activityTitle,
            description: 'Open this student activity',
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
