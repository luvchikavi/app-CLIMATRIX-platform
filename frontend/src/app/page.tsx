'use client';

declare global {
  interface Window {
    google: any;
  }
}

import { useState, useEffect, useRef, Suspense } from 'react';
import { useAuthStore } from '@/stores/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import { cn } from '@/lib/utils';
import { COUNTRIES } from '@/lib/countries';
import { plans } from '@/lib/pricing';
import {
  Leaf,
  Loader2,
  LogIn,
  ArrowRight,
  Check,
  Flame,
  Zap,
  Globe,
  Shield,
  TrendingUp,
  FileText,
  Building2,
  Sparkles,
  X,
  BarChart3,
  Brain,
  Lock,
  Users,
  Target,
  ChevronRight,
  Linkedin,
  Mail,
  ExternalLink,
  Rocket,
  DollarSign,
  Star,
} from 'lucide-react';

// Team data from climatrix.io
const team = [
  {
    name: 'Avi Luvchik',
    role: 'CEO',
    bio: 'Advisor and Board Member in climate tech companies with extensive experience in sustainability solutions.',
    image: '/images/team/avi.jpeg',
    linkedin: '#',
  },
  {
    name: 'Lihie Iuclea',
    role: 'CSO at BDO',
    bio: 'International UNEP climate policy consultant, Head of ESG with deep expertise in regulatory frameworks.',
    image: '/images/team/lihie.jpeg',
    linkedin: '#',
  },
  {
    name: 'Chezi Shpaisman',
    role: 'CTO',
    bio: 'Founder at Sakkoya Data Management Solutions, expert in data architecture and scalable systems.',
    image: '/images/team/chezi.jpeg',
    linkedin: '#',
  },
  {
    name: 'Leehee Goldenberg',
    role: 'CRO',
    bio: 'Lawyer specializing in energy, infrastructure, and climate governance with regulatory expertise.',
    image: '/images/team/leehee.jpeg',
    linkedin: '#',
  },
];

// Statistics
const stats = [
  { value: '15+', label: 'Scope 3 Categories' },
  { value: '99.9%', label: 'Uptime SLA' },
  { value: '20+', label: 'CBAM Products' },
  { value: '50+', label: 'Emission Factors' },
];

// Features/Services
const features = [
  {
    icon: BarChart3,
    title: 'GHG Emissions Tracking',
    description: 'Complete Scope 1, 2, and 3 emissions tracking with AI-powered data extraction and automated calculations.',
    gradient: 'from-emerald-500 to-teal-500',
  },
  {
    icon: Globe,
    title: 'CBAM Compliance',
    description: 'Full EU Carbon Border Adjustment Mechanism support with quarterly reporting and certificate management.',
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    icon: FileText,
    title: 'LCA & EPD Management',
    description: 'Life Cycle Assessment and Environmental Product Declaration management for comprehensive sustainability.',
    gradient: 'from-violet-500 to-purple-500',
  },
  {
    icon: Target,
    title: 'Scenario Planning',
    description: 'Model reduction scenarios and plan net-zero pathways with data-driven insights and forecasting.',
    gradient: 'from-orange-500 to-amber-500',
  },
  {
    icon: Brain,
    title: 'AI-Powered Insights',
    description: 'Intelligent data processing, automatic factor matching, and smart recommendations for emission reduction.',
    gradient: 'from-pink-500 to-rose-500',
  },
  {
    icon: Lock,
    title: 'Enterprise Security',
    description: 'SOC 2 ready, comprehensive audit logging, GDPR compliance, and multi-tenant data isolation.',
    gradient: 'from-slate-500 to-zinc-500',
  },
];

// Standards & Compliance
const standards = [
  'GHG Protocol',
  'ISO 14064',
  'CSRD',
  'CBAM',
  'TCFD',
  'SBTi',
];

function LandingPageContent() {
  const searchParams = useSearchParams();
  const [showLogin, setShowLogin] = useState(searchParams.get('login') === 'true');
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [countryCode, setCountryCode] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [googleReady, setGoogleReady] = useState(false);
  const { login, googleLogin, register, isLoading, error, clearError, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();
  const googleInitialized = useRef(false);

  useEffect(() => {
    if (searchParams.get('reset') === 'true') {
      logout();
      setShowLogin(true);
    } else if (searchParams.get('login') === 'true') {
      setShowLogin(true);
    }
  }, [searchParams, logout]);

  useEffect(() => {
    if (isAuthenticated && !searchParams.get('reset')) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router, searchParams]);

  // Load Google Identity Services script
  useEffect(() => {
    const existingScript = document.getElementById('google-gsi-script');
    if (existingScript) {
      if (window.google?.accounts?.id) setGoogleReady(true);
      else existingScript.addEventListener('load', () => setGoogleReady(true));
      return;
    }
    const script = document.createElement('script');
    script.id = 'google-gsi-script';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setGoogleReady(true);
    document.head.appendChild(script);
  }, []);

  // Initialize Google Sign-In and render button when script is ready and modal is visible
  useEffect(() => {
    if (!googleReady || !showLogin || !window.google?.accounts?.id) return;
    const container = document.getElementById('google-btn-container');
    if (!container) return;

    if (!googleInitialized.current) {
      window.google.accounts.id.initialize({
        client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
        callback: async (response: any) => {
          try {
            await googleLogin(response.credential);
            router.push('/dashboard');
          } catch {
            // Error is handled by the store
          }
        },
      });
      googleInitialized.current = true;
    }

    container.innerHTML = '';
    window.google.accounts.id.renderButton(container, {
      type: 'standard',
      theme: 'filled_black',
      size: 'large',
      text: 'continue_with',
      shape: 'pill',
      width: Math.min(container.offsetWidth || 380, 400),
    });
  }, [googleReady, showLogin, googleLogin, router]);

  if (isAuthenticated) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      if (isRegistering) {
        await register({
          email,
          password,
          full_name: fullName,
          organization_name: organizationName,
          country_code: countryCode || undefined,
        });
      } else {
        await login(email, password);
      }
      router.push('/dashboard');
    } catch {
      // Error is handled by the store
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setFullName('');
    setOrganizationName('');
    setCountryCode('');
    setTermsAccepted(false);
    clearError();
  };

  const toggleMode = () => {
    resetForm();
    setIsRegistering(!isRegistering);
  };

  return (
    <div className="min-h-screen bg-[#0a0f1a] text-white overflow-x-hidden">
      {/* Animated Background Gradient */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-emerald-500/10 via-transparent to-transparent rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-cyan-500/10 via-transparent to-transparent rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-gradient-to-br from-violet-500/5 to-transparent rounded-full blur-3xl" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0f1a]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
                <Leaf className="w-7 h-7 text-white" />
              </div>
              <div>
                <span className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">CLIMATRIX</span>
                <p className="text-[10px] text-gray-500 uppercase tracking-[0.2em]">Carbon Intelligence</p>
              </div>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
                Features
              </a>
              <a href="#pricing" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
                Pricing
              </a>
              <a href="#team" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
                Team
              </a>
              <a href="#standards" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
                Standards
              </a>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowLogin(true)}
                className="px-6 py-2.5 text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={() => { setShowLogin(true); setIsRegistering(true); }}
                className="px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl font-medium text-sm hover:shadow-lg hover:shadow-emerald-500/25 transition-all hover:-translate-y-0.5"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-40 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm font-medium mb-8 backdrop-blur-sm">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span className="text-gray-300">In Partnership with</span>
              <span className="text-white font-semibold">BDO</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.1] mb-8">
              <span className="text-white">Enterprise Carbon</span>
              <br />
              <span className="bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
                Intelligence Platform
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed">
              Measure, track, and reduce your environmental impact with AI-powered carbon accounting.
              Built on GHG Protocol, ISO 14064, CSRD, and CBAM standards.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
              <button
                onClick={() => { setShowLogin(true); setIsRegistering(true); }}
                className="group px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-2xl font-semibold text-lg hover:shadow-2xl hover:shadow-emerald-500/30 transition-all hover:-translate-y-1 flex items-center gap-3"
              >
                Start Free Trial
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <a
                href="#features"
                className="px-8 py-4 bg-white/5 border border-white/10 text-white rounded-2xl font-semibold text-lg hover:bg-white/10 transition-all backdrop-blur-sm"
              >
                Explore Features
              </a>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
              {stats.map((stat, i) => (
                <div key={i} className="text-center p-4">
                  <div className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent mb-1">
                    {stat.value}
                  </div>
                  <div className="text-sm text-gray-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium mb-6">
              <BarChart3 className="w-4 h-4" />
              Platform Features
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
              Complete Carbon Management
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Everything you need to measure, manage, and reduce your organization&apos;s environmental impact.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <div
                  key={i}
                  className="group relative p-8 rounded-3xl bg-white/[0.02] border border-white/5 hover:border-white/10 hover:bg-white/[0.04] transition-all duration-300 hover:-translate-y-1"
                >
                  <div className={cn(
                    'w-14 h-14 rounded-2xl bg-gradient-to-br flex items-center justify-center mb-6 shadow-lg',
                    feature.gradient
                  )}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Standards Section */}
      <section id="standards" className="relative py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-transparent via-emerald-950/20 to-transparent">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-2xl font-semibold text-white mb-12">Built on Global Standards</h2>
          <div className="flex flex-wrap items-center justify-center gap-4 md:gap-8">
            {standards.map((standard, i) => (
              <div
                key={i}
                className="px-6 py-3 rounded-full bg-white/5 border border-white/10 text-gray-300 font-medium backdrop-blur-sm hover:bg-white/10 hover:border-white/20 transition-all cursor-default"
              >
                {standard}
              </div>
            ))}
          </div>
          <div className="mt-12 flex items-center justify-center gap-8 text-gray-500">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-emerald-500" />
              <span className="text-sm">SOC 2 Ready</span>
            </div>
            <div className="flex items-center gap-2">
              <Lock className="w-5 h-5 text-emerald-500" />
              <span className="text-sm">GDPR Compliant</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-emerald-500" />
              <span className="text-sm">24/7 Encryption</span>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="relative py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-medium mb-6">
              <DollarSign className="w-4 h-4" />
              Pricing Plans
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
              Enterprise Features, Transparent Pricing
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Start with a 14-day free trial. No credit card required.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {plans.map((plan) => {
              const iconMap: Record<string, typeof Zap> = { Zap, Building2, Rocket };
              const Icon = iconMap[plan.icon] || Zap;
              return (
                <div
                  key={plan.name}
                  className={cn(
                    'relative p-8 rounded-3xl border transition-all duration-300 hover:-translate-y-1',
                    plan.popular
                      ? 'bg-white/[0.06] border-emerald-500/30 shadow-lg shadow-emerald-500/10'
                      : 'bg-white/[0.02] border-white/5 hover:border-white/10 hover:bg-white/[0.04]'
                  )}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-3 py-1 bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-xs font-semibold rounded-full flex items-center gap-1">
                        <Star className="w-3 h-3" /> Most Popular
                      </span>
                    </div>
                  )}
                  <div className="flex items-center gap-3 mb-4">
                    <div className={cn(
                      'w-10 h-10 rounded-xl flex items-center justify-center',
                      plan.popular ? 'bg-emerald-500/20' : 'bg-white/5'
                    )}>
                      <Icon className={cn('w-5 h-5', plan.popular ? 'text-emerald-400' : 'text-gray-400')} />
                    </div>
                    <h3 className="text-xl font-semibold text-white">{plan.name}</h3>
                  </div>
                  <div className="mb-6">
                    {plan.monthlyPrice != null ? (
                      <div className="flex items-baseline gap-1">
                        <span className="text-4xl font-bold text-white">${plan.monthlyPrice.toLocaleString()}</span>
                        <span className="text-gray-500">/month</span>
                      </div>
                    ) : (
                      <div className="flex items-baseline gap-1">
                        <span className="text-4xl font-bold text-white">Custom</span>
                      </div>
                    )}
                    <p className="text-sm text-gray-500 mt-1">{plan.description}</p>
                  </div>
                  <ul className="space-y-2.5 mb-8">
                    {plan.features.slice(0, 5).map((feature, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-300">{feature}</span>
                      </li>
                    ))}
                    {plan.features.length > 5 && (
                      <li className="text-sm text-gray-500">+{plan.features.length - 5} more features</li>
                    )}
                  </ul>
                  <button
                    onClick={() => { setShowLogin(true); setIsRegistering(true); }}
                    className={cn(
                      'w-full py-3 rounded-xl font-semibold text-sm transition-all',
                      plan.popular
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:shadow-lg hover:shadow-emerald-500/25 hover:-translate-y-0.5'
                        : 'bg-white/5 border border-white/10 text-white hover:bg-white/10'
                    )}
                  >
                    {plan.cta}
                  </button>
                </div>
              );
            })}
          </div>

          <div className="text-center">
            <a
              href="/pricing"
              className="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
            >
              See Full Comparison
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section id="team" className="relative py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm font-medium mb-6">
              <Users className="w-4 h-4" />
              Leadership Team
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
              Meet the Experts
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Industry veterans bringing decades of experience in climate technology, sustainability consulting, and enterprise solutions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {team.map((member, i) => (
              <div
                key={i}
                className="group relative p-6 rounded-3xl bg-white/[0.02] border border-white/5 hover:border-white/10 hover:bg-white/[0.04] transition-all duration-300 text-center"
              >
                {/* Team Photo */}
                <div className="w-28 h-28 mx-auto mb-6 rounded-full bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border-2 border-white/10 overflow-hidden">
                  <img
                    src={member.image}
                    alt={member.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <h3 className="text-lg font-semibold text-white mb-1">{member.name}</h3>
                <p className="text-emerald-400 text-sm font-medium mb-4">{member.role}</p>
                <p className="text-gray-500 text-sm leading-relaxed mb-4">{member.bio}</p>
                <a
                  href={member.linkedin}
                  className="inline-flex items-center gap-2 text-gray-400 hover:text-white text-sm transition-colors"
                >
                  <Linkedin className="w-4 h-4" />
                  LinkedIn
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="relative p-12 sm:p-16 rounded-[2.5rem] bg-gradient-to-br from-emerald-500/10 via-teal-500/5 to-cyan-500/10 border border-white/10 text-center overflow-hidden">
            {/* Background Glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent pointer-events-none" />

            <h2 className="relative text-3xl sm:text-4xl font-bold text-white mb-6">
              Ready to Start Your Carbon Journey?
            </h2>
            <p className="relative text-lg text-gray-400 mb-10 max-w-xl mx-auto">
              Join organizations already using CLIMATRIX to measure, manage, and reduce their environmental impact.
            </p>
            <div className="relative flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => { setShowLogin(true); setIsRegistering(true); }}
                className="group px-8 py-4 bg-white text-[#0a0f1a] rounded-2xl font-semibold text-lg hover:shadow-2xl hover:shadow-white/20 transition-all hover:-translate-y-1 flex items-center gap-3"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <a
                href="mailto:contact@climatrix.io"
                className="px-8 py-4 bg-white/5 border border-white/10 text-white rounded-2xl font-semibold text-lg hover:bg-white/10 transition-all backdrop-blur-sm flex items-center gap-2"
              >
                <Mail className="w-5 h-5" />
                Contact Sales
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative py-12 px-4 sm:px-6 lg:px-8 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                <Leaf className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-semibold text-white">CLIMATRIX</span>
            </div>
            <div className="flex items-center gap-8 text-sm text-gray-500">
              <a href="/privacy" className="hover:text-white transition-colors">Privacy Policy</a>
              <a href="/terms" className="hover:text-white transition-colors">Terms of Service</a>
              <a href="mailto:contact@climatrix.io" className="hover:text-white transition-colors">Contact</a>
            </div>
            <p className="text-sm text-gray-600">
              2026 CLIMATRIX. All rights reserved.
            </p>
          </div>
        </div>
      </footer>

      {/* Login/Register Modal */}
      {showLogin && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => { setShowLogin(false); resetForm(); setIsRegistering(false); }}
          />

          {/* Modal */}
          <div className="relative bg-[#0f1629] rounded-3xl shadow-2xl w-full max-w-md p-8 border border-white/10 max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in duration-200">
            <button
              onClick={() => { setShowLogin(false); resetForm(); setIsRegistering(false); }}
              className="absolute top-4 right-4 p-2 text-gray-500 hover:text-white transition-colors rounded-xl hover:bg-white/5"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-500/25">
                <Leaf className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white">
                {isRegistering ? 'Create Account' : 'Welcome Back'}
              </h2>
              <p className="text-gray-500 mt-1">
                {isRegistering ? 'Start your carbon journey' : 'Sign in to your account'}
              </p>
            </div>

            {/* Google Sign-In Button */}
            <div id="google-btn-container" className="flex justify-center mb-4 min-h-[44px]" />

            {/* Divider */}
            <div className="relative flex items-center gap-4 mb-4">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-xs text-gray-500 uppercase tracking-wider">or continue with email</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {isRegistering && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="John Smith"
                      required
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Organization Name
                    </label>
                    <input
                      type="text"
                      value={organizationName}
                      onChange={(e) => setOrganizationName(e.target.value)}
                      placeholder="Acme Corporation"
                      required
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Country (Optional)
                    </label>
                    <select
                      value={countryCode}
                      onChange={(e) => setCountryCode(e.target.value)}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
                    >
                      <option value="" className="bg-[#0f1629]">Select country...</option>
                      {COUNTRIES.map((c) => (
                        <option key={c.code} value={c.code} className="bg-[#0f1629]">{c.name}</option>
                      ))}
                    </select>
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  required
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={isRegistering ? 'Create a password' : 'Enter your password'}
                  required
                  minLength={isRegistering ? 6 : undefined}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
                />
                {isRegistering ? (
                  <p className="text-xs text-gray-600 mt-1">Minimum 6 characters</p>
                ) : (
                  <div className="flex justify-end mt-2">
                    <a
                      href="/forgot-password"
                      className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
                    >
                      Forgot password?
                    </a>
                  </div>
                )}
              </div>

              {isRegistering && (
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    id="terms"
                    checked={termsAccepted}
                    onChange={(e) => setTermsAccepted(e.target.checked)}
                    className="mt-1 w-4 h-4 rounded border-white/20 bg-white/5 text-emerald-500 focus:ring-emerald-500/50"
                  />
                  <label htmlFor="terms" className="text-sm text-gray-400">
                    I agree to the{' '}
                    <a href="/terms" target="_blank" className="text-emerald-400 hover:underline">
                      Terms of Service
                    </a>{' '}
                    and{' '}
                    <a href="/privacy" target="_blank" className="text-emerald-400 hover:underline">
                      Privacy Policy
                    </a>
                  </label>
                </div>
              )}

              {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || (isRegistering && !termsAccepted)}
                className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-emerald-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all hover:-translate-y-0.5"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    {isRegistering ? 'Creating account...' : 'Signing in...'}
                  </>
                ) : (
                  <>
                    {isRegistering ? 'Create Account' : 'Sign In'}
                    <ChevronRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-500">
                {isRegistering ? (
                  <>
                    Already have an account?{' '}
                    <button
                      onClick={toggleMode}
                      className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                    >
                      Sign in
                    </button>
                  </>
                ) : (
                  <>
                    Don&apos;t have an account?{' '}
                    <button
                      onClick={toggleMode}
                      className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                    >
                      Create one
                    </button>
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Wrap with Suspense for useSearchParams
export default function LandingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0a0f1a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center animate-pulse">
            <Leaf className="w-7 h-7 text-white" />
          </div>
          <Loader2 className="w-6 h-6 text-emerald-500 animate-spin" />
        </div>
      </div>
    }>
      <LandingPageContent />
    </Suspense>
  );
}
