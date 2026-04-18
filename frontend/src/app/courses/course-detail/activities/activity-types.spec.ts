/*
 * Copyright (c) 2026 Chandon Jarrett
 * SPDX-License-Identifier: MIT
 */

import {
  ACTIVITY_TYPE_OPTIONS,
  activityBasePathForTypeId,
  activityDetailRouteParts,
  activitySubmissionRouteParts,
  activitySubmitRouteParts,
  activityTypeOptionForBackendType,
  routeSegmentForActivityType,
} from './activity-types';

describe('activity-types', () => {
  const defaultType = ACTIVITY_TYPE_OPTIONS[0];

  it('should expose a non-empty registry of activity types', () => {
    expect(ACTIVITY_TYPE_OPTIONS.length).toBeGreaterThan(0);
    expect(defaultType).toEqual(
      expect.objectContaining({
        backendType: expect.any(String),
        routeSegment: expect.any(String),
        loaders: expect.objectContaining({
          create: expect.any(Function),
          detail: expect.any(Function),
          edit: expect.any(Function),
          submit: expect.any(Function),
          submissionDetail: expect.any(Function),
        }),
      }),
    );
  });

  it('should resolve known backend types to their route option', () => {
    expect(activityTypeOptionForBackendType(defaultType.backendType)).toEqual(defaultType);
    expect(routeSegmentForActivityType(defaultType.backendType)).toBe(defaultType.routeSegment);
  });

  it('should fall back to the default option for unknown backend types', () => {
    expect(activityTypeOptionForBackendType('does-not-exist')).toEqual(ACTIVITY_TYPE_OPTIONS[0]);
    expect(routeSegmentForActivityType('does-not-exist')).toBe(
      ACTIVITY_TYPE_OPTIONS[0].routeSegment,
    );
  });

  it('should build detail, submit, and submission route parts from activity type', () => {
    expect(activityDetailRouteParts(defaultType.backendType, 42)).toEqual([
      '42',
      defaultType.routeSegment,
    ]);
    expect(activitySubmitRouteParts(defaultType.backendType, 42)).toEqual([
      '42',
      defaultType.routeSegment,
      'submit',
    ]);
    expect(activitySubmissionRouteParts(defaultType.backendType, 42, 7)).toEqual([
      '42',
      defaultType.routeSegment,
      'submissions',
      '7',
    ]);
  });

  it('should build absolute activity base paths using type ids with fallback', () => {
    expect(activityBasePathForTypeId(1, 10, defaultType.backendType)).toBe(
      `/courses/1/activities/10/${defaultType.routeSegment}`,
    );
    expect(activityBasePathForTypeId(1, 10, 'unknown-type-id')).toBe(
      `/courses/1/activities/10/${defaultType.routeSegment}`,
    );
  });
});
