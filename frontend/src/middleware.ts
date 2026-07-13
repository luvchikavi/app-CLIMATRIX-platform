import { NextRequest, NextResponse } from 'next/server';

/**
 * Next.js middleware for route protection.
 *
 * Checks for the `climatrix_auth` cookie flag (set by auth store on login).
 * Redirects unauthenticated users to /login before the page loads,
 * avoiding the flash of loading spinners on protected routes.
 *
 * The app root hosts no marketing landing — marketing lives at
 * https://climatrix.co. "/" routes straight to the dashboard when
 * authenticated, /login otherwise. Legacy deep links from the retired
 * landing (/?login=true, /?register=true, /?reset=true, /register) are
 * mapped onto /login so old emails and bookmarks keep working.
 *
 * This is a fast-path check only — the actual JWT validation still happens
 * client-side via Zustand rehydration + api.validateToken().
 */

const PUBLIC_PATHS = new Set([
  '/login',
  '/try',
  '/cbam-check',
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
  const { pathname, searchParams } = request.nextUrl;
  const hasAuth = request.cookies.get('climatrix_auth');

  // Root: no landing page anymore — route by auth state. Preserve the
  // retired landing's query flags (register/reset) on the way to /login.
  if (pathname === '/') {
    if (hasAuth && !searchParams.get('reset')) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
    const loginUrl = new URL('/login', request.url);
    for (const flag of ['register', 'reset']) {
      if (searchParams.get(flag) === 'true') loginUrl.searchParams.set(flag, 'true');
    }
    return NextResponse.redirect(loginUrl);
  }

  // Legacy /register links (old website builds) → register mode on /login,
  // keeping any extra params (e.g. ?plan=starter from pricing CTAs).
  if (pathname === '/register') {
    const loginUrl = new URL('/login', request.url);
    searchParams.forEach((v, k) => loginUrl.searchParams.set(k, v));
    loginUrl.searchParams.set('register', 'true');
    return NextResponse.redirect(loginUrl);
  }

  // Allow public routes, static assets, and API calls.
  // /supplier-data/{token} is the public CBAM supplier magic-link form —
  // suppliers have no account, so it must never redirect to login.
  if (
    PUBLIC_PATHS.has(pathname) ||
    pathname.startsWith('/supplier-data/') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // Check for auth cookie flag
  if (!hasAuth) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Match all routes except static files and api
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
