/**
 * Auth Store - Zustand store for authentication state
 *
 * Persists to localStorage as 'auth-storage'.
 * Token is also synced to ApiClient via onRehydrateStorage.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api, User, Organization, RegisterRequest } from '@/lib/api';

interface AuthState {
  user: User | null;
  organization: Organization | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isHydrated: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  setAuth: (token: string, user: User, organization: Organization | null) => void;
  logout: () => void;
  setUser: (user: User | null) => void;
  setOrganization: (org: Organization | null) => void;
  clearError: () => void;
  setHydrated: (hydrated: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      organization: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      isHydrated: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.login({ email, password });
          set({
            user: response.user,
            organization: response.organization || null,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Login failed',
            isLoading: false,
          });
          throw error;
        }
      },

      register: async (data: RegisterRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.register(data);
          set({
            user: response.user,
            organization: response.organization,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Registration failed',
            isLoading: false,
          });
          throw error;
        }
      },

      setAuth: (token: string, user: User, organization: Organization | null) => {
        api.setToken(token);
        set({
          user,
          organization,
          token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      },

      logout: () => {
        api.logout();
        set({
          user: null,
          organization: null,
          token: null,
          isAuthenticated: false,
        });
      },

      setUser: (user: User | null) => {
        set({ user, isAuthenticated: !!user });
      },

      setOrganization: (organization: Organization | null) => {
        set({ organization });
      },

      clearError: () => {
        set({ error: null });
      },

      setHydrated: (hydrated: boolean) => {
        set({ isHydrated: hydrated });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        organization: state.organization,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        // Called after rehydration is complete
        if (state) {
          state.setHydrated(true);
          // Sync token to ApiClient
          if (state.token) {
            api.setToken(state.token);
            // Validate token asynchronously
            api.validateToken().then((isValid) => {
              if (!isValid) {
                // Token is invalid/expired, logout
                state.logout();
              }
            });
          }

          // Listen for auth expiration events from API
          if (typeof window !== 'undefined') {
            window.addEventListener('auth-expired', () => {
              state.logout();
            });
          }
        }
      },
    }
  )
);
