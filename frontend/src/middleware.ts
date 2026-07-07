import { NextRequest, NextResponse } from 'next/server';

/**
 * Next.js middleware for route protection.
 *
 * Checks for the `climatrix_auth` cookie flag (set by auth store on login).
 * Redirects unauthenticated users to the landing page before the page loads,
 * avoiding the flash of loading spinners on protected routes.
 *
 * This is a fast-path check only — the actual JWT validation still happens
 * client-side via Zustand rehydration + api.validateToken().
 */

const PUBLIC_PATHS = new Set([
  '/',
  '/try',
  '/pricing',
  '/terms',
  '/privacy',
  '/roadmap',
  '/forgot-password',
  '/reset-password',
  '/accept-invitation',
  '/security',
]);

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes, static assets, and API calls
  if (
    PUBLIC_PATHS.has(pathname) ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // Check for auth cookie flag
  const hasAuth = request.cookies.get('climatrix_auth');
  if (!hasAuth) {
    const loginUrl = new URL('/', request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Match all routes except static files and api
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
