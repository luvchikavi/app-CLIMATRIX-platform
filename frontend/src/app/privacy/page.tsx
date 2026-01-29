'use client';

import Link from 'next/link';
import { Leaf, ArrowLeft } from 'lucide-react';

export default function PrivacyPolicyPage() {
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
        <h1 className="text-3xl font-bold text-foreground mb-2">Privacy Policy</h1>
        <p className="text-foreground-muted mb-8">Last updated: January 2025</p>

        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">1. Introduction</h2>
            <p className="text-foreground-muted mb-4">
              CLIMATRIX ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy
              explains how we collect, use, disclose, and safeguard your information when you use our carbon
              accounting platform.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">2. Information We Collect</h2>

            <h3 className="text-lg font-medium text-foreground mb-3">2.1 Account Information</h3>
            <p className="text-foreground-muted mb-4">
              When you create an account, we collect:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2 mb-4">
              <li>Email address</li>
              <li>Full name</li>
              <li>Organization name</li>
              <li>Country/Region</li>
              <li>Password (encrypted)</li>
            </ul>

            <h3 className="text-lg font-medium text-foreground mb-3">2.2 Emissions Data</h3>
            <p className="text-foreground-muted mb-4">
              To provide our services, we collect and process:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2 mb-4">
              <li>Activity data (fuel consumption, electricity usage, travel data, etc.)</li>
              <li>Site and facility information</li>
              <li>Imported files and documents</li>
              <li>Calculated emissions data</li>
              <li>Report outputs</li>
            </ul>

            <h3 className="text-lg font-medium text-foreground mb-3">2.3 Usage Data</h3>
            <p className="text-foreground-muted mb-4">
              We automatically collect:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li>Log data (IP address, browser type, pages visited)</li>
              <li>Device information</li>
              <li>Usage patterns and feature interactions</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">3. How We Use Your Information</h2>
            <p className="text-foreground-muted mb-4">
              We use the collected information to:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li>Provide, maintain, and improve our carbon accounting services</li>
              <li>Calculate GHG emissions based on your activity data</li>
              <li>Generate reports and compliance documentation</li>
              <li>Send you transactional emails (password resets, notifications)</li>
              <li>Provide customer support</li>
              <li>Analyze usage to improve our platform</li>
              <li>Ensure security and prevent fraud</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">4. Data Sharing and Disclosure</h2>
            <p className="text-foreground-muted mb-4">
              We do not sell your personal information. We may share data with:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li><strong>Service Providers:</strong> Third parties that help us operate our platform (cloud hosting, payment processing, analytics)</li>
              <li><strong>Legal Requirements:</strong> When required by law or to protect our rights</li>
              <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
              <li><strong>With Your Consent:</strong> When you explicitly authorize us to share your data</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">5. Data Security</h2>
            <p className="text-foreground-muted mb-4">
              We implement industry-standard security measures to protect your data:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li>Encryption of data in transit (TLS/SSL) and at rest</li>
              <li>Secure password hashing</li>
              <li>Regular security audits and updates</li>
              <li>Access controls and authentication</li>
              <li>Automated backup systems</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">6. Data Retention</h2>
            <p className="text-foreground-muted mb-4">
              We retain your data for as long as your account is active or as needed to provide services.
              After account deletion, we may retain certain data:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li>For legal compliance purposes</li>
              <li>To resolve disputes</li>
              <li>To enforce our agreements</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">7. Your Rights</h2>
            <p className="text-foreground-muted mb-4">
              Depending on your location, you may have the right to:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li><strong>Access:</strong> Request a copy of your personal data</li>
              <li><strong>Rectification:</strong> Correct inaccurate data</li>
              <li><strong>Erasure:</strong> Request deletion of your data</li>
              <li><strong>Portability:</strong> Receive your data in a portable format</li>
              <li><strong>Objection:</strong> Object to certain processing activities</li>
              <li><strong>Restriction:</strong> Request limited processing of your data</li>
            </ul>
            <p className="text-foreground-muted mt-4">
              To exercise these rights, contact us at{' '}
              <a href="mailto:privacy@climatrix.io" className="text-primary hover:underline">
                privacy@climatrix.io
              </a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">8. International Data Transfers</h2>
            <p className="text-foreground-muted mb-4">
              Your data may be transferred to and processed in countries other than your own. We ensure
              appropriate safeguards are in place, including Standard Contractual Clauses for transfers
              from the EU/EEA.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">9. Cookies and Tracking</h2>
            <p className="text-foreground-muted mb-4">
              We use essential cookies to operate the platform. We may also use:
            </p>
            <ul className="list-disc list-inside text-foreground-muted space-y-2">
              <li>Authentication cookies to keep you logged in</li>
              <li>Preference cookies to remember your settings</li>
              <li>Analytics cookies to understand platform usage</li>
            </ul>
            <p className="text-foreground-muted mt-4">
              You can control cookie settings through your browser preferences.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">10. Children's Privacy</h2>
            <p className="text-foreground-muted mb-4">
              Our Service is not intended for individuals under 18 years of age. We do not knowingly
              collect personal information from children.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">11. Changes to This Policy</h2>
            <p className="text-foreground-muted mb-4">
              We may update this Privacy Policy from time to time. We will notify you of any material
              changes by posting the new policy on this page and updating the "Last updated" date.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">12. Contact Us</h2>
            <p className="text-foreground-muted">
              If you have questions about this Privacy Policy or our data practices, please contact:
            </p>
            <div className="mt-4 p-4 bg-background-muted rounded-lg">
              <p className="text-foreground font-medium">CLIMATRIX Privacy Team</p>
              <p className="text-foreground-muted mt-1">
                Email:{' '}
                <a href="mailto:privacy@climatrix.io" className="text-primary hover:underline">
                  privacy@climatrix.io
                </a>
              </p>
            </div>
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
