'use client';

import { useEffect, useState, useCallback, useSyncExternalStore } from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

type ToastVariant = 'success' | 'error' | 'warning' | 'info';

interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
  createdAt: number;
}

// =============================================================================
// External Store (useSyncExternalStore pattern)
// =============================================================================

type Listener = () => void;

let toasts: ToastItem[] = [];
let listeners: Set<Listener> = new Set();
let nextId = 0;

function emitChange() {
  for (const listener of listeners) {
    listener();
  }
}

function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function getSnapshot(): ToastItem[] {
  return toasts;
}

function getServerSnapshot(): ToastItem[] {
  return [];
}

function addToast(message: string, variant: ToastVariant): void {
  const id = `toast-${++nextId}-${Date.now()}`;
  const item: ToastItem = {
    id,
    message,
    variant,
    createdAt: Date.now(),
  };
  toasts = [...toasts, item];
  emitChange();
}

function removeToast(id: string): void {
  toasts = toasts.filter((t) => t.id !== id);
  emitChange();
}

// =============================================================================
// Public API: toast object
// =============================================================================

export const toast = {
  success(message: string) {
    addToast(message, 'success');
  },
  error(message: string) {
    addToast(message, 'error');
  },
  warning(message: string) {
    addToast(message, 'warning');
  },
  info(message: string) {
    addToast(message, 'info');
  },
};

// =============================================================================
// Variant configuration
// =============================================================================

const variantConfig: Record<
  ToastVariant,
  {
    icon: React.ReactNode;
    borderColor: string;
    iconColor: string;
    bgAccent: string;
  }
> = {
  success: {
    icon: <CheckCircle2 className="w-5 h-5 shrink-0" />,
    borderColor: 'border-l-[var(--color-success-500)]',
    iconColor: 'text-success',
    bgAccent: 'bg-[var(--color-success-50)]',
  },
  error: {
    icon: <XCircle className="w-5 h-5 shrink-0" />,
    borderColor: 'border-l-[var(--color-error-500)]',
    iconColor: 'text-error',
    bgAccent: 'bg-[var(--color-error-50)]',
  },
  warning: {
    icon: <AlertTriangle className="w-5 h-5 shrink-0" />,
    borderColor: 'border-l-[var(--color-warning-500)]',
    iconColor: 'text-warning',
    bgAccent: 'bg-[var(--color-warning-50)]',
  },
  info: {
    icon: <Info className="w-5 h-5 shrink-0" />,
    borderColor: 'border-l-[var(--color-info-500)]',
    iconColor: 'text-info',
    bgAccent: 'bg-[var(--color-info-50)]',
  },
};

// =============================================================================
// Individual Toast Component
// =============================================================================

const AUTO_DISMISS_MS = 4000;

function ToastItem({ item, onDismiss }: { item: ToastItem; onDismiss: (id: string) => void }) {
  const [isExiting, setIsExiting] = useState(false);

  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    // Wait for exit animation before removing from store
    setTimeout(() => {
      onDismiss(item.id);
    }, 200);
  }, [item.id, onDismiss]);

  // Auto-dismiss timer
  useEffect(() => {
    const timer = setTimeout(() => {
      handleDismiss();
    }, AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [handleDismiss]);

  const config = variantConfig[item.variant];

  return (
    <div
      role="alert"
      aria-live="polite"
      className={cn(
        'flex items-start gap-3 w-full max-w-sm p-4',
        'bg-background-elevated border border-border border-l-4 rounded-lg shadow-lg',
        config.borderColor,
        'transition-all duration-200 ease-out',
        isExiting
          ? 'opacity-0 translate-x-4'
          : 'opacity-100 translate-x-0'
      )}
      style={{
        animation: isExiting ? undefined : 'toastSlideIn 300ms ease-out',
      }}
    >
      {/* Icon */}
      <div className={config.iconColor}>{config.icon}</div>

      {/* Message */}
      <p className="flex-1 text-sm text-foreground leading-snug pt-px">
        {item.message}
      </p>

      {/* Close button */}
      <button
        onClick={handleDismiss}
        className={cn(
          'shrink-0 p-0.5 rounded',
          'text-foreground-muted hover:text-foreground',
          'hover:bg-background-muted',
          'transition-colors duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
        )}
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

// =============================================================================
// Toast Container
// =============================================================================

export function ToastContainer() {
  const currentToasts = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const handleDismiss = useCallback((id: string) => {
    removeToast(id);
  }, []);

  if (currentToasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 flex flex-col-reverse gap-2 pointer-events-none"
      style={{ zIndex: 'var(--z-toast)' }}
      aria-label="Notifications"
    >
      {currentToasts.map((item) => (
        <div key={item.id} className="pointer-events-auto">
          <ToastItem item={item} onDismiss={handleDismiss} />
        </div>
      ))}

      {/* Inline keyframes for toast slide-in animation */}
      <style>{`
        @keyframes toastSlideIn {
          from {
            opacity: 0;
            transform: translateY(16px) scale(0.96);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>
    </div>
  );
}

ToastContainer.displayName = 'ToastContainer';
