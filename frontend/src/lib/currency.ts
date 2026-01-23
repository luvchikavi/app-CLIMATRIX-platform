/**
 * Currency conversion utilities for spend-based calculations
 *
 * All EEIO emission factors are in kg CO2e per USD.
 * When user enters non-USD amounts, we must convert to USD before applying factors.
 */

// Currency conversion rates to USD (2024 annual averages)
// Source: ECB, OECD, Bank of Israel
export const CURRENCY_RATES_TO_USD: Record<string, number> = {
  USD: 1.00,
  EUR: 1.08,
  GBP: 1.27,
  ILS: 0.27,
  CAD: 0.74,
  AUD: 0.66,
  JPY: 0.0067,
  CNY: 0.14,
  INR: 0.012,
  CHF: 1.13,
  SEK: 0.095,
  NOK: 0.092,
  DKK: 0.145,
};

// Standard currency options for forms
export const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
  { code: 'CHF', symbol: 'Fr', name: 'Swiss Franc' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar' },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar' },
] as const;

/**
 * Convert an amount from any currency to USD
 */
export function convertToUSD(amount: number, currency: string): number {
  const rate = CURRENCY_RATES_TO_USD[currency.toUpperCase()] || 1;
  return amount * rate;
}

/**
 * Get the conversion rate for a currency to USD
 */
export function getUSDRate(currency: string): number {
  return CURRENCY_RATES_TO_USD[currency.toUpperCase()] || 1;
}

/**
 * Calculate spend-based emissions with proper currency conversion
 *
 * @param amount - The spend amount in the given currency
 * @param currency - The currency code (USD, EUR, ILS, etc.)
 * @param efPerUSD - The emission factor in kg CO2e per USD
 * @returns Object with converted amount, CO2e, and formula
 */
export function calculateSpendEmissions(
  amount: number,
  currency: string,
  efPerUSD: number
): { amountUSD: number; co2e: number; formula: string } {
  const rate = getUSDRate(currency);
  const amountUSD = amount * rate;
  const co2e = amountUSD * efPerUSD;

  let formula: string;
  if (currency === 'USD') {
    formula = `${amount.toLocaleString()} USD × ${efPerUSD.toFixed(2)} kg CO2e/USD = ${co2e.toFixed(2)} kg CO2e`;
  } else {
    formula = `${amount.toLocaleString()} ${currency} → ${amountUSD.toLocaleString(undefined, { maximumFractionDigits: 0 })} USD × ${efPerUSD.toFixed(2)} kg CO2e/USD = ${co2e.toFixed(2)} kg CO2e`;
  }

  return { amountUSD, co2e, formula };
}
