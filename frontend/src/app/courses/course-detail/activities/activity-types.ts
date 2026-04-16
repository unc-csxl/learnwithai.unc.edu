/*
 * Copyright (c) 2026 Chandon Jarrett
 * SPDX-License-Identifier: MIT
 */

/** Describes an activity type that can be created from the activities UI. */
export interface ActivityTypeOption {
  id: string;
  label: string;
  description: string;
}

/** Registry of activity types currently supported by activity creation. */
export const ACTIVITY_TYPE_OPTIONS: readonly ActivityTypeOption[] = [
  {
    id: 'iyow',
    label: 'In Your Own Words',
    description: 'Students write a response and receive AI feedback.',
  },
];
