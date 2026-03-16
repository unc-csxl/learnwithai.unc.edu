import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'jwt',
    loadComponent: () => import('./jwt/jwt').then((m) => m.Jwt),
  },
  {
    path: '',
    loadComponent: () => import('./home/home').then((m) => m.Home),
  },
];
