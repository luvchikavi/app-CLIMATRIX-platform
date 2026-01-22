/**
 * CLIMATRIX Design System - TypeScript Tokens
 *
 * This file exports design tokens for programmatic use in components.
 * These values mirror the CSS custom properties in globals.css
 */

// =============================================================================
// COLOR PALETTE
// =============================================================================

export const colors = {
  // Primary (Brand Blue)
  primary: {
    50: "#E6F3FF",
    100: "#CCE7FF",
    200: "#99CFFF",
    300: "#66B7FF",
    400: "#339FFF",
    500: "#0073E6", // Main brand color
    600: "#0059B3",
    700: "#004080",
    800: "#002B57",
    900: "#00162E",
  },

  // Secondary (Sustainability Green)
  secondary: {
    50: "#E6F7F0",
    100: "#CCEFE1",
    200: "#99DFC3",
    300: "#66CFA5",
    400: "#33BF87",
    500: "#00A86B", // Main green
    600: "#008555",
    700: "#00623E",
    800: "#003F28",
    900: "#001C12",
  },

  // Accent (Action Orange)
  accent: {
    50: "#FFF3ED",
    100: "#FFE7DB",
    200: "#FFCFB7",
    300: "#FFB793",
    400: "#FF9F6F",
    500: "#FF6B35", // Main orange
    600: "#CC552A",
    700: "#993F20",
    800: "#662A15",
    900: "#33150B",
  },

  // Semantic Colors
  success: {
    50: "#ECFDF5",
    100: "#D1FAE5",
    500: "#10B981",
    600: "#059669",
    700: "#047857",
  },

  warning: {
    50: "#FFFBEB",
    100: "#FEF3C7",
    500: "#F59E0B",
    600: "#D97706",
    700: "#B45309",
  },

  error: {
    50: "#FEF2F2",
    100: "#FEE2E2",
    500: "#EF4444",
    600: "#DC2626",
    700: "#B91C1C",
  },

  info: {
    50: "#EFF6FF",
    100: "#DBEAFE",
    500: "#3B82F6",
    600: "#2563EB",
    700: "#1D4ED8",
  },

  // Neutrals (Gray Scale)
  neutral: {
    0: "#FFFFFF",
    25: "#FCFCFD",
    50: "#F8FAFC",
    100: "#F1F5F9",
    200: "#E2E8F0",
    300: "#CBD5E1",
    400: "#94A3B8",
    500: "#64748B",
    600: "#475569",
    700: "#334155",
    800: "#1E293B",
    900: "#0F172A",
    950: "#020617",
  },

  // GHG Scope Colors
  scope: {
    1: "#EF4444", // Red - Direct emissions
    2: "#F59E0B", // Amber - Energy indirect
    3: "#3B82F6", // Blue - Value chain
  },

  scopeLight: {
    1: "#FEE2E2",
    2: "#FEF3C7",
    3: "#DBEAFE",
  },
} as const;

// =============================================================================
// TYPOGRAPHY
// =============================================================================

export const typography = {
  fontFamily: {
    sans: "'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif",
    mono: "'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', 'Droid Sans Mono', monospace",
  },

  fontSize: {
    xs: "0.75rem", // 12px
    sm: "0.875rem", // 14px
    base: "1rem", // 16px
    lg: "1.125rem", // 18px
    xl: "1.25rem", // 20px
    "2xl": "1.5rem", // 24px
    "3xl": "1.875rem", // 30px
    "4xl": "2.25rem", // 36px
    "5xl": "3rem", // 48px
  },

  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  lineHeight: {
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },

  letterSpacing: {
    tighter: "-0.05em",
    tight: "-0.025em",
    normal: "0",
    wide: "0.025em",
    wider: "0.05em",
  },
} as const;

// =============================================================================
// SPACING (8px base unit)
// =============================================================================

export const spacing = {
  0: "0",
  1: "0.25rem", // 4px
  2: "0.5rem", // 8px
  3: "0.75rem", // 12px
  4: "1rem", // 16px
  5: "1.25rem", // 20px
  6: "1.5rem", // 24px
  8: "2rem", // 32px
  10: "2.5rem", // 40px
  12: "3rem", // 48px
  16: "4rem", // 64px
  20: "5rem", // 80px
  24: "6rem", // 96px
} as const;

// Numeric spacing values (in pixels)
export const spacingPx = {
  0: 0,
  1: 4,
  2: 8,
  3: 12,
  4: 16,
  5: 20,
  6: 24,
  8: 32,
  10: 40,
  12: 48,
  16: 64,
  20: 80,
  24: 96,
} as const;

// =============================================================================
// BORDER RADIUS
// =============================================================================

export const borderRadius = {
  none: "0",
  sm: "0.25rem", // 4px
  md: "0.375rem", // 6px
  lg: "0.5rem", // 8px
  xl: "0.75rem", // 12px
  "2xl": "1rem", // 16px
  "3xl": "1.5rem", // 24px
  full: "9999px",
} as const;

// =============================================================================
// SHADOWS
// =============================================================================

export const shadows = {
  xs: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  sm: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
  md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
  lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
  xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
  "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
  inner: "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",
  card: "0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px 0 rgb(0 0 0 / 0.02)",
  cardHover: "0 4px 12px 0 rgb(0 0 0 / 0.08)",
} as const;

// =============================================================================
// TRANSITIONS
// =============================================================================

export const transitions = {
  fast: "150ms ease",
  base: "200ms ease",
  slow: "300ms ease",
  slower: "500ms ease",
} as const;

// =============================================================================
// Z-INDEX SCALE
// =============================================================================

export const zIndex = {
  behind: -1,
  base: 0,
  raised: 10,
  dropdown: 100,
  sticky: 200,
  overlay: 300,
  modal: 400,
  popover: 500,
  tooltip: 600,
  toast: 700,
} as const;

// =============================================================================
// LAYOUT
// =============================================================================

export const layout = {
  sidebarWidth: "280px",
  sidebarWidthCollapsed: "72px",
  headerHeight: "64px",
  maxContentWidth: "1440px",
} as const;

// =============================================================================
// BREAKPOINTS
// =============================================================================

export const breakpoints = {
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
} as const;

export const breakpointsPx = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
} as const;

// =============================================================================
// CHART COLORS (for Recharts)
// =============================================================================

export const chartColors = {
  // Scope colors for pie/bar charts
  scopes: [colors.scope[1], colors.scope[2], colors.scope[3]],

  // Category breakdown palette (12 colors)
  categories: [
    "#0073E6", // Primary blue
    "#00A86B", // Secondary green
    "#FF6B35", // Accent orange
    "#8B5CF6", // Purple
    "#EC4899", // Pink
    "#14B8A6", // Teal
    "#F59E0B", // Amber
    "#6366F1", // Indigo
    "#84CC16", // Lime
    "#EF4444", // Red
    "#06B6D4", // Cyan
    "#F97316", // Orange
  ],

  // Sequential palette (for heatmaps, gradients)
  sequential: {
    blue: ["#E6F3FF", "#99CFFF", "#339FFF", "#0073E6", "#004080"],
    green: ["#E6F7F0", "#99DFC3", "#33BF87", "#00A86B", "#00623E"],
    red: ["#FEE2E2", "#FECACA", "#F87171", "#EF4444", "#B91C1C"],
  },

  // Diverging palette (for positive/negative comparisons)
  diverging: ["#B91C1C", "#F87171", "#FEE2E2", "#F8FAFC", "#DBEAFE", "#60A5FA", "#2563EB"],
} as const;

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get scope color by scope number
 */
export function getScopeColor(scope: 1 | 2 | 3): string {
  return colors.scope[scope];
}

/**
 * Get scope light background by scope number
 */
export function getScopeLightColor(scope: 1 | 2 | 3): string {
  return colors.scopeLight[scope];
}

/**
 * Get category color by index (wraps around)
 */
export function getCategoryColor(index: number): string {
  return chartColors.categories[index % chartColors.categories.length];
}

/**
 * Format a number with thousands separator
 */
export function formatNumber(value: number, decimals: number = 0): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format CO2e value with appropriate unit (kg, tonnes, ktonnes)
 */
export function formatCO2e(kgValue: number): string {
  if (kgValue >= 1_000_000) {
    return `${formatNumber(kgValue / 1_000_000, 1)} kt CO2e`;
  } else if (kgValue >= 1_000) {
    return `${formatNumber(kgValue / 1_000, 1)} t CO2e`;
  }
  return `${formatNumber(kgValue, 0)} kg CO2e`;
}

/**
 * Get percentage change badge color
 */
export function getTrendColor(change: number): string {
  if (change < 0) return colors.success[500]; // Reduction is good
  if (change > 0) return colors.error[500]; // Increase is bad
  return colors.neutral[500]; // No change
}

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export type ColorScale = keyof typeof colors;
export type FontSize = keyof typeof typography.fontSize;
export type FontWeight = keyof typeof typography.fontWeight;
export type Spacing = keyof typeof spacing;
export type BorderRadius = keyof typeof borderRadius;
export type Shadow = keyof typeof shadows;
export type ZIndex = keyof typeof zIndex;
export type Breakpoint = keyof typeof breakpoints;
export type Scope = 1 | 2 | 3;
