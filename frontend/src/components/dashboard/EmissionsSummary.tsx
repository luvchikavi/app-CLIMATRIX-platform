'use client';

import { ReportSummary } from '@/lib/api';
import { Flame, Zap, Globe, TrendingUp } from 'lucide-react';

interface EmissionsSummaryProps {
  data: ReportSummary;
}

export function EmissionsSummary({ data }: EmissionsSummaryProps) {
  const cards = [
    {
      title: 'Total Emissions',
      value: data.total_co2e_tonnes,
      unit: 'tonnes CO2e',
      icon: TrendingUp,
      color: 'bg-gray-900',
      textColor: 'text-white',
    },
    {
      title: 'Scope 1',
      subtitle: 'Direct',
      value: data.scope_1_co2e_kg / 1000,
      unit: 'tonnes CO2e',
      icon: Flame,
      color: 'bg-red-100',
      textColor: 'text-red-700',
      iconColor: 'text-red-500',
    },
    {
      title: 'Scope 2',
      subtitle: 'Energy',
      value: data.scope_2_co2e_kg / 1000,
      unit: 'tonnes CO2e',
      icon: Zap,
      color: 'bg-yellow-100',
      textColor: 'text-yellow-700',
      iconColor: 'text-yellow-500',
    },
    {
      title: 'Scope 3',
      subtitle: 'Value Chain',
      value: data.scope_3_co2e_kg / 1000,
      unit: 'tonnes CO2e',
      icon: Globe,
      color: 'bg-blue-100',
      textColor: 'text-blue-700',
      iconColor: 'text-blue-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.title}
            className={`${card.color} rounded-xl p-6 ${card.title === 'Total Emissions' ? 'md:col-span-2 lg:col-span-1' : ''}`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className={`text-sm font-medium ${card.textColor} opacity-70`}>
                  {card.title}
                </p>
                {card.subtitle && (
                  <p className={`text-xs ${card.textColor} opacity-50`}>{card.subtitle}</p>
                )}
                <p className={`text-2xl font-bold ${card.textColor} mt-2`}>
                  {card.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </p>
                <p className={`text-xs ${card.textColor} opacity-70`}>{card.unit}</p>
              </div>
              <Icon className={`w-8 h-8 ${card.iconColor || card.textColor} opacity-50`} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
