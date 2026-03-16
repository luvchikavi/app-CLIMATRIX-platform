export default function ReportsLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="pt-16 lg:pl-[280px]">
        <div className="p-4 md:p-6 lg:p-8 animate-pulse">
          {/* Header skeleton */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="h-8 w-32 bg-background-muted rounded-lg" />
              <div className="h-4 w-56 bg-background-muted rounded mt-2" />
            </div>
            <div className="flex gap-3">
              <div className="h-9 w-48 bg-background-muted rounded-lg" />
              <div className="h-9 w-16 bg-background-muted rounded-lg" />
              <div className="h-9 w-16 bg-background-muted rounded-lg" />
            </div>
          </div>

          {/* Tab navigation skeleton */}
          <div className="flex gap-2 border-b border-border pb-4 mb-6">
            {[...Array(9)].map((_, i) => (
              <div key={i} className="h-9 w-24 bg-background-muted rounded-lg" />
            ))}
          </div>

          {/* KPI cards skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-background-elevated border border-border-muted rounded-xl p-6">
                <div className="h-3 w-24 bg-background-muted rounded mb-3" />
                <div className="h-8 w-28 bg-background-muted rounded mb-2" />
                <div className="h-3 w-20 bg-background-muted rounded" />
              </div>
            ))}
          </div>

          {/* Charts skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="bg-background-elevated border border-border-muted rounded-xl p-6">
                <div className="h-5 w-40 bg-background-muted rounded mb-6" />
                <div className="h-64 bg-background-muted rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
