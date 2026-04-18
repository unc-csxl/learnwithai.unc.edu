/*
 * Copyright (c) 2026 Chandon Jarrett
 * SPDX-License-Identifier: MIT
 */

import { Routes } from '@angular/router';
import { ACTIVITY_TYPE_OPTIONS } from './activity-types';

/** Activity routes generated from the activity type registry. */
export const ACTIVITY_TYPED_ROUTES: Routes = ACTIVITY_TYPE_OPTIONS.flatMap((activityTypeOption) => {
  const routeSegment = activityTypeOption.routeSegment;
  const loaders = activityTypeOption.loaders;

  return [
    {
      path: `create/${routeSegment}`,
      loadComponent: loaders.create,
    },
    {
      path: `:activityId/${routeSegment}`,
      loadComponent: loaders.detail,
    },
    {
      path: `:activityId/${routeSegment}/edit`,
      loadComponent: loaders.edit,
    },
    {
      path: `:activityId/${routeSegment}/submit`,
      loadComponent: loaders.submit,
    },
    {
      path: `:activityId/${routeSegment}/submissions/:studentPid`,
      loadComponent: loaders.submissionDetail,
    },
  ];
}).sort((left, right) => right.path!.split('/').length - left.path!.split('/').length);
