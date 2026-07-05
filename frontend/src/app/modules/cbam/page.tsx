'use client';

import { useState } from 'react';
import { AppShell } from '@/components/layout';
import {
  CBAMDashboard,
  CBAMInstallations,
  CBAMImports,
  CBAMReports,
  CBAMCalculator,
} from '@/components/cbam';
import {
  LayoutDashboard,
  Factory,
  Package,
  FileText,
  Calculator,
  Scale,
} from 'lucide-react';

type CBAMView = 'dashboard' | 'installations' | 'imports' | 'reports' | 'calculator';

const NAV_ITEMS: { id: CBAMView; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'installations', label: 'Installations', icon: Factory },
  { id: 'imports', label: 'Imports', icon: Package },
  { id: 'reports', label: 'Reports', icon: FileText },
  { id: 'calculator', label: 'Calculator', icon: Calculator },
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
      {/* Beta banner */}
      <div className="mb-6 rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 flex items-center gap-3 text-sm">
        <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-primary/15 text-primary shrink-0">
          Beta
        </span>
        <span className="text-foreground-muted">
          CBAM is in beta — preview-quality for exploration, not yet for official regulatory filing.
        </span>
      </div>

      {/* Header + sub-navigation */}
      <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
            <Scale className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">CBAM</h1>
            <p className="text-sm text-foreground-muted">Carbon Border Adjustment Mechanism</p>
          </div>
        </div>

        <nav className="flex items-center gap-1 flex-wrap">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary text-white'
                    : 'text-foreground-muted hover:text-foreground hover:bg-background-muted'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main content */}
      {renderView()}

      {/* Footer info */}
      <div className="mt-8 border-t border-border pt-4 text-xs text-foreground-muted">
        EU Regulation 2023/956 · Transitional Phase 2024–2025 · Definitive Phase 2026+ · Covered
        sectors: Cement, Iron &amp; Steel, Aluminium, Fertilisers, Electricity, Hydrogen
      </div>
    </AppShell>
  );
}
