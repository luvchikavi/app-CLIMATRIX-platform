'use client';

import { useState, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { AppShell } from '@/components/layout';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
  Button,
  Input,
} from '@/components/ui';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import {
  Briefcase,
  TrendingUp,
  Target,
  Users,
  DollarSign,
  Award,
  ChevronDown,
  ChevronUp,
  Shield,
  Loader2,
  Download,
  BarChart3,
  PieChart as PieChartIcon,
  Zap,
  Globe,
  CheckCircle2,
  XCircle,
  Building2,
} from 'lucide-react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Assumptions {
  // Market
  totalAddressableMarket: number;
  initialPenetrationPct: number;
  annualGrowthOptimistic: number;
  annualGrowthRealistic: number;
  annualGrowthPessimistic: number;

  // Pricing (monthly)
  starterPrice: number;
  professionalPrice: number;
  enterprisePrice: number;

  // Customer Mix (% of total)
  starterMixPct: number;
  professionalMixPct: number;
  enterpriseMixPct: number;

  // Churn
  annualChurnPct: number;

  // Costs
  implementationCostPerCustomer: number;
  monthlyHostingPerCustomer: number;
  salaryExpenseMonthly: number;
  marketingBudgetMonthly: number;
  supportCostPerCustomer: number;

  // Add-on adoption
  addOnAdoptionPct: number;
  avgAddOnRevenue: number;

  // SLA
  slaUptimePct: number;
  slaResponseHours: number;

  // Projection years
  projectionYears: number;
}

type ScenarioKey = 'optimistic' | 'realistic' | 'pessimistic';
type TabKey = 'overview' | 'revenue' | 'market' | 'competitive' | 'costs' | 'sla';

interface ScenarioMetrics {
  netCustomers: number;
  starterCustomers: number;
  proCustomers: number;
  entCustomers: number;
  newCustomers: number;
  mrr: number;
  arr: number;
  implementationRevenue: number;
  totalRevenue: number;
  hostingCost: number;
  salaryCost: number;
  marketingCost: number;
  supportCost: number;
  totalCosts: number;
  profit: number;
  margin: number;
  penetration: number;
}

// ─── Default Assumptions ─────────────────────────────────────────────────────

const DEFAULT_ASSUMPTIONS: Assumptions = {
  totalAddressableMarket: 500,
  initialPenetrationPct: 3,
  annualGrowthOptimistic: 45,
  annualGrowthRealistic: 30,
  annualGrowthPessimistic: 15,
  starterPrice: 649,
  professionalPrice: 1449,
  enterprisePrice: 3500,
  starterMixPct: 40,
  professionalMixPct: 45,
  enterpriseMixPct: 15,
  annualChurnPct: 10,
  implementationCostPerCustomer: 5000,
  monthlyHostingPerCustomer: 50,
  salaryExpenseMonthly: 45000,
  marketingBudgetMonthly: 15000,
  supportCostPerCustomer: 100,
  addOnAdoptionPct: 35,
  avgAddOnRevenue: 350,
  slaUptimePct: 99.9,
  slaResponseHours: 4,
  projectionYears: 5,
};

// ─── Color Palette ───────────────────────────────────────────────────────────

const COLORS = {
  optimistic: '#10B981',
  realistic: '#3B82F6',
  pessimistic: '#F59E0B',
  starter: '#8B5CF6',
  professional: '#3B82F6',
  enterprise: '#10B981',
  revenue: '#10B981',
  costs: '#EF4444',
  profit: '#3B82F6',
  pie: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316'],
  strengths: '#10B981',
  weaknesses: '#EF4444',
};

// ─── Competitor Data ─────────────────────────────────────────────────────────

const COMPETITORS = [
  {
    name: 'CLIMATRIX',
    isUs: true,
    pricing: '₪2,400–₪13,000/mo',
    strengths: ['AI-powered extraction', 'Hebrew UI & local support', 'Full Scope 3 (15 categories)', 'CBAM compliance built-in', 'Israeli regulation aligned', 'Fast implementation (2 weeks)'],
    weaknesses: ['New to market', 'Smaller brand recognition'],
    marketFit: 95,
    features: { ghg: 95, cbam: 90, ai: 95, reporting: 90, ux: 92, localSupport: 98, pricing: 85, compliance: 92 },
  },
  {
    name: 'Persefoni',
    isUs: false,
    pricing: '$1,000–$5,000/mo',
    strengths: ['Strong US brand', 'PCAF specialization', 'Large DB of factors'],
    weaknesses: ['No Hebrew', 'No Israeli regulations', 'Complex onboarding', 'Expensive for SMBs'],
    marketFit: 55,
    features: { ghg: 90, cbam: 60, ai: 80, reporting: 85, ux: 70, localSupport: 20, pricing: 50, compliance: 65 },
  },
  {
    name: 'Watershed',
    isUs: false,
    pricing: '$2,000–$10,000/mo',
    strengths: ['Enterprise grade', 'Strong integrations', 'Good UX'],
    weaknesses: ['Very expensive', 'No Hebrew', 'No CBAM', 'No Israeli focus'],
    marketFit: 40,
    features: { ghg: 92, cbam: 30, ai: 85, reporting: 88, ux: 90, localSupport: 10, pricing: 30, compliance: 60 },
  },
  {
    name: 'Sphera',
    isUs: false,
    pricing: 'Custom ($3K+/mo)',
    strengths: ['Deep LCA', 'EPD generation', 'Enterprise features'],
    weaknesses: ['Very complex', 'Long implementation', 'No Hebrew', 'Overkill for most Israeli SMBs'],
    marketFit: 35,
    features: { ghg: 85, cbam: 70, ai: 50, reporting: 80, ux: 45, localSupport: 15, pricing: 25, compliance: 70 },
  },
  {
    name: 'Plan A',
    isUs: false,
    pricing: '€500–€3,000/mo',
    strengths: ['EU-focused', 'Good CSRD support', 'Modern UI'],
    weaknesses: ['No Hebrew', 'Limited CBAM', 'No Israeli presence'],
    marketFit: 45,
    features: { ghg: 82, cbam: 65, ai: 70, reporting: 78, ux: 82, localSupport: 15, pricing: 65, compliance: 75 },
  },
];

const RADAR_CATEGORIES: { key: keyof (typeof COMPETITORS)[number]['features']; label: string }[] = [
  { key: 'ghg', label: 'GHG Tracking' },
  { key: 'cbam', label: 'CBAM' },
  { key: 'ai', label: 'AI Features' },
  { key: 'reporting', label: 'Reporting' },
  { key: 'ux', label: 'UX/Design' },
  { key: 'localSupport', label: 'IL Support' },
  { key: 'pricing', label: 'Pricing Value' },
  { key: 'compliance', label: 'Compliance' },
];

// ─── Israeli Market Context ──────────────────────────────────────────────────

const MARKET_SEGMENTS = [
  { segment: 'Manufacturing & Industrial', companies: 120, avgDeal: 1449, color: '#3B82F6' },
  { segment: 'Energy & Utilities', companies: 45, avgDeal: 3500, color: '#10B981' },
  { segment: 'Construction & Real Estate', companies: 80, avgDeal: 1449, color: '#F59E0B' },
  { segment: 'Food & Agriculture', companies: 65, avgDeal: 649, color: '#EF4444' },
  { segment: 'Tech & Pharma', companies: 90, avgDeal: 1449, color: '#8B5CF6' },
  { segment: 'Transport & Logistics', companies: 50, avgDeal: 649, color: '#EC4899' },
  { segment: 'Finance & Insurance', companies: 30, avgDeal: 3500, color: '#06B6D4' },
  { segment: 'Retail & Services', companies: 20, avgDeal: 649, color: '#F97316' },
];

// ─── Helper: Editable Field ─────────────────────────────────────────────────

function EditableField({
  label,
  value,
  onChange,
  suffix = '',
  prefix = '',
  min = 0,
  max,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  suffix?: string;
  prefix?: string;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-foreground-muted">{label}</label>
      <div className="flex items-center gap-1">
        {prefix && <span className="text-xs text-foreground-muted">{prefix}</span>}
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          min={min}
          max={max}
          step={step}
          className="w-full px-2 py-1.5 text-sm rounded-lg border-0 bg-cy-row text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
        {suffix && <span className="text-xs text-foreground-muted whitespace-nowrap">{suffix}</span>}
      </div>
    </div>
  );
}

// ─── Helper: Scenario Badge ──────────────────────────────────────────────────

function ScenarioBadge({ scenario }: { scenario: ScenarioKey }) {
  const config = {
    optimistic: { bg: 'bg-success/10', text: 'text-success', label: 'Optimistic' },
    realistic: { bg: 'bg-primary/10', text: 'text-primary', label: 'Realistic' },
    pessimistic: { bg: 'bg-warning/10', text: 'text-warning', label: 'Pessimistic' },
  };
  const c = config[scenario];
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  );
}

// ─── Helper: Format Currency ─────────────────────────────────────────────────

function fmt(n: number, decimals = 0): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(decimals)}K`;
  return `$${n.toFixed(decimals)}`;
}

function fmtNum(n: number): string {
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

// ─── Custom Tooltip ──────────────────────────────────────────────────────────

interface TooltipEntry {
  color?: string;
  name?: string | number;
  value?: string | number;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string | number;
}) {
  if (!active || !payload) return null;
  return (
    <div className="bg-background-elevated border border-cy-row rounded-lg p-3 shadow-lg">
      <p className="font-semibold text-sm mb-1">{label}</p>
      {payload.map((entry, i: number) => (
        <p key={i} className="text-xs" style={{ color: entry.color }}>
          {entry.name}: {typeof entry.value === 'number' && entry.value > 100
            ? fmt(entry.value)
            : entry.value}
        </p>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export default function BusinessPlanPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [assumptions, setAssumptions] = useState<Assumptions>(DEFAULT_ASSUMPTIONS);
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [showAssumptions, setShowAssumptions] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioKey>('realistic');

  // Mount check
  useState(() => { setMounted(true); });

  const updateAssumption = useCallback(<K extends keyof Assumptions>(key: K, value: Assumptions[K]) => {
    setAssumptions(prev => ({ ...prev, [key]: value }));
  }, []);

  // ─── Computed Data ───────────────────────────────────────────────────────

  const projections = useMemo(() => {
    const a = assumptions;
    const years: { year: number; scenarios: Record<ScenarioKey, ScenarioMetrics> }[] = [];

    for (let y = 0; y < a.projectionYears; y++) {
      const year = 2026 + y;

      const scenarios = {} as Record<ScenarioKey, ScenarioMetrics>;
      (['optimistic', 'realistic', 'pessimistic'] as ScenarioKey[]).forEach(scenario => {
        const growthRate = scenario === 'optimistic'
          ? a.annualGrowthOptimistic / 100
          : scenario === 'realistic'
            ? a.annualGrowthRealistic / 100
            : a.annualGrowthPessimistic / 100;

        const initialCustomers = Math.round(a.totalAddressableMarket * (a.initialPenetrationPct / 100));
        const totalCustomers = y === 0
          ? initialCustomers
          : Math.round(initialCustomers * Math.pow(1 + growthRate, y));
        const netCustomers = Math.round(totalCustomers * (1 - a.annualChurnPct / 100));

        const starterCustomers = Math.round(netCustomers * (a.starterMixPct / 100));
        const proCustomers = Math.round(netCustomers * (a.professionalMixPct / 100));
        const entCustomers = netCustomers - starterCustomers - proCustomers;

        const monthlyRecurring =
          starterCustomers * a.starterPrice +
          proCustomers * a.professionalPrice +
          entCustomers * a.enterprisePrice;

        const addOnMonthly = netCustomers * (a.addOnAdoptionPct / 100) * a.avgAddOnRevenue;
        const totalMRR = monthlyRecurring + addOnMonthly;
        const arr = totalMRR * 12;

        // Implementation revenue (only new customers)
        const newCustomers = y === 0 ? netCustomers : Math.max(0, netCustomers - (years[y - 1]?.scenarios?.[scenario]?.netCustomers || 0));
        const implementationRevenue = newCustomers * a.implementationCostPerCustomer;

        // Costs
        const hostingCost = netCustomers * a.monthlyHostingPerCustomer * 12;
        const salaryCost = a.salaryExpenseMonthly * 12 * (1 + y * 0.15); // team grows 15% per year
        const marketingCost = a.marketingBudgetMonthly * 12 * (1 + y * 0.1);
        const supportCost = netCustomers * a.supportCostPerCustomer * 12;
        const totalCosts = hostingCost + salaryCost + marketingCost + supportCost;

        const totalRevenue = arr + implementationRevenue;
        const profit = totalRevenue - totalCosts;
        const margin = totalRevenue > 0 ? (profit / totalRevenue) * 100 : 0;

        scenarios[scenario] = {
          netCustomers,
          starterCustomers,
          proCustomers,
          entCustomers,
          newCustomers,
          mrr: totalMRR,
          arr,
          implementationRevenue,
          totalRevenue,
          hostingCost,
          salaryCost,
          marketingCost,
          supportCost,
          totalCosts,
          profit,
          margin,
          penetration: (netCustomers / a.totalAddressableMarket) * 100,
        };
      });

      years.push({ year, scenarios });
    }
    return years;
  }, [assumptions]);

  // ─── Chart Data ──────────────────────────────────────────────────────────

  const revenueChartData = useMemo(() =>
    projections.map(p => ({
      year: p.year.toString(),
      Optimistic: Math.round(p.scenarios.optimistic.arr),
      Realistic: Math.round(p.scenarios.realistic.arr),
      Pessimistic: Math.round(p.scenarios.pessimistic.arr),
    })), [projections]);

  const customersChartData = useMemo(() =>
    projections.map(p => ({
      year: p.year.toString(),
      Optimistic: p.scenarios.optimistic.netCustomers,
      Realistic: p.scenarios.realistic.netCustomers,
      Pessimistic: p.scenarios.pessimistic.netCustomers,
    })), [projections]);

  const profitChartData = useMemo(() =>
    projections.map(p => ({
      year: p.year.toString(),
      Revenue: Math.round(p.scenarios[selectedScenario].totalRevenue),
      Costs: Math.round(p.scenarios[selectedScenario].totalCosts),
      Profit: Math.round(p.scenarios[selectedScenario].profit),
    })), [projections, selectedScenario]);

  const customerMixData = useMemo(() => {
    const s = projections[projections.length - 1]?.scenarios[selectedScenario];
    if (!s) return [];
    return [
      { name: 'Starter', value: s.starterCustomers, color: COLORS.starter },
      { name: 'Professional', value: s.proCustomers, color: COLORS.professional },
      { name: 'Enterprise', value: s.entCustomers, color: COLORS.enterprise },
    ];
  }, [projections, selectedScenario]);

  const marketSegmentData = useMemo(() =>
    MARKET_SEGMENTS.map(s => ({
      ...s,
      revenue: s.companies * s.avgDeal * 12,
    })), []);

  const radarData = useMemo(() =>
    RADAR_CATEGORIES.map(cat => {
      const row: Record<string, string | number> = { category: cat.label };
      COMPETITORS.forEach(c => {
        row[c.name] = c.features[cat.key];
      });
      return row;
    }), []);

  const costBreakdownData = useMemo(() => {
    const s = projections[projections.length - 1]?.scenarios[selectedScenario];
    if (!s) return [];
    return [
      { name: 'Hosting', value: Math.round(s.hostingCost), color: '#3B82F6' },
      { name: 'Salaries', value: Math.round(s.salaryCost), color: '#EF4444' },
      { name: 'Marketing', value: Math.round(s.marketingCost), color: '#F59E0B' },
      { name: 'Support', value: Math.round(s.supportCost), color: '#8B5CF6' },
    ];
  }, [projections, selectedScenario]);

  const revenueBreakdownOverTime = useMemo(() =>
    projections.map(p => {
      const s = p.scenarios[selectedScenario];
      return {
        year: p.year.toString(),
        Starter: Math.round(s.starterCustomers * assumptions.starterPrice * 12),
        Professional: Math.round(s.proCustomers * assumptions.professionalPrice * 12),
        Enterprise: Math.round(s.entCustomers * assumptions.enterprisePrice * 12),
        'Add-ons': Math.round(s.netCustomers * (assumptions.addOnAdoptionPct / 100) * assumptions.avgAddOnRevenue * 12),
        Implementation: Math.round(s.implementationRevenue),
      };
    }), [projections, selectedScenario, assumptions]);

  // ─── Auth guard ──────────────────────────────────────────────────────────

  if (!mounted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  // ─── Current Scenario Summary ────────────────────────────────────────────

  const currentYear = projections[0]?.scenarios[selectedScenario];
  const finalYear = projections[projections.length - 1]?.scenarios[selectedScenario];

  // ─── Tabs ────────────────────────────────────────────────────────────────

  const tabs: { key: TabKey; label: string; icon: React.ElementType }[] = [
    { key: 'overview', label: 'Overview', icon: BarChart3 },
    { key: 'revenue', label: 'Revenue & Growth', icon: TrendingUp },
    { key: 'market', label: 'Market Analysis', icon: Target },
    { key: 'competitive', label: 'Competitive Edge', icon: Award },
    { key: 'costs', label: 'Costs & P&L', icon: DollarSign },
    { key: 'sla', label: 'SLA & Pricing', icon: Shield },
  ];

  return (
    <AppShell>
      <div className="space-y-6">
        {/* ── Header ────────────────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-[20px] font-[650] tracking-[-0.01em] text-foreground flex items-center gap-2">
              <Briefcase className="w-6 h-6 text-primary" />
              Business Plan — Israel Market
            </h1>
            <p className="text-foreground-muted mt-1">
              Interactive projections for {assumptions.totalAddressableMarket} addressable companies
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* Scenario Selector */}
            <div className="flex bg-background-muted rounded-lg p-1">
              {(['optimistic', 'realistic', 'pessimistic'] as ScenarioKey[]).map(s => (
                <button
                  key={s}
                  onClick={() => setSelectedScenario(s)}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                    selectedScenario === s
                      ? s === 'optimistic' ? 'bg-success text-white' :
                        s === 'realistic' ? 'bg-primary text-white' :
                        'bg-warning text-white'
                      : 'text-foreground-muted hover:text-foreground'
                  }`}
                >
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
            <Button
              variant="ghost"
              onClick={() => setShowAssumptions(!showAssumptions)}
              leftIcon={showAssumptions ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            >
              Assumptions
            </Button>
          </div>
        </div>

        {/* ── Editable Assumptions Panel ────────────────────────────────── */}
        {showAssumptions && (
          <Card className="border-primary/20 bg-primary/5">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-5 h-5 text-primary" />
                Edit Assumptions
              </CardTitle>
              <CardDescription>Change any parameter below — all charts update instantly</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                <div className="col-span-full">
                  <h4 className="text-sm font-bold text-foreground mb-2 border-b border-cy-row pb-1">Market</h4>
                </div>
                <EditableField label="Total Addressable Market" value={assumptions.totalAddressableMarket} onChange={v => updateAssumption('totalAddressableMarket', v)} suffix="companies" />
                <EditableField label="Initial Penetration" value={assumptions.initialPenetrationPct} onChange={v => updateAssumption('initialPenetrationPct', v)} suffix="%" min={0.5} max={50} step={0.5} />
                <EditableField label="Projection Years" value={assumptions.projectionYears} onChange={v => updateAssumption('projectionYears', v)} suffix="years" min={3} max={10} />
                <EditableField label="Annual Churn" value={assumptions.annualChurnPct} onChange={v => updateAssumption('annualChurnPct', v)} suffix="%" min={0} max={50} />

                <div className="col-span-full">
                  <h4 className="text-sm font-bold text-foreground mb-2 border-b border-cy-row pb-1">Growth Rates</h4>
                </div>
                <EditableField label="Optimistic Growth" value={assumptions.annualGrowthOptimistic} onChange={v => updateAssumption('annualGrowthOptimistic', v)} suffix="%" min={5} max={100} />
                <EditableField label="Realistic Growth" value={assumptions.annualGrowthRealistic} onChange={v => updateAssumption('annualGrowthRealistic', v)} suffix="%" min={5} max={100} />
                <EditableField label="Pessimistic Growth" value={assumptions.annualGrowthPessimistic} onChange={v => updateAssumption('annualGrowthPessimistic', v)} suffix="%" min={5} max={100} />

                <div className="col-span-full">
                  <h4 className="text-sm font-bold text-foreground mb-2 border-b border-cy-row pb-1">Pricing (Monthly)</h4>
                </div>
                <EditableField label="Starter" value={assumptions.starterPrice} onChange={v => updateAssumption('starterPrice', v)} prefix="$" />
                <EditableField label="Professional" value={assumptions.professionalPrice} onChange={v => updateAssumption('professionalPrice', v)} prefix="$" />
                <EditableField label="Enterprise" value={assumptions.enterprisePrice} onChange={v => updateAssumption('enterprisePrice', v)} prefix="$" />

                <div className="col-span-full">
                  <h4 className="text-sm font-bold text-foreground mb-2 border-b border-cy-row pb-1">Customer Mix</h4>
                </div>
                <EditableField label="Starter %" value={assumptions.starterMixPct} onChange={v => updateAssumption('starterMixPct', v)} suffix="%" min={0} max={100} />
                <EditableField label="Professional %" value={assumptions.professionalMixPct} onChange={v => updateAssumption('professionalMixPct', v)} suffix="%" min={0} max={100} />
                <EditableField label="Enterprise %" value={assumptions.enterpriseMixPct} onChange={v => updateAssumption('enterpriseMixPct', v)} suffix="%" min={0} max={100} />

                <div className="col-span-full">
                  <h4 className="text-sm font-bold text-foreground mb-2 border-b border-cy-row pb-1">Costs</h4>
                </div>
                <EditableField label="Implementation/Customer" value={assumptions.implementationCostPerCustomer} onChange={v => updateAssumption('implementationCostPerCustomer', v)} prefix="$" />
                <EditableField label="Hosting/Customer/mo" value={assumptions.monthlyHostingPerCustomer} onChange={v => updateAssumption('monthlyHostingPerCustomer', v)} prefix="$" />
                <EditableField label="Salaries (monthly)" value={assumptions.salaryExpenseMonthly} onChange={v => updateAssumption('salaryExpenseMonthly', v)} prefix="$" />
                <EditableField label="Marketing (monthly)" value={assumptions.marketingBudgetMonthly} onChange={v => updateAssumption('marketingBudgetMonthly', v)} prefix="$" />
                <EditableField label="Support/Customer/mo" value={assumptions.supportCostPerCustomer} onChange={v => updateAssumption('supportCostPerCustomer', v)} prefix="$" />

                <div className="col-span-full">
                  <h4 className="text-sm font-bold text-foreground mb-2 border-b border-cy-row pb-1">Add-ons</h4>
                </div>
                <EditableField label="Add-on Adoption" value={assumptions.addOnAdoptionPct} onChange={v => updateAssumption('addOnAdoptionPct', v)} suffix="%" min={0} max={100} />
                <EditableField label="Avg Add-on Revenue" value={assumptions.avgAddOnRevenue} onChange={v => updateAssumption('avgAddOnRevenue', v)} prefix="$" suffix="/mo" />
              </div>

              <div className="mt-4 flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setAssumptions(DEFAULT_ASSUMPTIONS)}
                >
                  Reset to Defaults
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── KPI Strip ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[
            { label: 'Year 1 ARR', value: fmt(currentYear?.arr || 0), icon: DollarSign, color: 'bg-success/10 text-success' },
            { label: `Year ${assumptions.projectionYears} ARR`, value: fmt(finalYear?.arr || 0), icon: TrendingUp, color: 'bg-primary/10 text-primary' },
            { label: 'Year 1 Customers', value: fmtNum(currentYear?.netCustomers || 0), icon: Users, color: 'bg-info/10 text-info' },
            { label: `Year ${assumptions.projectionYears} Customers`, value: fmtNum(finalYear?.netCustomers || 0), icon: Building2, color: 'bg-warning/10 text-warning' },
            { label: `Year ${assumptions.projectionYears} Margin`, value: `${(finalYear?.margin || 0).toFixed(1)}%`, icon: Award, color: finalYear?.margin > 0 ? 'bg-success/10 text-success' : 'bg-error/10 text-error' },
            { label: 'Market Penetration', value: `${(finalYear?.penetration || 0).toFixed(1)}%`, icon: Target, color: 'bg-accent/10 text-accent' },
          ].map((kpi, i) => (
            <Card key={i} padding="md">
              <div className="flex items-center gap-2">
                <div className={`p-2 rounded-lg ${kpi.color}`}>
                  <kpi.icon className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-xs text-foreground-muted">{kpi.label}</p>
                  <p className="text-lg font-bold">{kpi.value}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* ── Tab Navigation ────────────────────────────────────────────── */}
        <div className="flex gap-1 border-b border-cy-row pb-2 overflow-x-auto">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${
                activeTab === key
                  ? 'bg-primary text-white'
                  : 'text-foreground-muted hover:bg-background-muted'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* ── Tab Content ───────────────────────────────────────────────── */}

        {/* OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* 3 Scenario Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <TrendingUp className="w-5 h-5 text-primary" />
                    ARR Projection — 3 Scenarios
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={320}>
                    <AreaChart data={revenueChartData}>
                      <defs>
                        <linearGradient id="gradOpt" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={COLORS.optimistic} stopOpacity={0.3} />
                          <stop offset="95%" stopColor={COLORS.optimistic} stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradReal" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={COLORS.realistic} stopOpacity={0.3} />
                          <stop offset="95%" stopColor={COLORS.realistic} stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradPess" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={COLORS.pessimistic} stopOpacity={0.3} />
                          <stop offset="95%" stopColor={COLORS.pessimistic} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                      <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Area type="monotone" dataKey="Optimistic" stroke={COLORS.optimistic} fill="url(#gradOpt)" strokeWidth={2} />
                      <Area type="monotone" dataKey="Realistic" stroke={COLORS.realistic} fill="url(#gradReal)" strokeWidth={2} />
                      <Area type="monotone" dataKey="Pessimistic" stroke={COLORS.pessimistic} fill="url(#gradPess)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="w-5 h-5 text-primary" />
                    Customer Growth — 3 Scenarios
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={customersChartData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Line type="monotone" dataKey="Optimistic" stroke={COLORS.optimistic} strokeWidth={3} dot={{ r: 5, fill: COLORS.optimistic }} />
                      <Line type="monotone" dataKey="Realistic" stroke={COLORS.realistic} strokeWidth={3} dot={{ r: 5, fill: COLORS.realistic }} />
                      <Line type="monotone" dataKey="Pessimistic" stroke={COLORS.pessimistic} strokeWidth={3} dot={{ r: 5, fill: COLORS.pessimistic }} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Profit/Loss Chart */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <DollarSign className="w-5 h-5 text-primary" />
                    Revenue vs Costs vs Profit ({selectedScenario})
                  </CardTitle>
                  <ScenarioBadge scenario={selectedScenario} />
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <ComposedChart data={profitChartData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                    <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Bar dataKey="Revenue" fill={COLORS.revenue} radius={[4, 4, 0, 0]} opacity={0.8} />
                    <Bar dataKey="Costs" fill={COLORS.costs} radius={[4, 4, 0, 0]} opacity={0.8} />
                    <Line type="monotone" dataKey="Profit" stroke={COLORS.profit} strokeWidth={3} dot={{ r: 5, fill: COLORS.profit }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Scenario Comparison Table */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Year-by-Year Scenario Comparison</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-cy-row">
                      <th className="text-left py-2 px-3 font-semibold">Year</th>
                      <th className="text-right py-2 px-3 font-semibold text-success">Opt. ARR</th>
                      <th className="text-right py-2 px-3 font-semibold text-primary">Real. ARR</th>
                      <th className="text-right py-2 px-3 font-semibold text-warning">Pess. ARR</th>
                      <th className="text-right py-2 px-3 font-semibold text-success">Opt. Customers</th>
                      <th className="text-right py-2 px-3 font-semibold text-primary">Real. Customers</th>
                      <th className="text-right py-2 px-3 font-semibold text-warning">Pess. Customers</th>
                      <th className="text-right py-2 px-3 font-semibold">Real. Margin</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projections.map((p) => (
                      <tr key={p.year} className="border-b border-cy-row/50 hover:bg-background-muted transition-colors">
                        <td className="py-2 px-3 font-semibold">{p.year}</td>
                        <td className="py-2 px-3 text-right text-success">{fmt(p.scenarios.optimistic.arr)}</td>
                        <td className="py-2 px-3 text-right text-primary">{fmt(p.scenarios.realistic.arr)}</td>
                        <td className="py-2 px-3 text-right text-warning">{fmt(p.scenarios.pessimistic.arr)}</td>
                        <td className="py-2 px-3 text-right text-success">{p.scenarios.optimistic.netCustomers}</td>
                        <td className="py-2 px-3 text-right text-primary">{p.scenarios.realistic.netCustomers}</td>
                        <td className="py-2 px-3 text-right text-warning">{p.scenarios.pessimistic.netCustomers}</td>
                        <td className="py-2 px-3 text-right font-semibold">
                          <span className={p.scenarios.realistic.margin > 0 ? 'text-success' : 'text-error'}>
                            {p.scenarios.realistic.margin.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>
        )}

        {/* REVENUE & GROWTH */}
        {activeTab === 'revenue' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue by Tier Over Time */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <BarChart3 className="w-5 h-5 text-primary" />
                    Revenue by Tier ({selectedScenario})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={revenueBreakdownOverTime}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                      <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Bar dataKey="Starter" stackId="a" fill={COLORS.starter} radius={[0, 0, 0, 0]} />
                      <Bar dataKey="Professional" stackId="a" fill={COLORS.professional} />
                      <Bar dataKey="Enterprise" stackId="a" fill={COLORS.enterprise} />
                      <Bar dataKey="Add-ons" stackId="a" fill="#EC4899" />
                      <Bar dataKey="Implementation" stackId="a" fill="#F97316" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Customer Mix Pie */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <PieChartIcon className="w-5 h-5 text-primary" />
                    Customer Mix — Year {assumptions.projectionYears} ({selectedScenario})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={350}>
                    <PieChart>
                      <Pie
                        data={customerMixData}
                        cx="50%"
                        cy="50%"
                        innerRadius={70}
                        outerRadius={120}
                        dataKey="value"
                        label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                      >
                        {customerMixData.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* MRR Growth */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Monthly Recurring Revenue (MRR) Growth</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={projections.map(p => ({
                    year: p.year.toString(),
                    MRR: Math.round(p.scenarios[selectedScenario].mrr),
                  }))}>
                    <defs>
                      <linearGradient id="gradMRR" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                    <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="MRR" stroke="#10B981" fill="url(#gradMRR)" strokeWidth={3} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Key Revenue Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {projections.slice(0, 3).map((p) => {
                const s = p.scenarios[selectedScenario];
                return (
                  <Card key={p.year} padding="lg" className="bg-gradient-to-br from-primary/5 to-transparent">
                    <h3 className="text-lg font-bold mb-3">{p.year}</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-foreground-muted">ARR</span>
                        <span className="font-bold text-success">{fmt(s.arr)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-foreground-muted">MRR</span>
                        <span className="font-semibold">{fmt(s.mrr)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-foreground-muted">Customers</span>
                        <span className="font-semibold">{s.netCustomers}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-foreground-muted">Avg Revenue/Customer</span>
                        <span className="font-semibold">{fmt(s.netCustomers > 0 ? s.mrr / s.netCustomers : 0)}/mo</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-foreground-muted">Implementation</span>
                        <span className="font-semibold">{fmt(s.implementationRevenue)}</span>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* MARKET ANALYSIS */}
        {activeTab === 'market' && (
          <div className="space-y-6">
            {/* Market Context */}
            <Card className="bg-gradient-to-r from-primary/10 via-secondary/5 to-accent/5 border-primary/20">
              <CardContent className="py-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-primary/20">
                    <Globe className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold mb-2">Israeli Carbon Reporting Market</h3>
                    <p className="text-sm text-foreground-muted leading-relaxed">
                      Israel&apos;s Climate Law (2022) and EU CBAM (2026 full enforcement) create mandatory reporting requirements
                      for ~500 companies. Israeli exporters to the EU face CBAM surcharges, manufacturers must report under
                      ISO 14064-1, and the TASE (Tel Aviv Stock Exchange) requires ESG disclosure for listed companies.
                      The market is underserved by local solutions — most competitors are US/EU platforms with no Hebrew support
                      or Israeli regulation alignment.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Market Segments */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Addressable Market by Segment</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={380}>
                    <BarChart data={marketSegmentData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis type="number" tick={{ fontSize: 11 }} />
                      <YAxis dataKey="segment" type="category" width={150} tick={{ fontSize: 11 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="companies" name="Companies" radius={[0, 4, 4, 0]}>
                        {marketSegmentData.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Revenue Potential by Segment */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Annual Revenue Potential by Segment</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={380}>
                    <PieChart>
                      <Pie
                        data={marketSegmentData}
                        cx="50%"
                        cy="50%"
                        outerRadius={130}
                        dataKey="revenue"
                        label={({ name, percent }: { name?: string | number; percent?: number }) => `${String(name).split(' ')[0]}: ${((percent || 0) * 100).toFixed(0)}%`}
                      >
                        {marketSegmentData.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v) => fmt(Number(v))} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Market Penetration Over Time */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Market Penetration % Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={projections.map(p => ({
                    year: p.year.toString(),
                    Optimistic: parseFloat(p.scenarios.optimistic.penetration.toFixed(1)),
                    Realistic: parseFloat(p.scenarios.realistic.penetration.toFixed(1)),
                    Pessimistic: parseFloat(p.scenarios.pessimistic.penetration.toFixed(1)),
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                    <YAxis unit="%" tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Area type="monotone" dataKey="Optimistic" stroke={COLORS.optimistic} fill={COLORS.optimistic} fillOpacity={0.15} strokeWidth={2} />
                    <Area type="monotone" dataKey="Realistic" stroke={COLORS.realistic} fill={COLORS.realistic} fillOpacity={0.15} strokeWidth={2} />
                    <Area type="monotone" dataKey="Pessimistic" stroke={COLORS.pessimistic} fill={COLORS.pessimistic} fillOpacity={0.15} strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Segment Details Table */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Market Segments Detail</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-cy-row">
                      <th className="text-left py-2 px-3">Segment</th>
                      <th className="text-right py-2 px-3">Companies</th>
                      <th className="text-right py-2 px-3">Avg Monthly Deal</th>
                      <th className="text-right py-2 px-3">Annual Revenue Potential</th>
                      <th className="text-right py-2 px-3">% of TAM</th>
                    </tr>
                  </thead>
                  <tbody>
                    {marketSegmentData.map((s) => (
                      <tr key={s.segment} className="border-b border-cy-row/50 hover:bg-background-muted">
                        <td className="py-2 px-3 font-medium flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: s.color }} />
                          {s.segment}
                        </td>
                        <td className="py-2 px-3 text-right">{s.companies}</td>
                        <td className="py-2 px-3 text-right">${s.avgDeal.toLocaleString()}</td>
                        <td className="py-2 px-3 text-right font-semibold">{fmt(s.revenue)}</td>
                        <td className="py-2 px-3 text-right">{((s.companies / assumptions.totalAddressableMarket) * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                    <tr className="font-bold border-t-2 border-cy-row">
                      <td className="py-2 px-3">Total</td>
                      <td className="py-2 px-3 text-right">{MARKET_SEGMENTS.reduce((a, s) => a + s.companies, 0)}</td>
                      <td className="py-2 px-3 text-right">—</td>
                      <td className="py-2 px-3 text-right">{fmt(marketSegmentData.reduce((a, s) => a + s.revenue, 0))}</td>
                      <td className="py-2 px-3 text-right">100%</td>
                    </tr>
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>
        )}

        {/* COMPETITIVE EDGE */}
        {activeTab === 'competitive' && (
          <div className="space-y-6">
            {/* Radar Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Award className="w-5 h-5 text-primary" />
                  Feature Comparison Radar
                </CardTitle>
                <CardDescription>CLIMATRIX vs top 4 international competitors (0–100 score)</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={450}>
                  <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                    <PolarGrid strokeDasharray="3 3" opacity={0.3} />
                    <PolarAngleAxis dataKey="category" tick={{ fontSize: 11, fill: 'var(--foreground-muted)' }} />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                    {COMPETITORS.map((c, i) => (
                      <Radar
                        key={c.name}
                        name={c.name}
                        dataKey={c.name}
                        stroke={COLORS.pie[i]}
                        fill={COLORS.pie[i]}
                        fillOpacity={c.isUs ? 0.3 : 0.05}
                        strokeWidth={c.isUs ? 3 : 1.5}
                      />
                    ))}
                    <Legend />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Market Fit Comparison */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Israeli Market Fit Score</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={COMPETITORS.map(c => ({ name: c.name, 'Market Fit': c.marketFit }))}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="Market Fit" radius={[6, 6, 0, 0]}>
                      {COMPETITORS.map((c, i) => (
                        <Cell key={i} fill={c.isUs ? '#3B82F6' : '#94A3B8'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Competitor Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {COMPETITORS.map((c) => (
                <Card
                  key={c.name}
                  padding="lg"
                  className={c.isUs ? 'border-primary/30 bg-primary/5 ring-2 ring-primary/20' : ''}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-lg">{c.name}</h3>
                    {c.isUs && (
                      <span className="px-2 py-0.5 bg-primary text-white text-xs rounded-full font-semibold">
                        Us
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-foreground-muted mb-3">Pricing: {c.pricing}</p>

                  <div className="mb-3">
                    <p className="text-xs font-semibold text-success mb-1 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Strengths
                    </p>
                    <ul className="space-y-1">
                      {c.strengths.map((s, i) => (
                        <li key={i} className="text-xs text-foreground-muted flex items-start gap-1">
                          <span className="text-success mt-0.5">+</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <p className="text-xs font-semibold text-error mb-1 flex items-center gap-1">
                      <XCircle className="w-3 h-3" /> Weaknesses
                    </p>
                    <ul className="space-y-1">
                      {c.weaknesses.map((w, i) => (
                        <li key={i} className="text-xs text-foreground-muted flex items-start gap-1">
                          <span className="text-error mt-0.5">−</span> {w}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Fit Bar */}
                  <div className="mt-3 pt-3 border-t border-cy-row">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-foreground-muted">IL Market Fit</span>
                      <span className="text-xs font-bold">{c.marketFit}%</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-background-muted overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${c.marketFit}%`,
                          backgroundColor: c.isUs ? '#3B82F6' : c.marketFit > 50 ? '#F59E0B' : '#94A3B8',
                        }}
                      />
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* CLIMATRIX Unique Advantages */}
            <Card className="bg-gradient-to-r from-primary/10 to-secondary/10 border-primary/20">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Zap className="w-5 h-5 text-primary" />
                  CLIMATRIX Competitive Moat
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { title: 'Hebrew-First Platform', desc: 'Only carbon platform with native Hebrew UI, support, and documentation. Israeli companies get local onboarding.' },
                    { title: 'Israeli Regulation Aligned', desc: 'Built for Israel Climate Law, TASE ESG requirements, and MoEP reporting standards from day one.' },
                    { title: 'EU CBAM Built-In', desc: 'Critical for Israeli exporters — embedded CBAM compliance with quarterly report generation and certificate tracking.' },
                    { title: 'AI-Powered Data Import', desc: 'Proprietary AI extraction from invoices, utility bills, and spreadsheets — 10x faster than manual entry.' },
                    { title: 'Fast Implementation', desc: '2-week avg go-live vs 2-3 months for enterprise competitors. Lower implementation cost = faster ROI.' },
                    { title: 'Competitive Pricing', desc: '40-60% cheaper than Watershed/Persefoni for equivalent features. Made for Israeli SMB-to-midmarket budgets.' },
                  ].map((item, i) => (
                    <div key={i} className="p-4 rounded-xl bg-background/80 border border-cy-row/50">
                      <h4 className="font-semibold text-sm mb-1">{item.title}</h4>
                      <p className="text-xs text-foreground-muted leading-relaxed">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* COSTS & P&L */}
        {activeTab === 'costs' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Cost Breakdown Pie */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Cost Breakdown — Year {assumptions.projectionYears} ({selectedScenario})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={350}>
                    <PieChart>
                      <Pie
                        data={costBreakdownData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        dataKey="value"
                        label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                      >
                        {costBreakdownData.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v) => fmt(Number(v))} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Margin Over Time */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Profit Margin % Over Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={350}>
                    <AreaChart data={projections.map(p => ({
                      year: p.year.toString(),
                      Optimistic: parseFloat(p.scenarios.optimistic.margin.toFixed(1)),
                      Realistic: parseFloat(p.scenarios.realistic.margin.toFixed(1)),
                      Pessimistic: parseFloat(p.scenarios.pessimistic.margin.toFixed(1)),
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                      <YAxis unit="%" tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Legend />
                      <Area type="monotone" dataKey="Optimistic" stroke={COLORS.optimistic} fill={COLORS.optimistic} fillOpacity={0.1} strokeWidth={2} />
                      <Area type="monotone" dataKey="Realistic" stroke={COLORS.realistic} fill={COLORS.realistic} fillOpacity={0.1} strokeWidth={2} />
                      <Area type="monotone" dataKey="Pessimistic" stroke={COLORS.pessimistic} fill={COLORS.pessimistic} fillOpacity={0.1} strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Costs Over Time Stacked */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Cost Structure Over Time ({selectedScenario})</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={projections.map(p => {
                    const s = p.scenarios[selectedScenario];
                    return {
                      year: p.year.toString(),
                      Hosting: Math.round(s.hostingCost),
                      Salaries: Math.round(s.salaryCost),
                      Marketing: Math.round(s.marketingCost),
                      Support: Math.round(s.supportCost),
                    };
                  })}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                    <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Bar dataKey="Hosting" stackId="a" fill="#3B82F6" />
                    <Bar dataKey="Salaries" stackId="a" fill="#EF4444" />
                    <Bar dataKey="Marketing" stackId="a" fill="#F59E0B" />
                    <Bar dataKey="Support" stackId="a" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Detailed P&L Table */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Profit & Loss — {selectedScenario.charAt(0).toUpperCase() + selectedScenario.slice(1)} Scenario</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-cy-row">
                      <th className="text-left py-2 px-3">Line Item</th>
                      {projections.map(p => (
                        <th key={p.year} className="text-right py-2 px-3">{p.year}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: 'Subscription Revenue (ARR)', key: 'arr', bold: false, color: '' },
                      { label: 'Implementation Revenue', key: 'implementationRevenue', bold: false, color: '' },
                      { label: 'Total Revenue', key: 'totalRevenue', bold: true, color: 'text-success' },
                      { label: '─ Hosting', key: 'hostingCost', bold: false, color: 'text-error' },
                      { label: '─ Salaries', key: 'salaryCost', bold: false, color: 'text-error' },
                      { label: '─ Marketing', key: 'marketingCost', bold: false, color: 'text-error' },
                      { label: '─ Support', key: 'supportCost', bold: false, color: 'text-error' },
                      { label: 'Total Costs', key: 'totalCosts', bold: true, color: 'text-error' },
                      { label: 'Net Profit', key: 'profit', bold: true, color: '' },
                    ].map((row) => (
                      <tr key={row.label} className={`border-b border-cy-row/50 ${row.bold ? 'bg-background-muted/50' : ''}`}>
                        <td className={`py-2 px-3 ${row.bold ? 'font-bold' : ''}`}>{row.label}</td>
                        {projections.map(p => {
                          const val = p.scenarios[selectedScenario][row.key as keyof ScenarioMetrics];
                          return (
                            <td key={p.year} className={`py-2 px-3 text-right ${row.bold ? 'font-bold' : ''} ${
                              row.key === 'profit' ? (val > 0 ? 'text-success' : 'text-error') : row.color
                            }`}>
                              {fmt(Math.round(val))}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                    <tr className="border-t-2 border-cy-row font-bold">
                      <td className="py-2 px-3">Margin %</td>
                      {projections.map(p => {
                        const m = p.scenarios[selectedScenario].margin;
                        return (
                          <td key={p.year} className={`py-2 px-3 text-right ${m > 0 ? 'text-success' : 'text-error'}`}>
                            {m.toFixed(1)}%
                          </td>
                        );
                      })}
                    </tr>
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>
        )}

        {/* SLA & PRICING */}
        {activeTab === 'sla' && (
          <div className="space-y-6">
            {/* Pricing Tiers Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                {
                  name: 'Starter',
                  price: assumptions.starterPrice,
                  color: 'from-purple-500/10 to-purple-500/5',
                  border: 'border-purple-500/20',
                  badge: 'bg-purple-500',
                  users: 3,
                  sites: 5,
                  sla: '99.5%',
                  response: '48h',
                  features: ['Scope 1 & 2', '200+ emission factors', 'Basic dashboard', 'PDF export', 'Email support'],
                  implementation: '$3,000',
                  maintenance: '$50/mo',
                },
                {
                  name: 'Professional',
                  price: assumptions.professionalPrice,
                  color: 'from-blue-500/10 to-blue-500/5',
                  border: 'border-info',
                  badge: 'bg-cy-scope3',
                  popular: true,
                  users: 10,
                  sites: 25,
                  sla: '99.9%',
                  response: '24h',
                  features: ['All scopes (15 categories)', 'AI data import', 'ISO 14064-1 reports', 'CDP export', 'SBTi targets', 'CBAM compliance', 'Priority support'],
                  implementation: '$5,000',
                  maintenance: '$100/mo',
                },
                {
                  name: 'Enterprise',
                  price: assumptions.enterprisePrice,
                  color: 'from-emerald-500/10 to-emerald-500/5',
                  border: 'border-cy-accent',
                  badge: 'bg-cy-accent',
                  users: -1,
                  sites: -1,
                  sla: '99.95%',
                  response: '4h',
                  features: ['Everything in Pro', 'Custom factors', 'CSRD/ESRS E1', 'Unlimited scenarios', 'Auditor portal', 'SSO/SAML', 'Full API', 'Dedicated AM'],
                  implementation: '$10,000+',
                  maintenance: '$200/mo',
                },
              ].map((tier) => (
                <Card
                  key={tier.name}
                  padding="lg"
                  className={`bg-gradient-to-b ${tier.color} ${tier.border} relative ${tier.popular ? 'ring-2 ring-info' : ''}`}
                >
                  {tier.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-3 py-1 bg-cy-scope3 text-white text-xs font-bold rounded-full">
                        Most Popular
                      </span>
                    </div>
                  )}
                  <div className="text-center mb-4">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-white text-xs font-bold ${tier.badge} mb-2`}>
                      {tier.name}
                    </span>
                    <div className="text-3xl font-bold">
                      ${tier.price.toLocaleString()}
                      <span className="text-sm font-normal text-foreground-muted">/mo</span>
                    </div>
                  </div>

                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between py-1 border-b border-cy-row/50">
                      <span className="text-foreground-muted">Users</span>
                      <span className="font-semibold">{tier.users === -1 ? 'Unlimited' : tier.users}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-cy-row/50">
                      <span className="text-foreground-muted">Sites</span>
                      <span className="font-semibold">{tier.sites === -1 ? 'Unlimited' : `Up to ${tier.sites}`}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-cy-row/50">
                      <span className="text-foreground-muted">SLA Uptime</span>
                      <span className="font-semibold text-success">{tier.sla}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-cy-row/50">
                      <span className="text-foreground-muted">Response Time</span>
                      <span className="font-semibold">{tier.response}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-cy-row/50">
                      <span className="text-foreground-muted">Implementation</span>
                      <span className="font-semibold">{tier.implementation}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-cy-row/50">
                      <span className="text-foreground-muted">Maintenance</span>
                      <span className="font-semibold">{tier.maintenance}</span>
                    </div>

                    <div className="pt-2">
                      <p className="text-xs font-semibold mb-2">Features:</p>
                      <ul className="space-y-1">
                        {tier.features.map((f, i) => (
                          <li key={i} className="text-xs text-foreground-muted flex items-center gap-1.5">
                            <CheckCircle2 className="w-3 h-3 text-success flex-shrink-0" />
                            {f}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* SLA Guarantees */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="w-5 h-5 text-primary" />
                  SLA Guarantees by Tier
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-cy-row">
                        <th className="text-left py-3 px-4">SLA Component</th>
                        <th className="text-center py-3 px-4 text-purple-500">Starter</th>
                        <th className="text-center py-3 px-4 text-info">Professional</th>
                        <th className="text-center py-3 px-4 text-cy-accent">Enterprise</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { item: 'Uptime Guarantee', starter: '99.5%', pro: '99.9%', ent: '99.95%' },
                        { item: 'Max Downtime/Month', starter: '3.6 hours', pro: '43 min', ent: '22 min' },
                        { item: 'Support Response', starter: '48 hours', pro: '24 hours', ent: '4 hours' },
                        { item: 'Critical Bug Fix', starter: '72 hours', pro: '24 hours', ent: '8 hours' },
                        { item: 'Data Backup', starter: 'Daily', pro: 'Hourly', ent: 'Real-time' },
                        { item: 'Disaster Recovery', starter: '24h RPO', pro: '4h RPO', ent: '1h RPO' },
                        { item: 'Dedicated CSM', starter: '—', pro: '—', ent: 'Yes' },
                        { item: 'Custom Integrations', starter: '—', pro: 'API access', ent: 'Full + dedicated' },
                        { item: 'Penalty (SLA breach)', starter: '—', pro: '5% credit', ent: '10% credit' },
                      ].map((row) => (
                        <tr key={row.item} className="border-b border-cy-row/50 hover:bg-background-muted">
                          <td className="py-2 px-4 font-medium">{row.item}</td>
                          <td className="py-2 px-4 text-center">{row.starter}</td>
                          <td className="py-2 px-4 text-center">{row.pro}</td>
                          <td className="py-2 px-4 text-center font-semibold">{row.ent}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Implementation Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Implementation Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col md:flex-row gap-4">
                  {[
                    { phase: 'Week 1', title: 'Setup & Config', items: ['Account provisioning', 'Organization setup', 'Site creation', 'User onboarding'], color: '#3B82F6' },
                    { phase: 'Week 2', title: 'Data Import', items: ['Historical data upload', 'AI extraction training', 'Emission factor mapping', 'Validation & QA'], color: '#10B981' },
                    { phase: 'Week 3', title: 'Reporting', items: ['Dashboard configuration', 'Report templates', 'Export setup (CDP, ISO)', 'Staff training'], color: '#F59E0B' },
                    { phase: 'Week 4', title: 'Go-Live', items: ['Final review', 'Production deployment', 'Handover & documentation', 'Ongoing support begins'], color: '#8B5CF6' },
                  ].map((phase, i) => (
                    <div key={i} className="flex-1 relative">
                      <div className="p-4 rounded-xl border-0 bg-cy-row-muted/50">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold" style={{ backgroundColor: phase.color }}>
                            {i + 1}
                          </div>
                          <div>
                            <p className="text-xs font-semibold" style={{ color: phase.color }}>{phase.phase}</p>
                            <p className="text-sm font-bold">{phase.title}</p>
                          </div>
                        </div>
                        <ul className="space-y-1 ml-10">
                          {phase.items.map((item, j) => (
                            <li key={j} className="text-xs text-foreground-muted flex items-center gap-1">
                              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: phase.color }} />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                      {i < 3 && (
                        <div className="hidden md:block absolute top-1/2 -right-2.5 w-5 h-0.5 bg-border" />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </AppShell>
  );
}
