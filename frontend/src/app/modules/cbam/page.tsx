'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/stores/auth';
import { LockedModule } from '@/components/modules/LockedModule';
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
  ArrowLeft,
  Scale,
} from 'lucide-react';

type CBAMView = 'dashboard' | 'installations' | 'imports' | 'reports' | 'calculator';

const PLAN_LEVELS: Record<string, number> = {
  free: 0,
  starter: 1,
  professional: 2,
  enterprise: 3,
};

const NAV_ITEMS: { id: CBAMView; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'installations', label: 'Installations', icon: Factory },
  { id: 'imports', label: 'Imports', icon: Package },
  { id: 'reports', label: 'Reports', icon: FileText },
  { id: 'calculator', label: 'Calculator', icon: Calculator },
];

export default function CBAMModulePage() {
  const [currentView, setCurrentView] = useState<CBAMView>('dashboard');
  const { organization } = useAuthStore();
  const currentPlan = organization?.subscription_plan || 'free';
  const isLocked = (PLAN_LEVELS[currentPlan] ?? 0) < PLAN_LEVELS['professional'];

  if (isLocked) {
    return (
      <LockedModule
        moduleName="CBAM"
        description="Carbon Border Adjustment Mechanism - EU carbon compliance for importers."
        icon={Scale}
        color="bg-blue-600"
        features={[
          'Embedded Emissions Calculation',
          'Supplier Data Collection',
          'CBAM Compliance Reports',
          'EU Regulatory Compliance',
          'Certificate Management',
        ]}
        requiredPlan="Professional"
        price="$149/mo"
      />
    );
  }

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
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <div className="bg-background-elevated border-b border-border sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo/Title */}
            <div className="flex items-center gap-4">
              <a href="/dashboard" className="flex items-center gap-2 text-foreground-muted hover:text-foreground">
                <ArrowLeft className="w-4 h-4" />
                <span className="text-sm">Back</span>
              </a>
              <div className="h-6 w-px bg-border" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">CB</span>
                </div>
                <div>
                  <h1 className="font-semibold text-foreground">CBAM Module</h1>
                  <p className="text-xs text-foreground-muted">Carbon Border Adjustment</p>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="flex items-center gap-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const isActive = currentView === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentView(item.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
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
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderView()}
      </main>

      {/* Footer Info */}
      <footer className="border-t border-border bg-background-muted mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between text-xs text-foreground-muted">
            <div className="flex items-center gap-4">
              <span>EU Regulation 2023/956</span>
              <span>|</span>
              <span>Transitional Phase: 2024-2025</span>
              <span>|</span>
              <span>Definitive Phase: 2026+</span>
            </div>
            <div>
              <span>Covered Sectors: Cement, Iron & Steel, Aluminium, Fertilisers, Electricity, Hydrogen</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
