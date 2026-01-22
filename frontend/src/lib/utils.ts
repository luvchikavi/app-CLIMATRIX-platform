/**
 * CLIMATRIX Utility Functions
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines class names using clsx and tailwind-merge
 * This handles Tailwind CSS class conflicts intelligently
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Debounce function for input handlers
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), wait);
  };
}

/**
 * Throttle function for scroll/resize handlers
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Format a date to a readable string
 */
export function formatDate(
  date: Date | string,
  options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  }
): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("en-US", options);
}

/**
 * Format a date to ISO format (YYYY-MM-DD)
 */
export function toISODateString(date: Date): string {
  return date.toISOString().split("T")[0];
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
 * Format a compact number (1K, 1M, etc.)
 */
export function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

/**
 * Format CO2e value with appropriate unit
 */
export function formatCO2e(kgValue: number): string {
  if (Math.abs(kgValue) >= 1_000_000) {
    return `${formatNumber(kgValue / 1_000_000, 1)} kt CO2e`;
  } else if (Math.abs(kgValue) >= 1_000) {
    return `${formatNumber(kgValue / 1_000, 1)} t CO2e`;
  }
  return `${formatNumber(kgValue, 0)} kg CO2e`;
}

/**
 * Format percentage with + sign for positive values
 */
export function formatPercentChange(value: number): string {
  const formatted = formatNumber(Math.abs(value), 1);
  if (value > 0) return `+${formatted}%`;
  if (value < 0) return `-${formatted}%`;
  return `${formatted}%`;
}

/**
 * Truncate a string to a maximum length
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 3) + "...";
}

/**
 * Capitalize first letter
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert string to title case
 */
export function toTitleCase(str: string): string {
  return str
    .toLowerCase()
    .split(" ")
    .map((word) => capitalize(word))
    .join(" ");
}

/**
 * Convert camelCase or snake_case to Title Case
 */
export function toReadable(str: string): string {
  return str
    .replace(/([A-Z])/g, " $1")
    .replace(/_/g, " ")
    .trim()
    .split(" ")
    .map((word) => capitalize(word.toLowerCase()))
    .join(" ");
}

/**
 * Generate a random ID
 */
export function generateId(prefix: string = ""): string {
  const random = Math.random().toString(36).substring(2, 9);
  return prefix ? `${prefix}_${random}` : random;
}

/**
 * Deep clone an object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Check if a value is empty (null, undefined, empty string, empty array, empty object)
 */
export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === "string") return value.trim() === "";
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === "object") return Object.keys(value).length === 0;
  return false;
}

/**
 * Sleep for a given number of milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Pluralize a word based on count
 */
export function pluralize(count: number, singular: string, plural?: string): string {
  return count === 1 ? singular : plural || `${singular}s`;
}

/**
 * Get scope label from scope number
 */
export function getScopeLabel(scope: 1 | 2 | 3): string {
  const labels = {
    1: "Scope 1 - Direct Emissions",
    2: "Scope 2 - Indirect Energy",
    3: "Scope 3 - Value Chain",
  };
  return labels[scope];
}

/**
 * Get short scope label
 */
export function getScopeShortLabel(scope: 1 | 2 | 3): string {
  const labels = {
    1: "Scope 1",
    2: "Scope 2",
    3: "Scope 3",
  };
  return labels[scope];
}

/**
 * Get category name from code
 */
export const categoryNames: Record<string, string> = {
  "1.1": "Stationary Combustion",
  "1.2": "Mobile Combustion",
  "1.3": "Fugitive Emissions",
  "2": "Purchased Energy",
  "2.1": "Purchased Electricity",
  "2.2": "Purchased Heat/Steam/Cooling",
  "3.1": "Purchased Goods & Services",
  "3.2": "Capital Goods",
  "3.3": "Fuel & Energy Related",
  "3.4": "Upstream Transportation",
  "3.5": "Waste Generated",
  "3.6": "Business Travel",
  "3.7": "Employee Commuting",
  "3.8": "Upstream Leased Assets",
  "3.9": "Downstream Transportation",
  "3.10": "Processing of Sold Products",
  "3.11": "Use of Sold Products",
  "3.12": "End-of-Life Treatment",
  "3.13": "Downstream Leased Assets",
  "3.14": "Franchises",
  "3.15": "Investments",
};

/**
 * Get category name
 */
export function getCategoryName(code: string): string {
  return categoryNames[code] || code;
}

/**
 * Calculate percentage of total
 */
export function calculatePercentage(value: number, total: number): number {
  if (total === 0) return 0;
  return (value / total) * 100;
}

/**
 * Safe division (returns 0 if divisor is 0)
 */
export function safeDivide(numerator: number, denominator: number): number {
  if (denominator === 0) return 0;
  return numerator / denominator;
}

/**
 * Clamp a number between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Get ordinal suffix for a number (1st, 2nd, 3rd, etc.)
 */
export function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

/**
 * Download data as a file
 */
export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
