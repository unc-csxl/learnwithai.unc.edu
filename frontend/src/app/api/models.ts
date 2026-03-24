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
export type { MembershipState } from './generated/models/membership-state';
