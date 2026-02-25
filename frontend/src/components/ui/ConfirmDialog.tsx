'use client';

import { useEffect, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { AlertTriangle, HelpCircle, X, Loader2 } from 'lucide-react';

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'default';
  isLoading?: boolean;
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  isLoading = false,
}: ConfirmDialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

  // Focus the cancel button when the dialog opens
  useEffect(() => {
    if (isOpen) {
      // Small delay to allow the animation to start
      const timer = setTimeout(() => {
        cancelButtonRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && !isLoading) {
        onClose();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, onClose]);

  // Prevent body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [isOpen]);

  // Close when clicking the backdrop
  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === overlayRef.current && !isLoading) {
        onClose();
      }
    },
    [isLoading, onClose]
  );

  if (!isOpen) return null;

  const variantConfig = {
    danger: {
      icon: <AlertTriangle className="w-6 h-6" />,
      iconBg: 'bg-[var(--color-error-50)]',
      iconColor: 'text-error',
      confirmButton: cn(
        'bg-error text-white',
        'hover:bg-[var(--color-error-600)]',
        'active:bg-[var(--color-error-700)]',
        'focus-visible:ring-error'
      ),
    },
    warning: {
      icon: <AlertTriangle className="w-6 h-6" />,
      iconBg: 'bg-[var(--color-warning-50)]',
      iconColor: 'text-warning',
      confirmButton: cn(
        'bg-primary text-white',
        'hover:bg-primary-hover',
        'active:bg-[var(--color-primary-700)]',
        'focus-visible:ring-primary'
      ),
    },
    default: {
      icon: <HelpCircle className="w-6 h-6" />,
      iconBg: 'bg-[var(--color-primary-50)]',
      iconColor: 'text-primary',
      confirmButton: cn(
        'bg-primary text-white',
        'hover:bg-primary-hover',
        'active:bg-[var(--color-primary-700)]',
        'focus-visible:ring-primary'
      ),
    },
  };

  const config = variantConfig[variant];

  return (
    <div
      ref={overlayRef}
      onClick={handleBackdropClick}
      className={cn(
        'fixed inset-0 flex items-center justify-center p-4',
        'bg-black/50 backdrop-blur-sm',
        'animate-fade-in'
      )}
      style={{ zIndex: 'var(--z-modal)' }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
    >
      <div
        className={cn(
          'relative w-full max-w-md',
          'bg-background-elevated border border-border rounded-xl shadow-xl',
          'transform transition-all duration-200 ease-out',
          'animate-[fadeInScale_200ms_ease-out]'
        )}
        style={{
          animation: 'fadeInScale 200ms ease-out',
        }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          disabled={isLoading}
          className={cn(
            'absolute top-3 right-3 p-1 rounded-lg',
            'text-foreground-muted hover:text-foreground',
            'hover:bg-background-muted',
            'transition-colors duration-150',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
          aria-label="Close dialog"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Content */}
        <div className="p-6">
          {/* Icon */}
          <div className="flex justify-center mb-4">
            <div
              className={cn(
                'flex items-center justify-center w-12 h-12 rounded-full',
                config.iconBg,
                config.iconColor
              )}
            >
              {config.icon}
            </div>
          </div>

          {/* Title */}
          <h2
            id="confirm-dialog-title"
            className="text-lg font-semibold text-foreground text-center"
          >
            {title}
          </h2>

          {/* Message */}
          <p
            id="confirm-dialog-message"
            className="mt-2 text-sm text-foreground-muted text-center leading-relaxed"
          >
            {message}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 px-6 pb-6">
          <button
            ref={cancelButtonRef}
            onClick={onClose}
            disabled={isLoading}
            className={cn(
              'flex-1 px-4 py-2 text-sm font-medium rounded-lg',
              'text-foreground bg-transparent border border-border',
              'hover:bg-background-muted',
              'active:bg-[var(--color-neutral-200)]',
              'transition-all duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={cn(
              'flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-lg',
              'transition-all duration-150',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              config.confirmButton
            )}
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            {confirmLabel}
          </button>
        </div>
      </div>

      {/* Inline keyframes for the scale animation */}
      <style>{`
        @keyframes fadeInScale {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
}

ConfirmDialog.displayName = 'ConfirmDialog';
