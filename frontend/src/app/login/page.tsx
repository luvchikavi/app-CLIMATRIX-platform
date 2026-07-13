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
import { Leaf, Loader2, ChevronRight } from 'lucide-react';

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
      theme: 'filled_black',
      size: 'large',
      text: 'continue_with',
      shape: 'pill',
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
    <div className="min-h-screen bg-[#0a0f1a] text-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-[#0f1629] rounded-3xl shadow-2xl p-8 border border-white/10">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-500/25">
              <Leaf className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">
              {isRegistering ? 'Create Account' : 'Welcome Back'}
            </h1>
            <p className="text-gray-500 mt-1">
              {isRegistering ? 'Start your carbon journey' : 'Sign in to your CLIMATRIX account'}
            </p>
          </div>

          {/* Google Sign-In Button */}
          <div id="google-btn-container" className="flex justify-center mb-4 min-h-[44px]" />

          {/* Divider */}
          <div className="relative flex items-center gap-4 mb-4">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-xs text-gray-500 uppercase tracking-wider">or continue with email</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegistering && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="John Smith"
                    required
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Organization Name
                  </label>
                  <input
                    type="text"
                    value={organizationName}
                    onChange={(e) => setOrganizationName(e.target.value)}
                    placeholder="Acme Corporation"
                    required
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Country (Optional)
                  </label>
                  <select
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
                  >
                    <option value="" className="bg-[#0f1629]">Select country...</option>
                    {COUNTRIES.map((c) => (
                      <option key={c.code} value={c.code} className="bg-[#0f1629]">{c.name}</option>
                    ))}
                  </select>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={isRegistering ? 'Create a password' : 'Enter your password'}
                required
                minLength={isRegistering ? 6 : undefined}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
              />
              {isRegistering ? (
                <p className="text-xs text-gray-600 mt-1">Minimum 6 characters</p>
              ) : (
                <div className="flex justify-end mt-2">
                  <a
                    href="/forgot-password"
                    className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    Forgot password?
                  </a>
                </div>
              )}
            </div>

            {isRegistering && (
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="terms"
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className="mt-1 w-4 h-4 rounded border-white/20 bg-white/5 text-emerald-500 focus:ring-emerald-500/50"
                />
                <label htmlFor="terms" className="text-sm text-gray-400">
                  I agree to the{' '}
                  <a href="/terms" target="_blank" className="text-emerald-400 hover:underline">
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a href="/privacy" target="_blank" className="text-emerald-400 hover:underline">
                    Privacy Policy
                  </a>
                </label>
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || (isRegistering && !termsAccepted)}
              className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-emerald-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all hover:-translate-y-0.5"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {isRegistering ? 'Creating account...' : 'Signing in...'}
                </>
              ) : (
                <>
                  {isRegistering ? 'Create Account' : 'Sign In'}
                  <ChevronRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              {isRegistering ? (
                <>
                  Already have an account?{' '}
                  <button
                    onClick={toggleMode}
                    className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                  >
                    Sign in
                  </button>
                </>
              ) : (
                <>
                  Don&apos;t have an account?{' '}
                  <button
                    onClick={toggleMode}
                    className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                  >
                    Create one
                  </button>
                </>
              )}
            </p>
          </div>
        </div>

        <p className="mt-6 text-center text-sm text-gray-600">
          <a
            href="https://climatrix.co"
            className="hover:text-gray-400 transition-colors"
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
      <div className="min-h-screen bg-[#0a0f1a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center animate-pulse">
            <Leaf className="w-7 h-7 text-white" />
          </div>
          <Loader2 className="w-6 h-6 text-emerald-500 animate-spin" />
        </div>
      </div>
    }>
      <LoginPageContent />
    </Suspense>
  );
}
