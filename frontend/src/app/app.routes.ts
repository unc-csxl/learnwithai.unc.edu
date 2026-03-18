import { Routes } from '@angular/router';

/** Declares the top-level lazy routes for the frontend application. */
export const routes: Routes = [
  {
    path: 'jwt',
    loadComponent: () => import('./jwt/jwt.component').then((m) => m.Jwt),
  },
  {
    path: '',
    loadComponent: () => import('./layout/layout.component').then((m) => m.Layout),
    children: [
      {
        path: 'courses/create',
        loadComponent: () =>
          import('./courses/create-course/create-course.component').then((m) => m.CreateCourse),
      },
      {
        path: 'courses/:id',
        loadComponent: () =>
          import('./courses/course-detail/course-detail.component').then((m) => m.CourseDetail),
        children: [
          {
            path: 'roster',
            loadComponent: () =>
              import('./courses/course-detail/roster/roster.component').then((m) => m.Roster),
          },
          {
            path: 'add-member',
            loadComponent: () =>
              import('./courses/add-member/add-member.component').then((m) => m.AddMember),
          },
          {
            path: 'activities',
            loadComponent: () =>
              import('./courses/course-detail/activities/activities.component').then(
                (m) => m.Activities,
              ),
          },
          {
            path: 'tools',
            loadComponent: () =>
              import('./courses/course-detail/tools/tools.component').then((m) => m.Tools),
          },
          {
            path: 'student',
            loadComponent: () =>
              import('./courses/course-detail/student/student-view.component').then(
                (m) => m.StudentView,
              ),
          },
          { path: '', redirectTo: 'roster', pathMatch: 'full' },
        ],
      },
      {
        path: 'courses',
        loadComponent: () =>
          import('./courses/course-list/course-list.component').then((m) => m.CourseList),
      },
      { path: '', redirectTo: 'courses', pathMatch: 'full' },
    ],
  },
];
