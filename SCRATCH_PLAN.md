# Scratch Plan

## Phase 1 — OpenAPI Client Codegen (Complete)

Generated frontend HTTP client and models from FastAPI OpenAPI spec via
`ng-openapi-gen`. Domain barrel in `src/app/api/models.ts`. Services use
`Api.invoke()`. All complete.

## Phase 2 — Domain Model Aliases (Complete)

Barrel file maps wire-format names to clean domain names. Services return
`Promise<T>`. All complete.

---

## Phase 3 — Frontend UI Sprint

### Goals

1. Angular Material as the component/design framework
2. Tailwind CSS for utility styling alongside Material
3. App shell: toolbar + responsive sidenav (desktop visible, mobile collapsible)
4. Rename component `.ts` files to `.component.ts` (Angular standard convention)
5. Route organization: course list → course detail with instructor/student views
6. Accessible theme with high-visibility focus, system-default light/dark toggle

### Step-by-step Plan

#### Step 1: Install Dependencies + Configure Material & Tailwind

- `ng add @angular/material` (or manual install + configure)
- Install `@angular/cdk` (comes with Material)
- Configure a custom Material theme (light + dark) in `styles.css`
- Ensure Tailwind v4 and Material coexist (Tailwind for utilities, Material for components)
- **Commit:** "feat: add Angular Material and configure theme"

#### Step 2: Rename Component Files to Standard Convention

- Rename `*.ts` → `*.component.ts` for all components (not services/interceptors)
- Rename `*.html` → `*.component.html` for templates
- Rename `*.spec.ts` → `*.component.spec.ts` for component tests
- Update all `templateUrl`, import paths, and route lazy-load paths
- Keep `app.ts` → `app.component.ts` (and its template/style files)
- **Commit:** "refactor: rename components to standard Angular file convention"

#### Step 3: Build the App Shell (Toolbar + Sidenav)

- Create a `LayoutComponent` with `MatToolbar`, `MatSidenav`, `MatSidenavContainer`
- Toolbar: app title, theme toggle button, user menu (login/logout)
- Sidenav: navigation links (Courses). Responsive: always open on desktop,
  drawer on mobile (use `BreakpointObserver` from CDK)
- Wrap routed content inside the layout
- Update `AppComponent` to use the layout
- **Commit:** "feat: add responsive app shell with toolbar and sidenav"

#### Step 4: Theme — Light/Dark Toggle with High-Visibility Focus

- Define Material light + dark color palettes
- System-default preference via `prefers-color-scheme` media query
- Toggle button in toolbar to override
- Persist preference in `localStorage`
- High-visibility focus: `:focus-visible` outline with strong contrast ring
- Meets WCAG AA contrast minimums
- **Commit:** "feat: add light/dark theme toggle with high-visibility focus"

#### Step 5: Restructure Routes and Course Navigation

- Course list is the main authenticated view (like Gradescope dashboard)
- Course detail becomes a parent route with child views:
  - Instructor view: roster, activities (placeholder), tools (placeholder)
  - Student view: placeholder
- Sidenav within course context shows course-specific navigation
- Move `create-course` and `add-member` into appropriate locations
- Home page redirects authenticated users to `/courses`
- **Commit:** "feat: restructure routes with course navigation hierarchy"

#### Step 6: Migrate Existing Components to Use Material

- CourseList: use `MatCard` for course cards, `MatButton` for actions
- CourseDetail/Roster: use `MatTable` for roster display
- CreateCourse: use `MatFormField`, `MatInput`, `MatButton`
- AddMember: use `MatFormField`, `MatInput`, `MatSelect`, `MatButton`
- Home: use Material buttons and typography
- **Commit:** "feat: migrate components to Angular Material"

#### Step 7: Update All Tests

- Update specs for new file paths
- Add tests for LayoutComponent
- Add tests for theme service
- Verify all existing tests pass with Material imports
- **Commit:** "test: update all tests for Material migration"

#### Step 8: Final Validation

- `pnpm format:check && pnpm lint && pnpm test:ci` from frontend/
- `./scripts/qa.sh --check` from repo root
- **Commit:** any final fixes

### Constraints

- Lean on Material's default design system — minimal custom CSS
- Tailwind only for utility classes (spacing, layout, flex) not for replacing Material
- No over-engineering: placeholders are fine for unbuilt features
- 100% test coverage maintained
- Accessibility: WCAG AA, visible focus rings, ARIA attributes

