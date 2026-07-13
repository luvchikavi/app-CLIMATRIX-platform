'use client';

import Link from 'next/link';
import {
  Leaf,
  ArrowLeft,
  Shield,
  Lock,
  Server,
  Eye,
  KeyRound,
  Users,
  FileCheck,
  Globe,
  AlertTriangle,
  CheckCircle2,
  Database,
  RefreshCw,
} from 'lucide-react';

const securityFeatures = [
  {
    icon: Lock,
    title: 'Encryption at Rest & in Transit',
    description:
      'All data is encrypted using AES-256 at rest and TLS 1.2+ (HTTPS) in transit. Database connections, API calls, and file transfers are fully encrypted end-to-end.',
  },
  {
    icon: KeyRound,
    title: 'Authentication & Access Control',
    description:
      'Secure JWT-based authentication with bcrypt password hashing (work factor 12). Support for Google OAuth 2.0 SSO. Role-based access control (RBAC) with organization-level tenant isolation.',
  },
  {
    icon: Shield,
    title: 'Rate Limiting & Abuse Prevention',
    description:
      'API rate limiting on all sensitive endpoints — login (10/min), registration (5/min), password reset (5/min), and data imports (20/min). Protects against brute-force and credential-stuffing attacks.',
  },
  {
    icon: Server,
    title: 'Infrastructure Security',
    description:
      'Hosted on Railway (backend) and Vercel (frontend) — both SOC 2 Type II certified providers. Automatic SSL certificate management, DDoS protection, and network-level firewalling included by default.',
  },
  {
    icon: Database,
    title: 'Multi-Tenant Data Isolation',
    description:
      'Strict organization-level data isolation. Every database query is scoped to the authenticated user\'s organization. No cross-tenant data access is possible at the application layer.',
  },
  {
    icon: Eye,
    title: 'Audit Logging',
    description:
      'Comprehensive audit trail for all data modifications, user actions, and administrative operations. Logs include timestamps, user identifiers, and action details for full traceability.',
  },
  {
    icon: RefreshCw,
    title: 'Backup & Disaster Recovery',
    description:
      'Automated daily database backups with point-in-time recovery. Infrastructure runs in highly available configurations with automatic failover and health monitoring.',
  },
  {
    icon: AlertTriangle,
    title: 'Vulnerability Management',
    description:
      'Continuous dependency scanning, automated CI/CD security checks, and regular code reviews. Input validation and parameterized queries protect against injection attacks (SQLi, XSS, CSRF).',
  },
];

const standards = [
  {
    name: 'GHG Protocol',
    description: 'Corporate Accounting & Reporting Standard for Scope 1, 2, and 3 emissions. The global benchmark for measuring and managing greenhouse gas emissions.',
  },
  {
    name: 'ISO 14064',
    description: 'International standard for quantification, monitoring, and reporting of GHG emissions and removals at the organizational and project level.',
  },
  {
    name: 'CSRD / ESRS',
    description: 'EU Corporate Sustainability Reporting Directive and European Sustainability Reporting Standards for mandatory ESG disclosures.',
  },
  {
    name: 'EU CBAM',
    description: 'Carbon Border Adjustment Mechanism — quarterly reporting of embedded emissions for goods imported into the EU, with certificate management.',
  },
  {
    name: 'TCFD',
    description: 'Task Force on Climate-related Financial Disclosures framework for climate risk reporting aligned with financial disclosures.',
  },
  {
    name: 'SBTi',
    description: 'Science Based Targets initiative — target setting and tracking aligned with Paris Agreement goals for net-zero pathways.',
  },
  {
    name: 'PCAF',
    description: 'Partnership for Carbon Accounting Financials — data quality scoring methodology for financial institutions\' financed emissions.',
  },
  {
    name: 'DEFRA',
    description: 'UK Department for Environment, Food & Rural Affairs emission factors database used for accurate GHG conversion calculations.',
  },
];

const complianceItems = [
  {
    icon: CheckCircle2,
    title: 'GDPR Compliance',
    description: 'Full compliance with the EU General Data Protection Regulation. Data minimization, right to erasure, data portability, and explicit consent management.',
  },
  {
    icon: CheckCircle2,
    title: 'SOC 2 Ready',
    description: 'Platform architecture designed to meet SOC 2 Type II requirements across security, availability, processing integrity, confidentiality, and privacy.',
  },
  {
    icon: CheckCircle2,
    title: 'Data Residency',
    description: 'Infrastructure deployed in regions that comply with local data residency requirements. Data processing and storage locations are transparent and documented.',
  },
  {
    icon: CheckCircle2,
    title: 'Data Processing Agreement',
    description: 'Standard DPA available for all enterprise customers, covering data processing terms, sub-processors, and contractual obligations under applicable privacy laws.',
  },
];

export default function SecurityPage() {
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
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-8 h-8 text-emerald-500" />
          <h1 className="text-3xl font-bold text-foreground">Security & Compliance</h1>
        </div>
        <p className="text-foreground-muted mb-12">
          Last updated: March 2026 &mdash; CLIMATRIX is built with enterprise-grade security at every layer.
        </p>

        {/* Overview */}
        <section className="mb-12">
          <div className="p-6 rounded-2xl bg-emerald-500/5 border border-emerald-500/20">
            <h2 className="text-xl font-semibold text-foreground mb-3">Our Commitment</h2>
            <p className="text-foreground-muted leading-relaxed">
              CLIMATRIX handles sensitive environmental and operational data for organizations worldwide.
              We treat data security and privacy as foundational — not optional. Our platform is designed
              with defense-in-depth principles, multi-tenant isolation, and compliance with international
              standards including GDPR, GHG Protocol, ISO 14064, CSRD, and CBAM.
            </p>
          </div>
        </section>

        {/* Security Features */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-foreground mb-6">Platform Security</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {securityFeatures.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <div
                  key={i}
                  className="p-5 rounded-xl border border-border hover:border-emerald-500/30 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Icon className="w-5 h-5 text-emerald-500" />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-foreground mb-1">{feature.title}</h3>
                      <p className="text-sm text-foreground-muted leading-relaxed">{feature.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Standards & Frameworks */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-foreground mb-2">Standards & Frameworks</h2>
          <p className="text-foreground-muted mb-6">
            CLIMATRIX is built on and aligned with the following international environmental and reporting standards.
          </p>
          <div className="space-y-3">
            {standards.map((standard, i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-border hover:border-emerald-500/30 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <Globe className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-base font-semibold text-foreground">{standard.name}</h3>
                    <p className="text-sm text-foreground-muted">{standard.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Compliance & Privacy */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-foreground mb-2">Compliance & Privacy</h2>
          <p className="text-foreground-muted mb-6">
            We maintain compliance with applicable data protection regulations and industry best practices.
          </p>
          <div className="space-y-3">
            {complianceItems.map((item, i) => {
              const Icon = item.icon;
              return (
                <div
                  key={i}
                  className="p-4 rounded-xl border border-border hover:border-emerald-500/30 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <Icon className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-base font-semibold text-foreground">{item.title}</h3>
                      <p className="text-sm text-foreground-muted">{item.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Technical Details */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-foreground mb-6">Technical Security Details</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-semibold text-foreground">Category</th>
                  <th className="text-left py-3 px-4 font-semibold text-foreground">Implementation</th>
                </tr>
              </thead>
              <tbody className="text-foreground-muted">
                <tr className="border-b border-border/50">
                  <td className="py-3 px-4 font-medium text-foreground">Password Hashing</td>
                  <td className="py-3 px-4">bcrypt with work factor 12</td>
                </tr>
                <tr className="border-b border-border/50">
                  <td className="py-3 px-4 font-medium text-foreground">Session Tokens</td>
                  <td className="py-3 px-4">JWT (JSON Web Tokens) with configurable expiration</td>
                </tr>
                <tr className="border-b border-border/50">
                  <td className="py-3 px-4 font-medium text-foreground">Transport Security</td>
                  <td className="py-3 px-4">TLS 1.2+ enforced on all endpoints (HTTPS only)</td>
                </tr>
                <tr className="border-b border-border/50">
                  <td className="py-3 px-4 font-medium text-foreground">Data Encryption</td>
                  <td className="py-3 px-4">AES-256 at rest (provider-managed keys)</td>
                </tr>
                <tr className="border-b border-border/50">
                  <td className="py-3 px-4 font-medium text-foreground">API Rate Limiting</td>
                  <td className="py-3 px-4">Per-endpoint limits with Redis-backed distributed counters</td>
                </tr>
                <tr className="border-b border-border/50">
                  <td className="py-3 px-4 font-medium text-foreground">File Upload Limits</td>
                  <td className="py-3 px-4">50 MB maximum per upload with server-side validation</td>
                </tr>
                <tr className="border-b border-border/50">
                  <td className="py-3 px-4 font-medium text-foreground">SSO</td>
                  <td className="py-3 px-4">Google OAuth 2.0 (additional providers on request)</td>
                </tr>
                <tr className="border-b border-border/50">
                  <td className="py-3 px-4 font-medium text-foreground">Database</td>
                  <td className="py-3 px-4">PostgreSQL with parameterized queries (SQLAlchemy ORM)</td>
                </tr>
                <tr className="border-b border-border/50">
                  <td className="py-3 px-4 font-medium text-foreground">CI/CD</td>
                  <td className="py-3 px-4">GitHub Actions with automated linting, testing, and build verification</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium text-foreground">Error Monitoring</td>
                  <td className="py-3 px-4">Sentry integration for real-time error tracking and alerting</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Contact */}
        <section className="mb-8">
          <div className="p-6 rounded-2xl border border-border">
            <div className="flex items-start gap-3">
              <Users className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
              <div>
                <h2 className="text-xl font-semibold text-foreground mb-2">Security Inquiries</h2>
                <p className="text-foreground-muted mb-4">
                  If you have security questions, need a detailed security questionnaire response, or want to
                  report a vulnerability, please contact our security team.
                </p>
                <div className="flex flex-wrap gap-4">
                  <a
                    href="mailto:security@climatrix.co"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium text-sm hover:bg-emerald-500/20 transition-colors"
                  >
                    <FileCheck className="w-4 h-4" />
                    security@climatrix.co
                  </a>
                  <a
                    href="mailto:contact@climatrix.co"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-border text-foreground-muted font-medium text-sm hover:bg-white/10 transition-colors"
                  >
                    General: contact@climatrix.co
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
