'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, Lock, Check, AlertCircle } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (!token) {
      setError('Invalid or missing reset token');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to reset password');
      }

      setIsSuccess(true);
      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push('/?login=true');
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

  // No token provided
  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4 text-foreground">
        <div className="relative w-full max-w-md">
          <div className="rounded-cy bg-background-elevated px-8 py-7 shadow-card">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-red-400" />
              </div>
              <h1 className="text-[17px] font-bold tracking-[-0.01em] text-foreground mb-2">Invalid Link</h1>
              <p className="text-cy-muted mb-6">
                This password reset link is invalid or has expired.
              </p>
              <Link
                href="/forgot-password"
                className="inline-flex w-full cursor-pointer items-center justify-center rounded-[10px] bg-cy-accent py-3 text-[13px] font-semibold text-white transition-colors hover:bg-[color-mix(in_srgb,var(--cy-accent)_88%,#000)]"
              >
                Request New Link
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4 text-foreground">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-cyan-500/10 via-transparent to-transparent rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative w-full max-w-md">
        <div className="rounded-cy bg-background-elevated px-8 py-7 shadow-card">
          {/* Logo */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-block">
              <p className="text-[15px] font-extrabold tracking-[0.01em] text-cy-ink">climatri<span className="text-cy-accent">x</span></p>
            </Link>
            <h1 className="text-[17px] font-bold tracking-[-0.01em] text-foreground">
              {isSuccess ? 'Password Reset!' : 'Create New Password'}
            </h1>
            <p className="text-[12.5px] text-cy-muted mt-1">
              {isSuccess
                ? 'You can now sign in with your new password'
                : 'Enter your new password below'}
            </p>
          </div>

          {isSuccess ? (
            <div className="space-y-6">
              <div className="flex flex-col items-center gap-4 py-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-cy-accent-soft">
                  <Check className="h-6 w-6 text-cy-accent" />
                </div>
                <p className="text-center text-cy-muted">
                  Your password has been reset successfully. Redirecting to login...
                </p>
              </div>

              <Link
                href="/?login=true"
                className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-[10px] bg-cy-accent py-3 text-[13px] font-semibold text-white transition-colors hover:bg-[color-mix(in_srgb,var(--cy-accent)_88%,#000)]"
              >
                Go to Login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-[11px] font-bold tracking-[0.06em] uppercase text-cy-faint">
                  New Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-cy-muted" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter new password"
                    required
                    minLength={6}
                    className="w-full rounded-[10px] border-0 bg-cy-row py-2.5 pl-11 pr-4 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                  />
                </div>
                <p className="text-xs text-cy-faint mt-1">Minimum 6 characters</p>
              </div>

              <div>
                <label className="mb-1.5 block text-[11px] font-bold tracking-[0.06em] uppercase text-cy-faint">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-cy-muted" />
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    required
                    className="w-full rounded-[10px] border-0 bg-cy-row py-2.5 pl-11 pr-4 text-[13px] font-semibold text-foreground placeholder:font-normal placeholder:text-cy-faint focus:outline-none focus:ring-2 focus:ring-cy-accent"
                  />
                </div>
              </div>

              {error && (
                <div className="rounded-[10px] bg-error-50 px-3 py-2.5">
                  <p className="text-[12.5px] text-error">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-[10px] bg-cy-accent py-3 text-[13px] font-semibold text-white transition-colors hover:bg-[color-mix(in_srgb,var(--cy-accent)_88%,#000)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Resetting...
                  </>
                ) : (
                  'Reset Password'
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-background">
          <div className="flex flex-col items-center gap-4">
            
            <Loader2 className="w-6 h-6 text-cy-accent animate-spin" />
          </div>
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
