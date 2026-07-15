'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Loader2, ArrowLeft, Mail, Check } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to send reset email');
      }

      setIsSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

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
              {isSubmitted ? 'Check Your Email' : 'Reset Password'}
            </h1>
            <p className="text-[12.5px] text-cy-muted mt-1">
              {isSubmitted
                ? 'We sent you a password reset link'
                : 'Enter your email to receive a reset link'}
            </p>
          </div>

          {isSubmitted ? (
            <div className="space-y-6">
              <div className="flex flex-col items-center gap-4 py-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-cy-accent-soft">
                  <Check className="h-6 w-6 text-cy-accent" />
                </div>
                <p className="text-center text-cy-muted">
                  If an account exists for <span className="font-semibold text-foreground">{email}</span>,
                  you will receive a password reset email shortly.
                </p>
              </div>

              <div className="space-y-3">
                <Link
                  href="/?login=true"
                  className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-[10px] bg-cy-accent py-3 text-[13px] font-semibold text-white transition-colors hover:bg-[color-mix(in_srgb,var(--cy-accent)_88%,#000)]"
                >
                  Back to Login
                </Link>
                <button
                  onClick={() => {
                    setIsSubmitted(false);
                    setEmail('');
                  }}
                  className="w-full cursor-pointer rounded-[10px] bg-cy-row py-3 text-[13px] font-semibold text-cy-muted transition-colors hover:text-cy-ink"
                >
                  Try Different Email
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-[11px] font-bold tracking-[0.06em] uppercase text-cy-faint">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-cy-muted" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
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
                    Sending...
                  </>
                ) : (
                  'Send Reset Link'
                )}
              </button>

              <Link
                href="/?login=true"
                className="flex items-center justify-center gap-2 text-cy-muted hover:text-cy-ink transition-colors mt-4"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Login
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
