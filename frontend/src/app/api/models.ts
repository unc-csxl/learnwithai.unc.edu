/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

/**
 * Domain-friendly re-exports of generated API models.
 *
 * Import from here instead of reaching into `api/generated/models/` directly.
 * This barrel strips transport-layer suffixes (Response, Request) so that
 * services and components think in domain terms.
 */

export type { CourseResponse as Course } from './generated/models/course-response';
export type { CourseMembership } from './generated/models/course-membership';
export type { CreateCourseRequest as CreateCourse } from './generated/models/create-course-request';
export type { Term } from './generated/models/term';
export { TERM } from './generated/models/term-array';
export type { MembershipResponse as Membership } from './generated/models/membership-response';
export type { AddMemberRequest as AddMember } from './generated/models/add-member-request';
export type { UserProfile as User } from './generated/models/user-profile';
export type { MembershipType } from './generated/models/membership-type';
export { MEMBERSHIP_TYPE } from './generated/models/membership-type-array';
export type { MembershipState } from './generated/models/membership-state';
export type { RosterMemberResponse as RosterMember } from './generated/models/roster-member-response';
export type { PaginatedRosterResponse as PaginatedRoster } from './generated/models/paginated-roster-response';
export type { RosterUploadResponse as RosterUpload } from './generated/models/roster-upload-response';
export type { RosterUploadStatusResponse as RosterUploadStatus } from './generated/models/roster-upload-status-response';
export type { BodyUploadRosterCsv as UploadRosterCsvBody } from './generated/models/body-upload-roster-csv';
export type { UpdateProfileRequest as UpdateProfile } from './generated/models/update-profile-request';
export type { UpdateCourseRequest as UpdateCourse } from './generated/models/update-course-request';
export type { UpdateMemberRoleRequest as UpdateMemberRole } from './generated/models/update-member-role-request';
export type { CreateJokeRequest as CreateJoke } from './generated/models/create-joke-request';
export type { JokeResponse as JokeRequest } from './generated/models/joke-response';
export type { AsyncJobInfo } from './generated/models/async-job-info';
export type { AsyncJobStatus } from './generated/models/async-job-status';
export type { ActivityResponse as Activity } from './generated/models/activity-response';
export type { IyowActivityResponse as IyowActivity } from './generated/models/iyow-activity-response';
export type { IyowSubmissionResponse as IyowSubmission } from './generated/models/iyow-submission-response';
export type { CreateIyowActivityRequest as CreateIyowActivity } from './generated/models/create-iyow-activity-request';
export type { UpdateIyowActivityRequest as UpdateIyowActivity } from './generated/models/update-iyow-activity-request';
export type { SubmitIyowRequest as SubmitIyow } from './generated/models/submit-iyow-request';
export type { StudentSubmissionRow } from './generated/models/student-submission-row';

// Operator / Admin
export type { OperatorProfile } from './generated/models/operator-profile';
export type { OperatorResponse as Operator } from './generated/models/operator-response';
export type { OperatorRole } from './generated/models/operator-role';
export type { OperatorPermission } from './generated/models/operator-permission';
export type { GrantOperatorRequest as GrantOperator } from './generated/models/grant-operator-request';
export type { UpdateOperatorRoleRequest as UpdateOperatorRole } from './generated/models/update-operator-role-request';
export type { ImpersonationTokenResponse } from './generated/models/impersonation-token-response';
export type { UserSearchResult } from './generated/models/user-search-result';
export type { UsageMetricsResponse as UsageMetrics } from './generated/models/usage-metrics-response';

// Job Control
export type { JobControlOverviewResponse as JobControlOverview } from './generated/models/job-control-overview-response';
export type { QueueInfoResponse as QueueInfo } from './generated/models/queue-info-response';
export type { WorkerInfoResponse as WorkerInfo } from './generated/models/worker-info-response';
export type { JobFailuresResponse as JobFailures } from './generated/models/job-failures-response';
export type { RecentFailedJobResponse as RecentFailedJob } from './generated/models/recent-failed-job-response';
