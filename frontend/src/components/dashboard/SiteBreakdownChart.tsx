'use client';

import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { SiteEmissionSummary } from '@/lib/api';
import { formatCO2e } from '@/lib/utils';

interface SiteBreakdownChartProps {
  data: SiteEmissionSummary[];
  onSiteClick?: (siteId: string) => void;
}

const SCOPE_COLORS = {
  scope1: '#ef4444', // red
  scope2: '#f59e0b', // amber
  scope3: '#3b82f6', // blue
};

export function SiteBreakdownChart({ data, onSiteClick }: SiteBreakdownChartProps) {
  const chartData = useMemo(() => {
    return data.map((site) => ({
      name: site.site_name.length > 20 ? site.site_name.slice(0, 18) + '...' : site.site_name,
      fullName: site.site_name,
      siteId: site.site_id,
      'Scope 1': Math.round(site.scope_1_co2e_kg),
      'Scope 2': Math.round(site.scope_2_co2e_kg),
      'Scope 3': Math.round(site.scope_3_co2e_kg),
      total: Math.round(site.total_co2e_kg),
    }));
  }, [data]);

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-foreground-muted">
        <p className="text-sm">No site emissions data available</p>
        <p className="text-xs mt-1">Upload data for your sites to see the breakdown</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(250, data.length * 45 + 60)}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
        onClick={(e: any) => {
          if (e?.activePayload?.[0]?.payload?.siteId && onSiteClick) {
            onSiteClick(e.activePayload[0].payload.siteId);
          }
        }}
      >
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
        <XAxis
          type="number"
          tickFormatter={(val) => {
            if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
            if (val >= 1000) return `${(val / 1000).toFixed(0)}k`;
            return val.toString();
          }}
          fontSize={11}
        />
        <YAxis
          dataKey="name"
          type="category"
          width={120}
          fontSize={11}
          tick={{ fill: 'var(--foreground-muted)' }}
        />
        <Tooltip
          formatter={(value: any, name: any) => [
            `${Number(value).toLocaleString()} kg CO2e`,
            String(name),
          ]}
          labelFormatter={(label, payload) => {
            const item = payload?.[0]?.payload;
            return item?.fullName || label;
          }}
          contentStyle={{
            backgroundColor: 'var(--background-elevated)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            fontSize: '12px',
          }}
        />
        <Legend fontSize={12} />
        <Bar dataKey="Scope 1" stackId="a" fill={SCOPE_COLORS.scope1} radius={[0, 0, 0, 0]} />
        <Bar dataKey="Scope 2" stackId="a" fill={SCOPE_COLORS.scope2} />
        <Bar dataKey="Scope 3" stackId="a" fill={SCOPE_COLORS.scope3} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
