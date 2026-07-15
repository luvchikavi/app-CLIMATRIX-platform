'use client';

import { useEffect, useState, useCallback, useSyncExternalStore } from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

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
const listeners: Set<Listener> = new Set();
let nextId = 0;

// Stable empty reference for SSR — useSyncExternalStore requires getServerSnapshot
// to return a cached value, otherwise React warns about a possible infinite loop.
const EMPTY_TOASTS: ToastItem[] = [];

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
  return EMPTY_TOASTS;
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

// Canopy toast: a quiet surface with a small status dot — no borders, no icons.
const variantConfig: Record<ToastVariant, { dot: string }> = {
  success: { dot: 'bg-cy-accent' },
  error: { dot: 'bg-error' },
  warning: { dot: 'bg-cy-warn' },
  info: { dot: 'bg-info' },
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
        'flex items-center gap-2.5 w-full max-w-sm px-4 py-2.5',
        'bg-background-elevated rounded-xl shadow-lg',
        'transition-all duration-200 ease-out',
        isExiting
          ? 'opacity-0 translate-x-4'
          : 'opacity-100 translate-x-0'
      )}
      style={{
        animation: isExiting ? undefined : 'toastSlideIn 300ms ease-out',
      }}
    >
      {/* Status dot */}
      <span className={cn('w-[7px] h-[7px] rounded-full shrink-0', config.dot)} aria-hidden="true" />

      {/* Message */}
      <p className="flex-1 text-[12.5px] text-foreground leading-snug">
        {item.message}
      </p>

      {/* Close button */}
      <button
        onClick={handleDismiss}
        className={cn(
          'shrink-0 p-0.5 rounded-md',
          'text-foreground-muted hover:text-foreground',
          'hover:bg-cy-row',
          'transition-colors duration-150',
          'focus-visible:outline-2 focus-visible:outline-cy-accent'
        )}
        aria-label="Dismiss notification"
      >
        <X className="w-3.5 h-3.5" />
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
