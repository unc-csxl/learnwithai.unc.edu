/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { buildActivityContextNav } from './activity-nav';
import { ACTIVITY_TYPE_OPTIONS } from './activity-types';

describe('buildActivityContextNav', () => {
  const baseOptions = { courseId: 1, activityId: 10 };
  const defaultRouteSegment = ACTIVITY_TYPE_OPTIONS[0].routeSegment;

  it('should produce 3 sibling items for staff', () => {
    const result = buildActivityContextNav({ ...baseOptions, role: 'staff' });

    expect(result.visibleBaseRoutes).toEqual(['/courses/1/dashboard', '/courses/1/activities']);
    expect(result.groups).toHaveLength(1);

    const items = result.groups[0].items;
    expect(items).toHaveLength(3);
    expect(items[0]).toEqual(
      expect.objectContaining({
        route: `/courses/1/activities/10/${defaultRouteSegment}`,
        label: 'Submissions',
      }),
    );
    expect(items[1]).toEqual(
      expect.objectContaining({
        route: `/courses/1/activities/10/${defaultRouteSegment}/edit`,
        label: 'Activity Editor',
      }),
    );
    expect(items[2]).toEqual(
      expect.objectContaining({
        route: `/courses/1/activities/10/${defaultRouteSegment}/submit`,
        label: 'Preview & Test',
      }),
    );
  });

  it('should produce 1 item for student', () => {
    const result = buildActivityContextNav({ ...baseOptions, role: 'student' });

    expect(result.visibleBaseRoutes).toEqual(['/courses/1/student', '/courses/1/activities']);
    expect(result.groups).toHaveLength(1);

    const items = result.groups[0].items;
    expect(items).toHaveLength(1);
    expect(items[0]).toEqual(
      expect.objectContaining({
        route: `/courses/1/activities/10/${defaultRouteSegment}/submit`,
        label: 'Submissions',
      }),
    );
  });

  it('should append extra groups', () => {
    const extraGroups = [
      {
        label: 'Submission',
        items: [
          {
            route: `/courses/1/activities/10/${defaultRouteSegment}/submissions/111`,
            label: 'Student 111',
            icon: 'person',
          },
        ],
      },
    ];
    const result = buildActivityContextNav({ ...baseOptions, role: 'staff', extraGroups });

    expect(result.groups).toHaveLength(2);
    expect(result.groups[0].label).toBe('Current activity');
    expect(result.groups[1]).toEqual(
      expect.objectContaining({ label: 'Submission', items: extraGroups[0].items }),
    );
  });

  it('should label the group "Current activity"', () => {
    const result = buildActivityContextNav({ ...baseOptions, role: 'staff' });
    expect(result.groups[0].label).toBe('Current activity');
  });

  it('should default unknown activity types to the registry default routes', () => {
    const result = buildActivityContextNav({
      ...baseOptions,
      activityType: 'custom',
      role: 'staff',
    });

    const items = result.groups[0].items;
    expect(items[0]).toEqual(
      expect.objectContaining({
        route: `/courses/1/activities/10/${defaultRouteSegment}`,
        label: 'Submissions',
      }),
    );
    expect(items[1]).toEqual(
      expect.objectContaining({ route: `/courses/1/activities/10/${defaultRouteSegment}/edit` }),
    );
    expect(items[2]).toEqual(
      expect.objectContaining({
        route: `/courses/1/activities/10/${defaultRouteSegment}/submit`,
      }),
    );
  });
});
