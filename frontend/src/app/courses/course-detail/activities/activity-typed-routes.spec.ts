/*
 * Copyright (c) 2026 Chandon Jarrett
 * SPDX-License-Identifier: MIT
 */

import { ACTIVITY_TYPED_ROUTES } from './activity-typed-routes';
import { ACTIVITY_TYPE_OPTIONS } from './activity-types';

describe('ACTIVITY_TYPED_ROUTES', () => {
  it('should generate an activity detail route for every registered activity type', () => {
    for (const activityTypeOption of ACTIVITY_TYPE_OPTIONS) {
      const expectedPath = `:activityId/${activityTypeOption.routeSegment}`;
      const route = ACTIVITY_TYPED_ROUTES.find((candidate) => candidate.path === expectedPath);

      expect(route).toBeTruthy();
      expect(route?.loadComponent).toBeTruthy();
    }
  });

  it('should generate a submission detail route for every registered activity type', () => {
    for (const activityTypeOption of ACTIVITY_TYPE_OPTIONS) {
      const expectedPath = `:activityId/${activityTypeOption.routeSegment}/submissions/:studentPid`;
      const route = ACTIVITY_TYPED_ROUTES.find((candidate) => candidate.path === expectedPath);

      expect(route).toBeTruthy();
      expect(route?.loadComponent).toBeTruthy();
    }
  });

  it('should generate create, edit, and submit routes for every registered activity type', () => {
    for (const activityTypeOption of ACTIVITY_TYPE_OPTIONS) {
      expect(
        ACTIVITY_TYPED_ROUTES.find(
          (candidate) => candidate.path === `create/${activityTypeOption.routeSegment}`,
        ),
      ).toBeTruthy();
      expect(
        ACTIVITY_TYPED_ROUTES.find(
          (candidate) => candidate.path === `:activityId/${activityTypeOption.routeSegment}/edit`,
        ),
      ).toBeTruthy();
      expect(
        ACTIVITY_TYPED_ROUTES.find(
          (candidate) => candidate.path === `:activityId/${activityTypeOption.routeSegment}/submit`,
        ),
      ).toBeTruthy();
    }
  });

  it('should sort generated routes by descending path depth', () => {
    const depths = ACTIVITY_TYPED_ROUTES.map((route) => route.path!.split('/').length);
    for (let index = 1; index < depths.length; index += 1) {
      expect(depths[index - 1]).toBeGreaterThanOrEqual(depths[index]);
    }
  });

  it('should lazily resolve every generated activity route component', async () => {
    for (const route of ACTIVITY_TYPED_ROUTES) {
      if (!route.loadComponent) {
        continue;
      }

      const loaded = await route.loadComponent();
      expect(loaded).toBeTruthy();
    }
  });
});
