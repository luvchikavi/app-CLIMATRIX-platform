'use client';

import { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  Button,
  Badge,
} from '@/components/ui';
import { formatNumber } from '@/lib/utils';
import {
  Download,
  FileJson,
  Globe,
  Building2,
  Leaf,
  CheckCircle,
  ExternalLink,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import type { CDPExport, ESRSE1Export } from '@/lib/api';

interface ExportOptionsProps {
  cdpData?: CDPExport | null;
  esrsData?: ESRSE1Export | null;
  cdpLoading?: boolean;
  esrsLoading?: boolean;
  onExportCDP: () => Promise<void>;
  onExportESRS: () => Promise<void>;
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
    <div className="space-y-6">
      {/* Export Overview */}
      <Card className="bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
        <CardContent className="py-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-xl bg-primary/10">
              <Download className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">Export Data</h2>
              <p className="text-foreground-muted mt-1">
                Export your GHG inventory data in standardized formats for reporting frameworks.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CDP Climate Export */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-foreground-muted" />
              CDP Climate Disclosure
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Badge variant="info">CDP</Badge>
                <p className="text-sm text-foreground-muted">
                  Carbon Disclosure Project format for climate change questionnaire submissions.
                </p>
              </div>

              {cdpLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : cdpData ? (
                <div className="bg-background-muted rounded-lg p-4 space-y-3">
                  <h4 className="font-semibold text-foreground text-sm">Preview</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-foreground-muted">Organization</p>
                      <p className="font-medium">{cdpData.organization_name}</p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Reporting Year</p>
                      <p className="font-medium">{cdpData.reporting_year}</p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Scope 1</p>
                      <p className="font-medium">
                        {formatNumber(cdpData.emissions_totals.scope_1_metric_tonnes, 1)} t
                      </p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Scope 2 (Location)</p>
                      <p className="font-medium">
                        {formatNumber(cdpData.emissions_totals.scope_2_location_based_metric_tonnes, 1)} t
                      </p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Scope 3</p>
                      <p className="font-medium">
                        {formatNumber(cdpData.emissions_totals.scope_3_metric_tonnes, 1)} t
                      </p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Total</p>
                      <p className="font-bold text-primary">
                        {formatNumber(cdpData.emissions_totals.total_metric_tonnes, 1)} t
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-border">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-foreground-muted">Data Quality Score</span>
                      <span className="font-medium">
                        {cdpData.data_quality.overall_data_quality_score.toFixed(1)}/5
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-1">
                      <span className="text-foreground-muted">Verified Data</span>
                      <span className="font-medium">
                        {cdpData.data_quality.percentage_verified_data.toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-1">
                      <span className="text-foreground-muted">Verification Status</span>
                      <Badge
                        variant={
                          cdpData.data_quality.verification_status === 'verified' ? 'success' : 'default'
                        }
                        size="sm"
                      >
                        {cdpData.data_quality.verification_status}
                      </Badge>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-background-muted rounded-lg p-4 text-center">
                  <AlertCircle className="w-8 h-8 text-foreground-muted mx-auto mb-2" />
                  <p className="text-sm text-foreground-muted">
                    Click export to generate CDP format data
                  </p>
                </div>
              )}

              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-foreground-muted">
                  <CheckCircle className="w-4 h-4 text-success" />
                  <span>Scope 1, 2 & 3 emissions breakdown</span>
                </div>
                <div className="flex items-center gap-2 text-foreground-muted">
                  <CheckCircle className="w-4 h-4 text-success" />
                  <span>Data quality and verification status</span>
                </div>
                <div className="flex items-center gap-2 text-foreground-muted">
                  <CheckCircle className="w-4 h-4 text-success" />
                  <span>Emission factor sources documented</span>
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter className="border-t border-border bg-background-muted/30">
            <div className="flex items-center justify-between w-full">
              <a
                href="https://www.cdp.net"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                Learn more about CDP <ExternalLink className="w-3 h-3" />
              </a>
              <Button
                variant="primary"
                leftIcon={
                  cdpExporting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <FileJson className="w-4 h-4" />
                  )
                }
                onClick={handleCDPExport}
                disabled={cdpExporting}
              >
                Export CDP JSON
              </Button>
            </div>
          </CardFooter>
        </Card>

        {/* ESRS E1 Export */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-foreground-muted" />
              ESRS E1 Climate Change
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Badge variant="warning">CSRD</Badge>
                <p className="text-sm text-foreground-muted">
                  European Sustainability Reporting Standards E1 format for CSRD compliance.
                </p>
              </div>

              {esrsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : esrsData ? (
                <div className="bg-background-muted rounded-lg p-4 space-y-3">
                  <h4 className="font-semibold text-foreground text-sm">Preview</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-foreground-muted">Undertaking</p>
                      <p className="font-medium">{esrsData.undertaking_name}</p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Consolidation Scope</p>
                      <p className="font-medium">{esrsData.consolidation_scope}</p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Scope 1</p>
                      <p className="font-medium">
                        {formatNumber(esrsData.gross_emissions.scope_1_tonnes, 1)} t
                      </p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Scope 2 (Location)</p>
                      <p className="font-medium">
                        {formatNumber(esrsData.gross_emissions.scope_2_location_based_tonnes, 1)} t
                      </p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Scope 3</p>
                      <p className="font-medium">
                        {formatNumber(esrsData.gross_emissions.scope_3_tonnes, 1)} t
                      </p>
                    </div>
                    <div>
                      <p className="text-foreground-muted">Total GHG</p>
                      <p className="font-bold text-primary">
                        {formatNumber(esrsData.gross_emissions.total_ghg_emissions_tonnes, 1)} t
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-border">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-foreground-muted">Transition Plan</span>
                      <Badge variant={esrsData.transition_plan.has_transition_plan ? 'success' : 'default'} size="sm">
                        {esrsData.transition_plan.has_transition_plan ? 'Yes' : 'No'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-1">
                      <span className="text-foreground-muted">Climate Targets</span>
                      <span className="font-medium">{esrsData.climate_targets.length} defined</span>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-1">
                      <span className="text-foreground-muted">Intensity Metrics</span>
                      <span className="font-medium">{esrsData.intensity_metrics.length} defined</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-background-muted rounded-lg p-4 text-center">
                  <AlertCircle className="w-8 h-8 text-foreground-muted mx-auto mb-2" />
                  <p className="text-sm text-foreground-muted">
                    Click export to generate ESRS E1 format data
                  </p>
                </div>
              )}

              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-foreground-muted">
                  <CheckCircle className="w-4 h-4 text-success" />
                  <span>Gross GHG emissions by scope</span>
                </div>
                <div className="flex items-center gap-2 text-foreground-muted">
                  <CheckCircle className="w-4 h-4 text-success" />
                  <span>Scope 3 category breakdown</span>
                </div>
                <div className="flex items-center gap-2 text-foreground-muted">
                  <CheckCircle className="w-4 h-4 text-success" />
                  <span>Transition plan and targets</span>
                </div>
                <div className="flex items-center gap-2 text-foreground-muted">
                  <CheckCircle className="w-4 h-4 text-success" />
                  <span>Intensity metrics</span>
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter className="border-t border-border bg-background-muted/30">
            <div className="flex items-center justify-between w-full">
              <a
                href="https://www.efrag.org/lab6"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                Learn more about ESRS <ExternalLink className="w-3 h-3" />
              </a>
              <Button
                variant="primary"
                leftIcon={
                  esrsExporting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <FileJson className="w-4 h-4" />
                  )
                }
                onClick={handleESRSExport}
                disabled={esrsExporting}
              >
                Export ESRS E1 JSON
              </Button>
            </div>
          </CardFooter>
        </Card>
      </div>

      {/* Additional Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Leaf className="w-5 h-5 text-foreground-muted" />
            Export Standards Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-foreground mb-2">CDP (Carbon Disclosure Project)</h4>
              <p className="text-sm text-foreground-muted">
                CDP is a not-for-profit charity that runs the global disclosure system for
                investors, companies, cities, states and regions to manage their environmental
                impacts. The exported JSON follows CDP's climate change questionnaire structure.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-2">ESRS E1 (CSRD)</h4>
              <p className="text-sm text-foreground-muted">
                The European Sustainability Reporting Standards (ESRS) E1 covers climate change
                disclosure requirements under the Corporate Sustainability Reporting Directive
                (CSRD). The export includes gross emissions, intensity metrics, and transition plans.
              </p>
            </div>
          </div>
          <div className="mt-6 p-4 bg-info/10 rounded-lg border border-info/20">
            <p className="text-sm text-info">
              <strong>Note:</strong> These exports provide structured data in JSON format. For
              official submissions, you may need to transfer this data to the respective reporting
              platforms' submission systems.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
