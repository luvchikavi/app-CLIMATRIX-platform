import type { Metadata, Viewport } from "next";
import { Open_Sans } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

// Open Sans - Apple-like typography
const openSans = Open_Sans({
  subsets: ["latin", "hebrew"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-open-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "CLIMATRIX - GHG Emissions Platform",
  description: "Professional carbon accounting and GHG emissions management platform for organizations",
  keywords: ["GHG", "carbon accounting", "emissions", "sustainability", "climate", "ESG"],
  authors: [{ name: "CLIMATRIX" }],
  creator: "CLIMATRIX",
  publisher: "CLIMATRIX",
  applicationName: "CLIMATRIX",
  metadataBase: new URL("https://climatrix.io"),
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://climatrix.io",
    title: "CLIMATRIX - GHG Emissions Platform",
    description: "Professional carbon accounting and GHG emissions management platform",
    siteName: "CLIMATRIX",
  },
  twitter: {
    card: "summary_large_image",
    title: "CLIMATRIX - GHG Emissions Platform",
    description: "Professional carbon accounting and GHG emissions management platform",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F8FAFC" },
    { media: "(prefers-color-scheme: dark)", color: "#020617" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Preconnect to Google Fonts for performance */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={`${openSans.variable} font-sans antialiased`}>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2 focus:bg-primary focus:text-white focus:rounded-lg focus:text-sm focus:font-medium focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          Skip to main content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
