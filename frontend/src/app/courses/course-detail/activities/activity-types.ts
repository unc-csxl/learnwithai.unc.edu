/*
 * Copyright (c) 2026 Chandon Jarrett
 * SPDX-License-Identifier: MIT
 */

import type { Routes } from '@angular/router';

/** Describes an activity type that can be created from the activities UI. */
export interface ActivityTypeOption {
  backendType: string;
  routeSegment: string;
  label: string;
  description: string;
  loaders: {
    create: NonNullable<Routes[number]['loadComponent']>;
    detail: NonNullable<Routes[number]['loadComponent']>;
    edit: NonNullable<Routes[number]['loadComponent']>;
    submit: NonNullable<Routes[number]['loadComponent']>;
    submissionDetail: NonNullable<Routes[number]['loadComponent']>;
  };
}

/** Registry of activity types currently supported by activity creation. */
export const ACTIVITY_TYPE_OPTIONS: readonly ActivityTypeOption[] = [
  {
    backendType: 'iyow',
    routeSegment: 'iyow',
    label: 'In Your Own Words',
    description: 'Students write a response and receive AI feedback.',
    loaders: {
      create: () => import('./iyow/create/create-iyow.component').then((m) => m.CreateIyow),
      detail: () =>
        import('./iyow/detail/iyow-activity-detail.component').then((m) => m.IyowActivityDetail),
      edit: () => import('./iyow/edit/edit-iyow.component').then((m) => m.EditIyow),
      submit: () => import('./iyow/submit/iyow-submit.component').then((m) => m.IyowSubmit),
      submissionDetail: () =>
        import('./iyow/submission-detail/iyow-submission-detail.component').then(
          (m) => m.IyowSubmissionDetail,
        ),
    },
  },
];

const DEFAULT_ACTIVITY_TYPE_OPTION = ACTIVITY_TYPE_OPTIONS[0];

/** Maps backend activity type values to route path segments. */
export function routeSegmentForActivityType(activityType: string): string {
  return activityTypeOptionForBackendType(activityType).routeSegment;
}

/** Resolves the route descriptor for a backend activity type, defaulting to the first registry entry. */
export function activityTypeOptionForBackendType(activityType: string): ActivityTypeOption {
  return (
    ACTIVITY_TYPE_OPTIONS.find(
      (activityTypeOption) => activityTypeOption.backendType === activityType,
    ) ?? DEFAULT_ACTIVITY_TYPE_OPTION
  );
}

/** Returns route parts for an activity detail page based on backend type. */
export function activityDetailRouteParts(
  activityType: string,
  activityId: number | string,
): string[] {
  const option = activityTypeOptionForBackendType(activityType);
  return [String(activityId), option.routeSegment];
}

/** Returns route parts for an activity submit page based on backend type. */
export function activitySubmitRouteParts(
  activityType: string,
  activityId: number | string,
): string[] {
  return [...activityDetailRouteParts(activityType, activityId), 'submit'];
}

/** Returns route parts for an instructor submission detail page based on backend type. */
export function activitySubmissionRouteParts(
  activityType: string,
  activityId: number | string,
  studentPid: number | string,
): string[] {
  return [...activityDetailRouteParts(activityType, activityId), 'submissions', String(studentPid)];
}

/** Builds the activity base path for a known backend activity type. */
export function activityBasePathForTypeId(
  courseId: number,
  activityId: number,
  activityTypeId: string = '',
): string {
  const routeSegment = routeSegmentForActivityType(activityTypeId);
  return `/courses/${courseId}/activities/${activityId}/${routeSegment}`;
}
