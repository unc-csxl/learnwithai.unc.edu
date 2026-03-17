import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthTokenService } from './auth-token.service';

function isApiRequest(url: string): boolean {
  return url === '/api' || url.startsWith('/api/');
}

/** Attaches the persisted bearer token to same-app API requests. */
export const authTokenInterceptor: HttpInterceptorFn = (request, next) => {
  const tokenService = inject(AuthTokenService);
  const token = tokenService.getToken();

  if (!token || !isApiRequest(request.url) || request.headers.has('Authorization')) {
    return next(request);
  }

  return next(
    request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    }),
  );
};
