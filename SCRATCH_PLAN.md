# Modeling Refactor Plan

## Part 1: Replace UUID Primary Key with 9-Digit PID

### Background

The current `User` table uses `uuid.UUID` as the primary key (`id` column) with
the PID stored as a separate indexed `str` column. We will drop the UUID column and
promote the PID to be the primary key.

**Integer type choice:** A 9-digit PID has a maximum value of 999,999,999. PostgreSQL
`INTEGER` (4 bytes, signed) tops out at 2,147,483,647. This comfortably holds all
9-digit values. `SMALLINT` (2 bytes, max 32,767) and even `BIGINT` (8 bytes) are
unnecessary. We will use **`INTEGER`** (`sa_column=Column(Integer, primary_key=True)`)
in SQLModel, which maps to PostgreSQL `int4`.

### Step-by-step

#### Step 1.1 — Update the `User` SQLModel table

**File:** `packages/learnwithai-core/src/learnwithai/tables/user.py`

- Remove the `uuid` import.
- Remove the `id: uuid.UUID` field with `default_factory=uuid.uuid4`.
- Remove the `pid: str = Field(index=True)` field.
- Add `pid: int = Field(primary_key=True)` as the new primary key.
  Use `sa_column=Column(Integer, primary_key=True, autoincrement=False)` to prevent
  Postgres from treating it as a serial. The PID is externally assigned.
- Keep all other fields (`name`, `onyen`, `family_name`, `given_name`, `email`,
  `updated_at`) unchanged.

#### Step 1.2 — Update `UserRepository`

**File:** `packages/learnwithai-core/src/learnwithai/repositories/user_repository.py`

- Remove `get_by_id(user_id: str)` — this looked up by UUID.
- Remove `get_by_pid(pid: str)` — the PID is now the primary key.
- Add `get_by_pid(pid: int) -> User | None` — looks up by PID (primary key).
- Keep `register_user` unchanged (it adds/flushes/refreshes).

#### Step 1.3 — Update `CSXLAuthService`

**File:** `packages/learnwithai-core/src/learnwithai/services/csxl_auth_service.py`

- In `verify_auth_token`: The upstream API returns `pid` as a string.
  Convert to `int` at this boundary: `pid = int(body["pid"])`.
  Update return type to `tuple[str, int]`.
- In `registered_user_from_onyen_pid(onyen: str, pid: int)`:
  Use `self._user_repo.get_by_pid(pid)`.
- In `_register_new_user(onyen: str, pid: int)`:
  Pass `pid=pid` (already an int) to the `User()` constructor.
- In `issue_jwt_token(user: User)`:
  Change `"sub": str(user.id)` → `"sub": str(user.pid)`.
  The JWT `sub` claim will now be the string representation of the PID.
- In `verify_jwt(token: str) -> int`:
  Change return type from `str` to `int`.
  Parse `user_id = int(payload["sub"])`.
- Remove `get_user_by_id(user_id: str)`.
  Add `get_user_by_pid(pid: int) -> User | None` delegating to repo.

#### Step 1.4 — Update API dependency injection

**File:** `api/src/api/dependency_injection.py`

- In `get_current_user`:
  - `verify_jwt` now returns an `int` (the PID).
  - Call `csxl_auth_svc.get_user_by_pid(pid)` instead of `get_user_by_id`.

#### Step 1.5 — Update `UserProfile` API model

**File:** `api/src/api/models/user_profile.py`

- Change `id: str` → `pid: int`.
  The frontend-facing profile now exposes the PID as the identifier.

#### Step 1.6 — Update API route: `auth.py`

**File:** `api/src/api/routes/auth.py`

- In `authenticate_with_csxl_callback`:
  - `verify_auth_token` now returns `(onyen: str, pid: int)`.
  - No other changes needed; the downstream calls already accept the new types.

#### Step 1.7 — Update the frontend `User` model

**File:** `frontend/src/app/user.model.ts`

- Remove `id: string`.
- Change `pid: string` → `pid: number`.
  The primary identifier is now `pid` (a number).

#### Step 1.8 — Update the frontend `AuthService` and `Home` component

**Files:**
- `frontend/src/app/auth.service.ts` — the `fetchProfile` call populates the
  user signal. No structural changes needed since the `User` interface changes
  propagate automatically.
- `frontend/src/app/home/home.ts` — No changes needed unless `user().id` is
  referenced; it should use `user().pid` or `user().name`.

#### Step 1.9 — Update all tests (core package)

**File:** `packages/learnwithai-core/test/test_user_repository.py`

- Remove tests for `get_by_id`.
- Update `get_by_pid` tests to use `pid: int` instead of `pid: str`.
- Update `register_user` tests: no more auto-generated UUID; supply `pid=` in User.
- Update assertions that referenced `result.id` to reference `result.pid`.

**File:** `packages/learnwithai-core/test/test_csxl_auth_service.py`

- `_make_user`: Remove `id=uuid.uuid4()`, add `pid=123456789` (int).
- `test_issue_jwt_token_returns_decodable_jwt`: Assert `decoded["sub"] == str(user.pid)`.
- `test_verify_jwt_returns_user_id_for_valid_token`: Assert returns `int(user.pid)`.
- `test_get_user_by_id_*` → rename to `test_get_user_by_pid_*`, use `int` pid.
- Remove `uuid` import.

#### Step 1.10 — Update all tests (API package)

**File:** `api/test/test_routes_auth.py`

- `_stub_user`: Remove `id=uuid.uuid4()`, add `pid=123456789` (int).
- Update `test_get_current_user_returns_user_for_valid_token`:
  Use `pid` instead of `uuid` for the JWT subject.
- Remove `uuid` import.

**File:** `api/test/test_routes_me.py`

- `_stub_user`: Remove `id` parameter, use `pid: int`.
- Update `test_get_current_user_profile_returns_user_profile`:
  Assert `pid=user.pid` in expected `UserProfile`.
- Remove `uuid` import.

#### Step 1.11 — Update frontend tests

**File:** `frontend/src/app/home/home.spec.ts`

- `fakeUser`: Remove `id`, change `pid` from string to number.

#### Step 1.12 — Run full QA suite

- Run `./scripts/qa.sh` (fix mode) to autoformat.
- Run `./scripts/qa.sh --check` to verify everything passes.
- Fix any remaining issues.

---

## Part 2: Add Course and Membership Models, Tables, and Repositories

### Background

We need a `Course` table and a `Membership` join table between `User` and `Course`.
Membership tracks the role a user plays in a course and the enrollment state.

### Step-by-step

#### Step 2.1 — Define the `Course` SQLModel table

**File:** `packages/learnwithai-core/src/learnwithai/tables/course.py` (new)

```python
"""Database-backed course models."""

from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Integer, func

class Course(SQLModel, table=True):
    """Represents a course in the system."""

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    name: str = Field()
    term: str = Field()           # e.g. "Fall 2026", "Spring 2027"
    section: str = Field()        # e.g. "001"
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        default=None,
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        default=None,
    )
```

#### Step 2.2 — Define enums for membership

**File:** `packages/learnwithai-core/src/learnwithai/tables/membership.py` (new)

```python
"""Database-backed membership (user-course join) models."""

import enum
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, func

class MembershipType(str, enum.Enum):
    INSTRUCTOR = "instructor"
    TA = "ta"
    STUDENT = "student"

class MembershipState(str, enum.Enum):
    ENROLLED = "enrolled"
    DROPPED = "dropped"

class Membership(SQLModel, table=True):
    """Join table linking users to courses with role and state."""

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    user_pid: int = Field(
        sa_column=Column(Integer, ForeignKey("user.pid"), nullable=False),
    )
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id"), nullable=False),
    )
    type: MembershipType = Field(
        sa_column=Column(Enum(MembershipType), nullable=False),
    )
    state: MembershipState = Field(
        sa_column=Column(
            Enum(MembershipState),
            nullable=False,
            server_default=MembershipState.ENROLLED.value,
        ),
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        default=None,
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        default=None,
    )
```

#### Step 2.3 — Create `CourseRepository`

**File:** `packages/learnwithai-core/src/learnwithai/repositories/course_repository.py` (new)

Methods:
- `create(course: Course) -> Course` — insert and return with DB defaults.
- `get_by_id(course_id: int) -> Course | None` — lookup by PK.
- `update(course: Course) -> Course` — merge, flush, refresh.
- `delete(course_id: int) -> None` — delete by PK.

#### Step 2.4 — Create `MembershipRepository`

**File:** `packages/learnwithai-core/src/learnwithai/repositories/membership_repository.py` (new)

Methods:
- `create(membership: Membership) -> Membership` — insert and return.
- `get_by_id(membership_id: int) -> Membership | None` — lookup by PK.
- `get_by_user_and_course(user_pid: int, course_id: int) -> Membership | None` — lookup on the join.
- `update(membership: Membership) -> Membership` — merge, flush, refresh.
- `delete(membership_id: int) -> None` — delete by PK.

#### Step 2.5 — Write integration tests for `CourseRepository`

**File:** `packages/learnwithai-core/test/test_course_repository.py` (new)

Tests:
- Create a course and verify returned fields / DB defaults.
- Get by ID returns the course.
- Get by ID returns None when not found.
- Update modifies the course name.
- Delete removes the course.

#### Step 2.6 — Write integration tests for `MembershipRepository`

**File:** `packages/learnwithai-core/test/test_membership_repository.py` (new)

Tests:
- Create a membership and verify returned fields.
- Get by ID returns the membership.
- Get by user and course returns the membership.
- Get by user and course returns None when not found.
- Update changes membership state (e.g. enrolled → dropped).
- Delete removes the membership.

#### Step 2.7 — Wire new tables into the DB metadata

Ensure `Course` and `Membership` tables are imported before `SQLModel.metadata.create_all`
is called. Update test fixtures if needed so the integration test session creates
all tables.

#### Step 2.8 — Run full QA suite

- Run `./scripts/qa.sh` (fix mode) to autoformat.
- Run `./scripts/qa.sh --check` to verify everything passes.
- Fix any remaining issues.

---

## Part 3: Next Steps and Suggestions

### 3.1 — Course Service Layer

Create a `CourseService` in `packages/learnwithai-core/src/learnwithai/services/` that
orchestrates course operations with access control:

- **`create_course(user: User, name, term, section) -> Course`**
  Only instructors (or a future admin role) should be able to create courses.
  Initially, the creator is automatically enrolled as the instructor.
- **`add_member(user: User, course_id, target_pid, membership_type) -> Membership`**
  Only the instructor of the course can add members (students, TAs).
- **`drop_member(user: User, course_id, target_pid) -> Membership`**
  Instructor can drop members. Students can drop themselves.
- **`get_my_courses(user: User) -> list[Course]`**
  Returns all courses where the user has an active (enrolled) membership.
- **`get_course_roster(user: User, course_id) -> list[Membership]`**
  Only instructor/TA of the course can view the full roster.

### 3.2 — Access Control Design

Implement a simple, cross-cutting access control pattern at the service layer:

1. **Every service method receives the authenticated `User` as its first argument.**
   The API route handler obtains the user via `CurrentUserDI` and passes it through.

2. **Authorization checks happen inside the service method**, not in the route handler.
   This keeps the logic testable and prevents routes from becoming authorization gatekeepers.

3. **A helper function `require_membership(user, course_id, allowed_types)`** can be
   shared across methods:
   ```python
   def _require_membership(
       self, user_pid: int, course_id: int, allowed_types: set[MembershipType]
   ) -> Membership:
       membership = self._membership_repo.get_by_user_and_course(user_pid, course_id)
       if membership is None or membership.state != MembershipState.ENROLLED:
           raise PermissionError("Not a member of this course")
       if membership.type not in allowed_types:
           raise PermissionError("Insufficient permissions")
       return membership
   ```

4. **Raise domain exceptions** (`PermissionError` or a custom `AuthorizationError`)
   from the service layer. The API layer catches these and returns 403.

### 3.3 — API Routes for Courses

Create routes in `api/src/api/routes/courses.py`:

- `POST /api/courses` — create a course (authenticated user becomes instructor).
- `GET /api/courses` — list courses for the current user.
- `GET /api/courses/{id}/roster` — get course roster (instructor/TA only).
- `POST /api/courses/{id}/members` — add a member (instructor only).
- `DELETE /api/courses/{id}/members/{pid}` — drop a member.

### 3.4 — Frontend Course Views

- **Course list page** (`/courses`) — shows enrolled courses grouped by term.
- **Course detail page** (`/courses/:id`) — shows roster for instructors, basic info
  for students.
- **Create course form** — simple reactive form for course name, term, section.
- **Add member form** — search by PID, select role (student/TA).

### 3.5 — Future Considerations

- **Bulk enrollment** — import a CSV of PIDs to enroll students.
- **Audit logging** — track who added/dropped whom and when.
- **Role-based route guards** on the frontend to prevent unauthorized navigation.
- **Pagination** on roster endpoints for large courses.
