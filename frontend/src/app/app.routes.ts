import { Routes } from '@angular/router';
import { authGuard, landingGuard } from './auth.guard';

/** Declares the top-level lazy routes for the frontend application. */
export const routes: Routes = [
  {
    path: 'jwt',
    loadComponent: () => import('./jwt/jwt.component').then((m) => m.Jwt),
  },
  {
    path: '',
    pathMatch: 'full',
    canActivate: [landingGuard],
    loadComponent: () => import('./landing/landing.component').then((m) => m.Landing),
  },
  {
    path: '',
    loadComponent: () => import('./layout/layout.component').then((m) => m.Layout),
    canActivate: [authGuard],
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
            path: 'dashboard',
            loadComponent: () =>
              import('./courses/course-detail/dashboard/dashboard.component').then(
                (m) => m.Dashboard,
              ),
          },
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
            children: [
              {
                path: '',
                loadComponent: () =>
                  import('./courses/course-detail/activities/activities.component').then(
                    (m) => m.Activities,
                  ),
              },
              {
                path: 'create-iyow',
                loadComponent: () =>
                  import('./courses/course-detail/activities/create-iyow/create-iyow.component').then(
                    (m) => m.CreateIyow,
                  ),
              },
              {
                path: ':activityId',
                loadComponent: () =>
                  import('./courses/course-detail/activities/activity-detail/activity-detail.component').then(
                    (m) => m.ActivityDetail,
                  ),
              },
              {
                path: ':activityId/submit',
                loadComponent: () =>
                  import('./courses/course-detail/activities/iyow-submit/iyow-submit.component').then(
                    (m) => m.IyowSubmit,
                  ),
              },
            ],
          },
          {
            path: 'tools',
            children: [
              {
                path: '',
                loadComponent: () =>
                  import('./courses/course-detail/tools/tools.component').then((m) => m.Tools),
              },
              {
                path: 'joke-generator',
                loadComponent: () =>
                  import('./courses/course-detail/tools/joke-generator/joke-generator.component').then(
                    (m) => m.JokeGenerator,
                  ),
              },
            ],
          },
          {
            path: 'settings',
            loadComponent: () =>
              import('./courses/course-detail/settings/settings.component').then((m) => m.Settings),
          },
          {
            path: 'student',
            loadComponent: () =>
              import('./courses/course-detail/student/student-view.component').then(
                (m) => m.StudentView,
              ),
          },
          { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
        ],
      },
      {
        path: 'profile',
        loadComponent: () =>
          import('./profile/profile-editor.component').then((m) => m.ProfileEditor),
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
