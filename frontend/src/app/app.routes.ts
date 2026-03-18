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
        path: 'courses/:id/add-member',
        loadComponent: () =>
          import('./courses/add-member/add-member.component').then((m) => m.AddMember),
      },
      {
        path: 'courses/:id',
        loadComponent: () =>
          import('./courses/course-detail/course-detail.component').then((m) => m.CourseDetail),
      },
      {
        path: 'courses',
        loadComponent: () =>
          import('./courses/course-list/course-list.component').then((m) => m.CourseList),
      },
      {
        path: '',
        loadComponent: () => import('./home/home.component').then((m) => m.Home),
      },
    ],
  },
];
