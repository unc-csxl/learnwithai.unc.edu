export interface Course {
  id: number;
  name: string;
  term: string;
  section: string;
}

export interface CreateCourseRequest {
  name: string;
  term: string;
  section: string;
}

export type MembershipType = 'instructor' | 'ta' | 'student';
export type MembershipState = 'pending' | 'enrolled' | 'dropped';

export interface Membership {
  user_pid: number;
  course_id: number;
  type: MembershipType;
  state: MembershipState;
}

export interface AddMemberRequest {
  pid: number;
  type: MembershipType;
}
