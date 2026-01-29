'use client';

import { EmissionProfileAnalysis } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  Loader2,
  Factory,
  Zap,
  Truck,
  Building2,
} from 'lucide-react';

interface EmissionProfileCardProps {
  profile?: EmissionProfileAnalysis;
  isLoading?: boolean;
}

export function EmissionProfileCard({ profile, isLoading }: EmissionProfileCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Emission Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!profile || profile.top_sources.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Emission Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-foreground-muted">
            <Factory className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No emission data available for this period.</p>
            <p className="text-sm mt-1">Import activities to see your emission profile.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const scopeColors = {
    1: 'bg-error/10 text-error',
    2: 'bg-warning/10 text-warning',
    3: 'bg-primary/10 text-primary',
  };

  const scopeIcons = {
    1: Factory,
    2: Zap,
    3: Truck,
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Emission Profile</span>
          <Badge variant="secondary">{profile.period_name}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Scope Breakdown */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[1, 2, 3].map((scope) => {
            const Icon = scopeIcons[scope as 1 | 2 | 3];
            const tonnes = scope === 1 ? profile.scope1_co2e_tonnes :
                          scope === 2 ? profile.scope2_co2e_tonnes :
                          profile.scope3_co2e_tonnes;
            const pct = profile.total_co2e_tonnes > 0
              ? (tonnes / profile.total_co2e_tonnes * 100).toFixed(0)
              : 0;

            return (
              <div key={scope} className="text-center">
                <div className={cn(
                  "w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-2",
                  scopeColors[scope as 1 | 2 | 3]
                )}>
                  <Icon className="w-6 h-6" />
                </div>
                <p className="text-lg font-bold text-foreground">{Number(tonnes || 0).toLocaleString()}</p>
                <p className="text-sm text-foreground-muted">Scope {scope} ({pct}%)</p>
              </div>
            );
          })}
        </div>

        {/* Top Sources */}
        <div>
          <h4 className="font-medium text-foreground mb-3">Top Emission Sources</h4>
          <div className="space-y-3">
            {profile.top_sources.slice(0, 5).map((source, index) => (
              <div key={source.activity_key} className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-background-muted flex items-center justify-center text-sm font-medium text-foreground-muted">
                  {index + 1}
                </span>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-foreground">{source.display_name}</span>
                    <span className="text-sm font-medium text-foreground">
                      {Number(source.total_co2e_tonnes || 0).toLocaleString()} tCO2e
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 h-2 bg-background-muted rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full",
                          scopeColors[source.scope as 1 | 2 | 3].split(' ')[0].replace('/10', '')
                        )}
                        style={{ width: `${Number(source.percentage_of_total || 0)}%` }}
                      />
                    </div>
                    <span className="text-xs text-foreground-muted w-12 text-right">
                      {Number(source.percentage_of_total || 0).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Category Breakdown */}
        {Object.keys(profile.emissions_by_category).length > 0 && (
          <div className="mt-6 pt-4 border-t border-border">
            <h4 className="font-medium text-foreground mb-3">By Category</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(profile.emissions_by_category)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 8)
                .map(([category, tonnes]) => (
                  <Badge key={category} variant="secondary" className="text-xs">
                    {category}: {tonnes.toLocaleString()} t
                  </Badge>
                ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
