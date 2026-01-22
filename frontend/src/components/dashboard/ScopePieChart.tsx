'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { formatCO2e } from '@/lib/utils';

interface ScopePieChartProps {
  data: {
    scope_1_co2e_kg: number;
    scope_2_co2e_kg: number;
    scope_3_co2e_kg: number;
  };
}

// Use design system colors for scopes
const SCOPE_COLORS = {
  1: 'var(--color-scope1)',    // red
  2: 'var(--color-scope2)',    // amber
  3: 'var(--color-scope3)',    // blue
};

export function ScopePieChart({ data }: ScopePieChartProps) {
  const chartData = [
    { name: 'Scope 1', value: data.scope_1_co2e_kg, color: SCOPE_COLORS[1] },
    { name: 'Scope 2', value: data.scope_2_co2e_kg, color: SCOPE_COLORS[2] },
    { name: 'Scope 3', value: data.scope_3_co2e_kg, color: SCOPE_COLORS[3] },
  ].filter((item) => item.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-foreground-muted">
        No emissions data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
          labelLine={{ stroke: 'var(--color-foreground-muted)' }}
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--color-background-elevated)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            boxShadow: 'var(--shadow-md)',
          }}
          labelStyle={{ color: 'var(--color-foreground)' }}
          formatter={(value) => [
            formatCO2e(value as number),
            'Emissions',
          ]}
        />
        <Legend
          wrapperStyle={{
            paddingTop: '16px',
          }}
          formatter={(value) => (
            <span style={{ color: 'var(--color-foreground)' }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
