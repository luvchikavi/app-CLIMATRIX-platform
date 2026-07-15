/**
 * Canopy theme values for recharts: muted grid, scope colors, 12px labels,
 * no chart borders. Values reference the cy-* CSS variables so charts follow
 * light/dark automatically. If a chart can't be made quiet with these,
 * replace it with BarList (bars-over-numbers usually prefers that anyway).
 */
export const canopyChart = {
  grid: 'var(--cy-row)',
  axisLine: 'var(--cy-row)',
  tick: { fontSize: 12, fill: 'var(--cy-muted)' },
  scope: {
    1: 'var(--cy-scope1)',
    2: 'var(--cy-scope2)',
    3: 'var(--cy-scope3)',
  } as Record<1 | 2 | 3, string>,
  series: [
    'var(--cy-accent)',
    'var(--cy-scope3)',
    'var(--cy-scope1)',
    'var(--cy-warn)',
    'var(--cy-faint)',
  ],
  tooltip: {
    contentStyle: {
      background: 'var(--cy-surface)',
      border: 'none',
      borderRadius: 12,
      boxShadow: 'var(--cy-shadow-surface)',
      fontSize: 12.5,
      color: 'var(--cy-ink)',
    },
  },
};
