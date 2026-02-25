'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState, useEffect, ReactNode } from 'react';
import { useAuthStore } from '@/stores/auth';
import { api } from '@/lib/api';
import { ToastContainer } from '@/components/ui/Toast';

/**
 * Token sync component - ensures ApiClient has the token on mount
 * This bridges the gap between Zustand persistence (auth-storage) and
 * ApiClient's localStorage (auth_token)
 */
function TokenSync() {
  const { token, isHydrated } = useAuthStore();

  useEffect(() => {
    // Sync Zustand token to ApiClient when hydrated and when token changes
    if (isHydrated && token) {
      api.setToken(token);
    }
  }, [token, isHydrated]);

  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Default stale time of 1 minute
            staleTime: 60 * 1000,
            // Retry failed requests once
            retry: 1,
            // Don't refetch on window focus by default
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <TokenSync />
      {children}
      <ToastContainer />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
