'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react';

export default function BillingError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Billing error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="mx-auto w-16 h-16 rounded-full bg-error/10 flex items-center justify-center mb-6">
          <AlertTriangle className="w-8 h-8 text-error" />
        </div>
        <h2 className="text-xl font-semibold text-foreground mb-2">
          Failed to load billing
        </h2>
        <p className="text-foreground-muted mb-6">
          There was a problem loading billing information. Please try again.
        </p>
        <div className="flex items-center justify-center gap-3">
          <a
            href="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-border text-foreground hover:bg-background-muted transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Dashboard
          </a>
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-primary text-white hover:bg-primary-hover transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      </div>
    </div>
  );
}
