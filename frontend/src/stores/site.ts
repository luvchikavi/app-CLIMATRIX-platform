'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SiteState {
  selectedSiteId: string | null;
  setSelectedSiteId: (id: string | null) => void;
}

export const useSiteStore = create<SiteState>()(
  persist(
    (set) => ({
      selectedSiteId: null,
      setSelectedSiteId: (id) => set({ selectedSiteId: id }),
    }),
    {
      name: 'climatrix-site',
    }
  )
);
