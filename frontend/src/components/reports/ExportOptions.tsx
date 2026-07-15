'use client';

import { useState } from 'react';
import { Surface, PanelLabel, Chip } from '@/components/canopy';
import { Button, Badge } from '@/components/ui';
import { formatNumber } from '@/lib/utils';
import { Loader2 } from 'lucide-react';
import type { CDPExport, ESRSE1Export } from '@/lib/api';

interface ExportOptionsProps {
  cdpData?: CDPExport | null;
  esrsData?: ESRSE1Export | null;
  cdpLoading?: boolean;
  esrsLoading?: boolean;
  onExportCDP: () => Promise<void>;
  onExportESRS: () => Promise<void>;
}

/** One label/value pair inside a compact preview line. */
function Kv({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <p className="text-[12px]">
      <span className="text-cy-muted">{label} </span>
      <b className="font-semibold tabular-nums text-cy-ink">{value}</b>
    </p>
  );
}

export function ExportOptions({
  cdpData,
  esrsData,
  cdpLoading,
  esrsLoading,
  onExportCDP,
  onExportESRS,
}: ExportOptionsProps) {
  const [cdpExporting, setCdpExporting] = useState(false);
  const [esrsExporting, setEsrsExporting] = useState(false);

  const handleCDPExport = async () => {
    setCdpExporting(true);
    try {
      await onExportCDP();
    } finally {
      setCdpExporting(false);
    }
  };

  const handleESRSExport = async () => {
    setEsrsExporting(true);
    try {
      await onExportESRS();
    } finally {
      setEsrsExporting(false);
    }
  };

  return (
    <div className="space-y-4">
      <Surface>
        <PanelLabel>Export</PanelLabel>
        <div className="divide-y divide-cy-row">
          {/* CDP */}
          <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2 py-3 first:pt-0 last:pb-0">
            <div className="min-w-0 flex-1">
              <p className="flex items-center gap-2 text-[13px] font-semibold text-cy-ink">
                CDP climate disclosure <Chip>CDP</Chip>
              </p>
              <p className="mt-0.5 max-w-[58ch] text-[12px] text-cy-muted">
                Carbon Disclosure Project questionnaire format — emissions by scope, data quality
                and factor sources, as structured JSON.
              </p>
              {cdpLoading ? (
                <p className="mt-2.5 flex items-center gap-1.5 text-[12px] text-cy-muted">
                  <Loader2 className="h-3 w-3 animate-spin" /> Building preview…
                </p>
              ) : cdpData ? (
                <div className="mt-2.5 flex flex-wrap gap-x-6 gap-y-1">
                  <Kv label="Org" value={cdpData.organization_name} />
                  <Kv label="Year" value={cdpData.reporting_year} />
                  <Kv
                    label="Scope 1"
                    value={`${formatNumber(cdpData.emissions_totals.scope_1_metric_tonnes, 1)} t`}
                  />
                  <Kv
                    label="Scope 2"
                    value={`${formatNumber(cdpData.emissions_totals.scope_2_location_based_metric_tonnes, 1)} t`}
                  />
                  <Kv
                    label="Scope 3"
                    value={`${formatNumber(cdpData.emissions_totals.scope_3_metric_tonnes, 1)} t`}
                  />
                  <Kv
                    label="Total"
                    value={`${formatNumber(cdpData.emissions_totals.total_metric_tonnes, 1)} t`}
                  />
                  <Kv
                    label="DQ"
                    value={`${cdpData.data_quality.overall_data_quality_score.toFixed(1)}/5`}
                  />
                  <span className="inline-flex items-center">
                    <Badge
                      variant={
                        cdpData.data_quality.verification_status === 'verified'
                          ? 'success'
                          : 'default'
                      }
                      size="sm"
                    >
                      {cdpData.data_quality.verification_status}
                    </Badge>
                  </span>
                </div>
              ) : null}
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleCDPExport}
              disabled={cdpExporting}
            >
              {cdpExporting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Export JSON
            </Button>
          </div>

          {/* ESRS E1 */}
          <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2 py-3 first:pt-0 last:pb-0">
            <div className="min-w-0 flex-1">
              <p className="flex items-center gap-2 text-[13px] font-semibold text-cy-ink">
                ESRS E1 climate change <Chip>CSRD</Chip>
              </p>
              <p className="mt-0.5 max-w-[58ch] text-[12px] text-cy-muted">
                European Sustainability Reporting Standards E1 — gross emissions, intensity
                metrics and transition plan, for CSRD compliance.
              </p>
              {esrsLoading ? (
                <p className="mt-2.5 flex items-center gap-1.5 text-[12px] text-cy-muted">
                  <Loader2 className="h-3 w-3 animate-spin" /> Building preview…
                </p>
              ) : esrsData ? (
                <div className="mt-2.5 flex flex-wrap gap-x-6 gap-y-1">
                  <Kv label="Undertaking" value={esrsData.undertaking_name} />
                  <Kv
                    label="Scope 1"
                    value={`${formatNumber(esrsData.gross_emissions.scope_1_tonnes, 1)} t`}
                  />
                  <Kv
                    label="Scope 2"
                    value={`${formatNumber(esrsData.gross_emissions.scope_2_location_based_tonnes, 1)} t`}
                  />
                  <Kv
                    label="Scope 3"
                    value={`${formatNumber(esrsData.gross_emissions.scope_3_tonnes, 1)} t`}
                  />
                  <Kv
                    label="Total"
                    value={`${formatNumber(esrsData.gross_emissions.total_ghg_emissions_tonnes, 1)} t`}
                  />
                  <Kv
                    label="Targets"
                    value={esrsData.climate_targets.length}
                  />
                  <Kv
                    label="Transition plan"
                    value={esrsData.transition_plan.has_transition_plan ? 'Yes' : 'No'}
                  />
                </div>
              ) : null}
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleESRSExport}
              disabled={esrsExporting}
            >
              {esrsExporting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Export JSON
            </Button>
          </div>
        </div>
      </Surface>

      <p className="px-1 text-[11.5px] text-cy-faint">
        Structured JSON for official submissions — transfer into the{' '}
        <a
          href="https://www.cdp.net"
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-cy-accent"
        >
          CDP
        </a>{' '}
        or{' '}
        <a
          href="https://www.efrag.org/lab6"
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-cy-accent"
        >
          ESRS
        </a>{' '}
        reporting platforms.
      </p>
    </div>
  );
}
