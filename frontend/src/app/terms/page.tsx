'use client';

import Link from 'next/link';
import { Leaf, ArrowLeft } from 'lucide-react';

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Leaf className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-foreground">CLIMATRIX</span>
          </Link>
          <Link
            href="/"
            className="flex items-center gap-2 text-foreground-muted hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold text-foreground mb-2">Terms of Service</h1>
        <p className="text-foreground-muted mb-8">Last updated: January 2025</p>

        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">1. Acceptance of Terms</h2>
            <p className="text-foreground-muted mb-4">
              By accessing or using CLIMATRIX ("the Service"), you agree to be bound by these Terms of Service
              ("Terms"). If you disagree with any part of the terms, you may not access the Service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">2. Description of Service</h2>
            <p className="text-foreground-muted mb-4">
              CLIMATRIX is a carbon accounting platform that helps organizations track, calculate, and report
              their greenhouse gas (GHG) emissions in accordance with international standards such as the
              GHG Protocol, ISO 14064, and various regulatory frameworks.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">3. User Accounts</h2>
            <p className="text-foreground-muted mb-4">
              When you create an account with us, you must provide accurate, complete, and current information.
              You are responsible for safeguarding your password and for all activities that occur under your account.
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li>You must be at least 18 years old to use the Service</li>
              <li>You must provide a valid email address</li>
              <li>You are responsible for maintaining the security of your account</li>
              <li>You must notify us immediately of any unauthorized access</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">4. Acceptable Use</h2>
            <p className="text-foreground-muted mb-4">
              You agree not to use the Service for any unlawful purpose or in any way that could damage,
              disable, or impair the Service. Prohibited activities include:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li>Uploading false or misleading emissions data</li>
              <li>Attempting to gain unauthorized access to other accounts</li>
              <li>Interfering with the proper functioning of the Service</li>
              <li>Using the Service to violate any applicable laws or regulations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">5. Data and Privacy</h2>
            <p className="text-foreground-muted mb-4">
              Your use of the Service is also governed by our <Link href="/privacy" className="text-primary hover:underline">Privacy Policy</Link>.
              You retain ownership of the data you upload to the Service. We process your data only to provide
              and improve the Service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">6. Intellectual Property</h2>
            <p className="text-foreground-muted mb-4">
              The Service and its original content, features, and functionality are owned by CLIMATRIX and
              are protected by international copyright, trademark, and other intellectual property laws.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">7. Subscription and Payments</h2>
            <p className="text-foreground-muted mb-4">
              Certain features of the Service require a paid subscription. You agree to pay all applicable
              fees and charges. Subscription fees are billed in advance on a monthly or annual basis.
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li>Prices may change with 30 days' notice</li>
              <li>You may cancel your subscription at any time</li>
              <li>Refunds are provided in accordance with our refund policy</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">8. Disclaimer of Warranties</h2>
            <p className="text-foreground-muted mb-4">
              The Service is provided "as is" without warranties of any kind. While we strive for accuracy
              in emission calculations, the results should be verified by qualified professionals before
              official reporting or compliance purposes.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">9. Limitation of Liability</h2>
            <p className="text-foreground-muted mb-4">
              In no event shall CLIMATRIX be liable for any indirect, incidental, special, consequential,
              or punitive damages arising from your use of the Service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">10. Changes to Terms</h2>
            <p className="text-foreground-muted mb-4">
              We reserve the right to modify these Terms at any time. We will notify users of any material
              changes via email or through the Service. Your continued use of the Service after such
              modifications constitutes acceptance of the updated Terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">11. Contact Us</h2>
            <p className="text-foreground-muted">
              If you have any questions about these Terms, please contact us at:
            </p>
            <p className="text-foreground mt-2">
              <a href="mailto:legal@climatrix.io" className="text-primary hover:underline">
                legal@climatrix.io
              </a>
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="max-w-4xl mx-auto px-4 text-center text-foreground-muted">
          <p>&copy; {new Date().getFullYear()} CLIMATRIX. All rights reserved.</p>
          <div className="mt-4 flex justify-center gap-6">
            <Link href="/terms" className="hover:text-foreground transition-colors">
              Terms of Service
            </Link>
            <Link href="/privacy" className="hover:text-foreground transition-colors">
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
