import { Routes } from '@angular/router';

/** Declares the top-level lazy routes for the frontend application. */
export const routes: Routes = [
  {
    path: 'jwt',
    loadComponent: () => import('./jwt/jwt').then((m) => m.Jwt),
  },
  {
    path: 'courses/create',
    loadComponent: () =>
      import('./courses/create-course/create-course').then((m) => m.CreateCourse),
  },
  {
    path: 'courses/:id/add-member',
    loadComponent: () => import('./courses/add-member/add-member').then((m) => m.AddMember),
  },
  {
    path: 'courses/:id',
    loadComponent: () =>
      import('./courses/course-detail/course-detail').then((m) => m.CourseDetail),
  },
  {
    path: 'courses',
    loadComponent: () => import('./courses/course-list/course-list').then((m) => m.CourseList),
  },
  {
    path: '',
    loadComponent: () => import('./home/home').then((m) => m.Home),
  },
];
