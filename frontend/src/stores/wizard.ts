/**
 * Wizard Store - Zustand store for data entry wizard state
 *
 * Multi-step wizard for adding activities:
 * 1. Select Scope (1, 2, 3)
 * 2. Select Category (1.1, 2, 3.1, etc.)
 * 3. Select Activity Type (activity_key from dropdown)
 * 4. Enter Details (quantity, unit, date, description)
 * 5. Review & Confirm
 */
import { create } from 'zustand';
import { ActivityCreate, EmissionFactor } from '@/lib/api';

type WizardStep = 'scope' | 'category' | 'activity' | 'details' | 'review';

interface WizardEntry {
  scope: 1 | 2 | 3;
  category_code: string;
  activity_key: string;
  description: string;
  quantity: number;
  unit: string;
  activity_date?: string; // Optional - defaults to today for annual reporting
  // For preview calculations
  co2e_factor?: number;
  factor_source?: string;
  display_name?: string;
}

interface WizardState {
  // Current step
  step: WizardStep;

  // Selected values
  selectedScope: 1 | 2 | 3 | null;
  selectedCategory: string | null;
  selectedActivityKey: string | null;
  selectedFactor: EmissionFactor | null;

  // Entry data
  entry: Partial<WizardEntry>;

  // Entries to submit (for bulk entry)
  entries: WizardEntry[];

  // Actions
  setStep: (step: WizardStep) => void;
  setScope: (scope: 1 | 2 | 3) => void;
  setCategory: (code: string) => void;
  setActivityKey: (key: string, factor: EmissionFactor) => void;
  setEntryField: <K extends keyof WizardEntry>(field: K, value: WizardEntry[K]) => void;
  addEntry: () => boolean; // Returns true if entry was added
  removeEntry: (index: number) => void;
  clearEntries: () => void;
  reset: () => void;
  goBack: () => void;

  // Computed
  getTotalCO2e: () => number;
}

// Category definitions for each scope
export const CATEGORIES = {
  1: [
    { code: '1.1', name: 'Stationary Combustion', description: 'Boilers, furnaces, generators' },
    { code: '1.2', name: 'Mobile Combustion', description: 'Company vehicles' },
    { code: '1.3', name: 'Fugitive Emissions', description: 'Refrigerants, fire suppression' },
    { code: '1.4', name: 'Process Emissions', description: 'Industrial processes (cement, lime, chemicals)' },
  ],
  2: [
    { code: '2.1', name: 'Purchased Electricity (Location-based)', description: 'Grid average emission factors' },
    { code: '2.2', name: 'Purchased Electricity (Market-based)', description: 'Supplier-specific, RECs, PPAs' },
    { code: '2.3', name: 'Purchased Heat/Steam/Cooling', description: 'District heating, steam, cooling' },
  ],
  3: [
    { code: '3.1', name: 'Purchased Goods & Services', description: 'Physical, Spend, or Supplier-Specific' },
    { code: '3.2', name: 'Capital Goods', description: 'Equipment purchases' },
    { code: '3.3', name: 'Fuel & Energy Related', description: 'Auto-calculated from Scope 1/2' },
    { code: '3.4', name: 'Upstream Transportation', description: 'Freight' },
    { code: '3.5', name: 'Waste', description: 'Waste disposal' },
    { code: '3.6', name: 'Business Travel', description: 'Flights, hotels' },
    { code: '3.7', name: 'Employee Commuting', description: 'Commute to work' },
    { code: '3.8', name: 'Upstream Leased Assets', description: 'Leased buildings, vehicles, equipment' },
    { code: '3.9', name: 'Downstream Transportation', description: 'Delivery to customers' },
    { code: '3.10', name: 'Processing of Sold Products', description: 'Processing by third parties' },
    { code: '3.11', name: 'Use of Sold Products', description: 'End-use of sold products' },
    { code: '3.12', name: 'End-of-Life Treatment', description: 'Disposal of sold products' },
    { code: '3.13', name: 'Downstream Leased Assets', description: 'Assets leased to others' },
    { code: '3.14', name: 'Franchises', description: 'Franchise operations' },
  ],
};

// Categories with specialized forms (skip activity selector step)
export const SPECIALIZED_CATEGORIES = ['3.1', '3.2'];

const initialState = {
  step: 'scope' as WizardStep,
  selectedScope: null,
  selectedCategory: null,
  selectedActivityKey: null,
  selectedFactor: null,
  entry: {},
  entries: [],
};

export const useWizardStore = create<WizardState>()((set, get) => ({
  ...initialState,

  setStep: (step) => set({ step }),

  setScope: (scope) =>
    set({
      selectedScope: scope,
      selectedCategory: null,
      selectedActivityKey: null,
      selectedFactor: null,
      entry: {},
      step: 'category',
    }),

  setCategory: (code) =>
    set({
      selectedCategory: code,
      selectedActivityKey: null,
      selectedFactor: null,
      entry: {
        scope: get().selectedScope!,
        category_code: code,
      },
      // Skip activity step for specialized categories (3.1, 3.2)
      // These have their own forms with method selection
      step: SPECIALIZED_CATEGORIES.includes(code) ? 'details' : 'activity',
    }),

  setActivityKey: (key, factor) =>
    set({
      selectedActivityKey: key,
      selectedFactor: factor,
      entry: {
        ...get().entry,
        activity_key: key,
        unit: factor.activity_unit,
        scope: get().selectedScope!,
        category_code: get().selectedCategory!,
      },
      step: 'details',
    }),

  setEntryField: (field, value) =>
    set((state) => ({
      entry: { ...state.entry, [field]: value },
    })),

  addEntry: () => {
    const state = get();
    const entry = state.entry as WizardEntry;
    const factor = state.selectedFactor;

    // FIX-1: Date is optional - defaults to today for annual reporting
    if (
      entry.scope &&
      entry.category_code &&
      entry.activity_key &&
      entry.description &&
      entry.quantity &&
      entry.unit
    ) {
      set({
        entries: [...state.entries, {
          ...entry,
          activity_date: entry.activity_date || new Date().toISOString().split('T')[0],
          // Include factor info for preview calculations
          co2e_factor: factor?.co2e_factor,
          factor_source: factor?.source,
          display_name: factor?.display_name,
        }],
        // Reset form but NOT entries
        step: 'scope',
        selectedScope: null,
        selectedCategory: null,
        selectedActivityKey: null,
        selectedFactor: null,
        entry: {},
      });
      return true;
    }
    return false;
  },

  removeEntry: (index) =>
    set((state) => ({
      entries: state.entries.filter((_, i) => i !== index),
    })),

  clearEntries: () => set({ entries: [] }),

  reset: () => set(initialState),

  getTotalCO2e: () => {
    const state = get();
    return state.entries.reduce((total, entry) => {
      const co2e = (entry.quantity || 0) * (entry.co2e_factor || 0);
      return total + co2e;
    }, 0);
  },

  goBack: () => {
    const state = get();
    switch (state.step) {
      case 'category':
        set({ step: 'scope', selectedScope: null });
        break;
      case 'activity':
        set({ step: 'category', selectedCategory: null });
        break;
      case 'details':
        // For specialized categories, go back to category (skip activity)
        if (SPECIALIZED_CATEGORIES.includes(state.selectedCategory || '')) {
          set({ step: 'category', selectedCategory: null });
        } else {
          set({ step: 'activity', selectedActivityKey: null, selectedFactor: null });
        }
        break;
      case 'review':
        set({ step: 'details' });
        break;
    }
  },
}));
