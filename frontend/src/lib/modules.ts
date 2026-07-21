/**
 * Single source of truth for CLIMATRIX modules — status, badges, and gating.
 * Consumed by the Sidebar and the /modules catalog so they can never disagree.
 *
 * No pricing / "locked" tier for the pilot: every module is Active, Beta, or Coming Soon.
 */
import {
  Target,
  Scale,
  Coins,
  Microscope,
  FileStack,
  Building2,
  Package,
  type LucideIcon,
} from 'lucide-react';

export type ModuleStatus = 'active' | 'beta' | 'coming-soon';

export interface ModuleDef {
  id: string;
  name: string;
  href: string;
  icon: LucideIcon;
  status: ModuleStatus;
  blurb: string;
  features: string[];
}

export const MODULE_REGISTRY: ModuleDef[] = [
  {
    id: 'ccf',
    name: 'CCF',
    href: '/reports',
    icon: Building2,
    status: 'active',
    blurb: 'Corporate Carbon Footprint — full Scope 1-3 inventory per GHG Protocol & ISO 14064-1.',
    features: ['Scopes 1-3', 'ISO 14064-1 report', 'Scope-3 screening', 'VSME / ESRS / CDP exports', 'Verifier portal'],
  },
  {
    id: 'decarbonization',
    name: 'Decarbonization',
    href: '/decarbonization',
    icon: Target,
    status: 'beta',
    blurb: 'SBTi-aligned targets, initiatives and scenarios to plan your path to net zero.',
    features: ['SBTi targets', 'Initiative library', 'Scenario modeling', 'Progress tracking'],
  },
  {
    id: 'cbam',
    name: 'CBAM',
    href: '/modules/cbam',
    icon: Scale,
    status: 'beta',
    blurb: 'EU Carbon Border Adjustment Mechanism — embedded emissions & reporting.',
    features: ['50t exemption checker', 'Embedded emissions', 'CN-code classification', 'Quarterly reports', 'EU ETS pricing'],
  },
  {
    id: 'pcaf',
    name: 'PCAF',
    href: '/modules/pcaf',
    icon: Coins,
    status: 'coming-soon',
    blurb: 'Financed emissions for banks, insurers & asset managers.',
    features: ['Asset-class attribution', 'Portfolio footprint', 'PCAF data quality', 'TCFD-aligned'],
  },
  {
    id: 'pcf',
    name: 'PCF',
    href: '/products',
    icon: Package,
    status: 'beta',
    blurb: 'Product Carbon Footprint per ISO 14067 with PACT-conformant data exchange.',
    features: ['Cradle-to-gate per product', 'BOM modeling', 'PACT v3 exchange format', 'Supplier PCF ingestion', 'Primary-data share'],
  },
  {
    id: 'lca',
    name: 'LCA',
    href: '/modules/lca',
    icon: Microscope,
    status: 'coming-soon',
    blurb: 'Streamlined life-cycle assessment on the EF 3.1 impact method.',
    features: ['ISO 14040/44', 'EF 3.1 impact categories', 'Lifecycle modules A1-D', 'Feeds EPD generation'],
  },
  {
    id: 'epd',
    name: 'EPD',
    href: '/modules/epd',
    icon: FileStack,
    status: 'coming-soon',
    blurb: 'EN 15804+A2 Environmental Product Declarations, verification-ready.',
    features: ['EN 15804+A2 results matrix', 'Digital EPD (ILCD+EPD)', 'Verification workflow', 'Program-operator submission'],
  },
];

export const STATUS_META: Record<
  ModuleStatus,
  { label: string; className: string }
> = {
  active: { label: 'Active', className: 'bg-success/10 text-success border border-success/20' },
  beta: { label: 'Beta', className: 'bg-primary/10 text-primary border border-primary/20' },
  'coming-soon': { label: 'Soon', className: 'bg-muted text-foreground-muted border border-border' },
};

/** Active + Beta modules are enterable; Coming Soon are not. */
export const isEnterable = (s: ModuleStatus): boolean => s === 'active' || s === 'beta';

export function getModule(id: string): ModuleDef | undefined {
  return MODULE_REGISTRY.find((m) => m.id === id);
}

/**
 * "Find the right service": rank modules for an org with a light heuristic
 * on industry / region. (GHG inventory itself is core, not a module —
 * it lives in Data Hub / Reports.)
 */
export function recommendedModules(org?: {
  industry_code?: string | null;
  default_region?: string;
}): ModuleDef[] {
  const industry = (org?.industry_code || '').toLowerCase();
  const region = (org?.default_region || '').toLowerCase();
  const score = (m: ModuleDef): number => {
    if (m.id === 'ccf') return 95; // measuring is where everyone starts
    if (m.id === 'decarbonization') return 90; // the natural next step after measuring
    if (m.id === 'cbam' && (industry.includes('manufactur') || industry.includes('steel') || industry.includes('cement') || region === 'eu' || region === 'il')) return 80;
    if (m.id === 'pcaf' && (industry.includes('financ') || industry.includes('bank') || industry.includes('insur'))) return 70;
    if ((m.id === 'pcf' || m.id === 'lca' || m.id === 'epd') && industry.includes('manufactur')) return 60;
    if (m.status === 'active' || m.status === 'beta') return 40;
    return 20;
  };
  return [...MODULE_REGISTRY].sort((a, b) => score(b) - score(a)).slice(0, 3);
}
