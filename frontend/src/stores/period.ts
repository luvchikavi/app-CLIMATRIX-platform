'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface PeriodState {
  selectedPeriodId: string | null;
  setSelectedPeriodId: (id: string | null) => void;
}

export const usePeriodStore = create<PeriodState>()(
  persist(
    (set) => ({
      selectedPeriodId: null,
      setSelectedPeriodId: (id) => set({ selectedPeriodId: id }),
    }),
    {
      name: 'climatrix-period',
    }
  )
);
