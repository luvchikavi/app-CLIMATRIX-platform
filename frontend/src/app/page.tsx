import { redirect } from 'next/navigation';

/**
 * The app root no longer hosts a marketing landing — marketing lives at
 * https://climatrix.co. Middleware normally routes "/" before this page
 * renders (dashboard when authenticated, login otherwise); this redirect
 * is the fallback for anything that slips through.
 */
export default function RootPage() {
  redirect('/login');
}
