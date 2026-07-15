'use client';

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: {
          initialize: (config: {
            client_id?: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

import { useState, useEffect, useRef, Suspense } from 'react';
import { useAuthStore } from '@/stores/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import { COUNTRIES } from '@/lib/countries';
import { Loader2 } from 'lucide-react';

const fieldLabel = 'mb-1.5 block text-[11px] font-bold tracking-[0.06em] uppercase text-cy-faint';
const fieldInput =
  'w-full rounded-[10px] border-0 bg-cy-row px-3 py-2.5 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent';

function LoginPageContent() {
  const searchParams = useSearchParams();
  const [isRegistering, setIsRegistering] = useState(searchParams.get('register') === 'true');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [countryCode, setCountryCode] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [googleReady, setGoogleReady] = useState(false);
  const { login, googleLogin, register, isLoading, error, clearError, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();
  const googleInitialized = useRef(false);

  useEffect(() => {
    if (searchParams.get('reset') === 'true') {
      logout();
    }
  }, [searchParams, logout]);

  useEffect(() => {
    if (isAuthenticated && !searchParams.get('reset')) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router, searchParams]);

  // Load Google Identity Services script
  useEffect(() => {
    const existingScript = document.getElementById('google-gsi-script');
    if (existingScript) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional state sync on mount; mirrors previous landing-page behavior
      if (window.google?.accounts?.id) setGoogleReady(true);
      else existingScript.addEventListener('load', () => setGoogleReady(true));
      return;
    }
    const script = document.createElement('script');
    script.id = 'google-gsi-script';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setGoogleReady(true);
    document.head.appendChild(script);
  }, []);

  // Initialize Google Sign-In and render the button when the script is ready
  useEffect(() => {
    if (!googleReady || !window.google?.accounts?.id) return;
    const container = document.getElementById('google-btn-container');
    if (!container) return;

    if (!googleInitialized.current) {
      window.google.accounts.id.initialize({
        client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID?.trim(),
        callback: async (response) => {
          try {
            await googleLogin(response.credential);
            router.push('/dashboard');
          } catch {
            // Error is handled by the store
          }
        },
      });
      googleInitialized.current = true;
    }

    container.innerHTML = '';
    window.google.accounts.id.renderButton(container, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      text: 'continue_with',
      shape: 'pill',
      // Always English — without this the button follows the browser locale
      // (Hebrew on Avi's machine) and breaks the login page's language.
      locale: 'en',
      width: Math.min(container.offsetWidth || 380, 400),
    });
  }, [googleReady, googleLogin, router]);

  if (isAuthenticated && !searchParams.get('reset')) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      if (isRegistering) {
        await register({
          email,
          password,
          full_name: fullName,
          organization_name: organizationName,
          country_code: countryCode || undefined,
        });
      } else {
        await login(email, password);
      }
      router.push('/dashboard');
    } catch {
      // Error is handled by the store
    }
  };

  const toggleMode = () => {
    setEmail('');
    setPassword('');
    setFullName('');
    setOrganizationName('');
    setCountryCode('');
    setTermsAccepted(false);
    clearError();
    setIsRegistering(!isRegistering);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4 text-foreground">
      <div className="w-full max-w-md">
        <div className="rounded-cy bg-background-elevated px-8 py-7 shadow-card">
          <div className="mb-6">
            <p className="text-[15px] font-extrabold tracking-[0.01em] text-cy-ink">
              climatri<span className="text-cy-accent">x</span>
            </p>
            <h1 className="mt-3 text-[17px] font-bold tracking-[-0.01em] text-foreground">
              {isRegistering ? 'Create your account' : 'Welcome back'}
            </h1>
            <p className="mt-0.5 text-[12.5px] text-cy-muted">
              {isRegistering
                ? 'Measure, plan and report — starting with one file.'
                : 'Sign in to your Climatrix account'}
            </p>
          </div>

          {/* Google Sign-In Button */}
          <div id="google-btn-container" className="mb-4 flex min-h-[44px] justify-center" />

          {/* Divider */}
          <div className="mb-4 flex items-center gap-4">
            <div className="h-px flex-1 bg-cy-row" />
            <span className="text-[10.5px] font-bold uppercase tracking-[0.08em] text-cy-faint">
              or with email
            </span>
            <div className="h-px flex-1 bg-cy-row" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegistering && (
              <>
                <div>
                  <label className={fieldLabel}>Full name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="John Smith"
                    required
                    className={fieldInput}
                  />
                </div>

                <div>
                  <label className={fieldLabel}>Organization name</label>
                  <input
                    type="text"
                    value={organizationName}
                    onChange={(e) => setOrganizationName(e.target.value)}
                    placeholder="Acme Corporation"
                    required
                    className={fieldInput}
                  />
                </div>

                <div>
                  <label className={fieldLabel}>Country (optional)</label>
                  <select
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                    className={fieldInput}
                  >
                    <option value="">Select country…</option>
                    {COUNTRIES.map((c) => (
                      <option key={c.code} value={c.code}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </>
            )}

            <div>
              <label className={fieldLabel}>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className={fieldInput}
              />
            </div>

            <div>
              <label className={fieldLabel}>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={isRegistering ? 'Create a password' : 'Enter your password'}
                required
                minLength={isRegistering ? 6 : undefined}
                className={fieldInput}
              />
              {isRegistering ? (
                <p className="mt-1 text-[11.5px] text-cy-faint">Minimum 6 characters</p>
              ) : (
                <div className="mt-2 flex justify-end">
                  <a
                    href="/forgot-password"
                    className="text-[12px] font-semibold text-cy-accent"
                  >
                    Forgot password?
                  </a>
                </div>
              )}
            </div>

            {isRegistering && (
              <div className="flex items-start gap-2.5">
                <input
                  type="checkbox"
                  id="terms"
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded accent-[var(--cy-accent)]"
                />
                <label htmlFor="terms" className="text-[12.5px] text-cy-muted">
                  I agree to the{' '}
                  <a href="/terms" target="_blank" className="font-semibold text-cy-accent">
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a href="/privacy" target="_blank" className="font-semibold text-cy-accent">
                    Privacy Policy
                  </a>
                </label>
              </div>
            )}

            {error && (
              <div className="rounded-[10px] bg-error-50 px-3 py-2.5">
                <p className="text-[12.5px] text-error">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || (isRegistering && !termsAccepted)}
              className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-[10px] bg-cy-accent py-3 text-[13px] font-semibold text-white transition-colors hover:bg-[color-mix(in_srgb,var(--cy-accent)_88%,#000)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cy-accent disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {isRegistering ? 'Creating account…' : 'Signing in…'}
                </>
              ) : (
                <>{isRegistering ? 'Create account' : 'Sign in'}</>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-[12.5px] text-cy-muted">
              {isRegistering ? (
                <>
                  Already have an account?{' '}
                  <button
                    onClick={toggleMode}
                    className="cursor-pointer font-semibold text-cy-accent"
                  >
                    Sign in
                  </button>
                </>
              ) : (
                <>
                  Don&apos;t have an account?{' '}
                  <button
                    onClick={toggleMode}
                    className="cursor-pointer font-semibold text-cy-accent"
                  >
                    Create one
                  </button>
                </>
              )}
            </p>
          </div>
        </div>

        <p className="mt-6 text-center text-[12.5px] text-cy-faint">
          <a
            href="https://climatrix.co"
            className="transition-colors hover:text-cy-muted"
          >
            &larr; climatrix.co
          </a>
        </p>
      </div>
    </div>
  );
}

// Wrap with Suspense for useSearchParams
export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-cy-accent" />
      </div>
    }>
      <LoginPageContent />
    </Suspense>
  );
}
