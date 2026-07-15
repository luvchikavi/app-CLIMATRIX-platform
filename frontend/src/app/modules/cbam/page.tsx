'use client';

import { useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout';
import {
  CBAMDashboard,
  CBAMInstallations,
  CBAMImports,
  CBAMReports,
  CBAMCalculator,
  CBAMAnnualDeclaration,
  CBAMSuppliers,
  CBAMCertificates,
} from '@/components/cbam';
type CBAMView =
  | 'dashboard'
  | 'installations'
  | 'imports'
  | 'suppliers'
  | 'declaration'
  | 'certificates'
  | 'reports'
  | 'calculator';

const NAV_ITEMS: { id: CBAMView; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'installations', label: 'Installations' },
  { id: 'imports', label: 'Imports register' },
  { id: 'suppliers', label: 'Suppliers' },
  { id: 'declaration', label: 'Annual declaration' },
  { id: 'certificates', label: 'Certificates' },
  { id: 'reports', label: 'Quarterly history' },
  { id: 'calculator', label: 'Calculator' },
];

export default function CBAMModulePage() {
  const [currentView, setCurrentView] = useState<CBAMView>('dashboard');

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <CBAMDashboard onNavigate={setCurrentView} />;
      case 'installations':
        return <CBAMInstallations />;
      case 'imports':
        return <CBAMImports />;
      case 'suppliers':
        return <CBAMSuppliers />;
      case 'declaration':
        return <CBAMAnnualDeclaration />;
      case 'certificates':
        return <CBAMCertificates />;
      case 'reports':
        return <CBAMReports />;
      case 'calculator':
        return <CBAMCalculator />;
      default:
        return <CBAMDashboard onNavigate={setCurrentView} />;
    }
  };

  return (
    <AppShell>
      {/* Beta notice — a quiet line, not a box */}
      <div className="mb-4 flex items-center gap-2 text-[12.5px] text-cy-muted">
        <span className="shrink-0 rounded-full bg-cy-warn-soft px-2 py-0.5 text-[11px] font-bold text-cy-warn">
          Beta
        </span>
        Preview-quality for exploration — not yet for official regulatory filing.
      </div>

      {/* Header + sub-navigation */}
      <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[20px] font-[650] tracking-[-0.01em] text-cy-ink">CBAM</h1>
          <p className="mt-[3px] text-[13px] text-cy-muted">Carbon Border Adjustment Mechanism</p>
        </div>

        <nav className="flex flex-wrap items-center gap-1.5">
          {NAV_ITEMS.map((item) => {
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`cursor-pointer rounded-full px-3.5 py-[7px] text-[12.5px] font-semibold transition-colors ${
                  isActive
                    ? 'bg-cy-accent-soft text-cy-accent'
                    : 'text-cy-muted hover:bg-cy-row hover:text-cy-ink'
                }`}
              >
                {item.label}
              </button>
            );
          })}
          <span aria-hidden="true" className="mx-1.5 h-5 w-px shrink-0 bg-cy-row" />
          <Link
            href="/cbam-check"
            className="rounded-full px-3.5 py-[7px] text-[12.5px] font-semibold text-cy-warn/70 transition-colors hover:bg-cy-warn-soft/50 hover:text-cy-warn"
          >
            Exemption checker ↗
          </Link>
        </nav>
      </div>

      {/* Main content */}
      {renderView()}

      {/* Footer info */}
      <div className="mt-8 text-[11.5px] text-cy-faint">
        EU Regulation 2023/956 · Transitional Phase 2024–2025 · Definitive Phase 2026+ · Covered
        sectors: Cement, Iron &amp; Steel, Aluminium, Fertilisers, Electricity, Hydrogen
      </div>
    </AppShell>
  );
}
