import localFont from 'next/font/local';

// Canopy's app face (decision #2): self-hosted Nunito Sans — the closest open
// cousin of the mockups' Avenir Next. Variable weight 400–700, latin subset,
// 48KB. Applied via Shell's wrapper class; batch 2.1 moves it to the root
// layout and removes Open Sans. Latin-only: Hebrew strings fall back to the
// system stack (the app UI is English).
export const canopyFont = localFont({
  src: '../../fonts/NunitoSans-latin-var.woff2',
  weight: '400 700',
  style: 'normal',
  display: 'swap',
  variable: '--font-canopy',
});
