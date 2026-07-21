/** Shared PCF module constants (declared units, BOM line types, EN 15804 stages). */

export const DECLARED_UNITS = [
  { value: 'kilogram', label: 'kilogram (kg)' },
  { value: 'tonne', label: 'tonne (t)' },
  { value: 'piece', label: 'piece' },
  { value: 'liter', label: 'liter (L)' },
  { value: 'kilowatt_hour', label: 'kilowatt hour (kWh)' },
  { value: 'cubic_meter', label: 'cubic meter (m³)' },
  { value: 'square_meter', label: 'square meter (m²)' },
  { value: 'megajoule', label: 'megajoule (MJ)' },
  { value: 'ton_kilometer', label: 'tonne-kilometer (tkm)' },
];

export const UNIT_SHORT: Record<string, string> = {
  kilogram: 'kg',
  tonne: 't',
  piece: 'pc',
  liter: 'L',
  kilowatt_hour: 'kWh',
  cubic_meter: 'm³',
  square_meter: 'm²',
  megajoule: 'MJ',
  ton_kilometer: 'tkm',
};

export const INPUT_TYPES = [
  { value: 'purchased_material', label: 'Purchased material' },
  { value: 'energy', label: 'Energy' },
  { value: 'transport', label: 'Inbound transport' },
  { value: 'process', label: 'Process emissions' },
  { value: 'supplier_pcf', label: 'Supplier PCF' },
] as const;

export const INPUT_TYPE_LABEL: Record<string, string> = Object.fromEntries(
  INPUT_TYPES.map((t) => [t.value, t.label])
);

/** EN 15804 lifecycle stages we tag BOM lines with (A1-A3 = cradle-to-gate). */
export const STAGE_META: Record<string, { label: string; color: string }> = {
  A1: { label: 'A1 · Raw materials', color: 'bg-cy-accent' },
  A2: { label: 'A2 · Inbound transport', color: 'bg-cy-warn' },
  A3: { label: 'A3 · Production', color: 'bg-scope3' },
  A4: { label: 'A4 · Distribution', color: 'bg-cy-faint' },
  A5: { label: 'A5 · Installation', color: 'bg-cy-faint' },
};
