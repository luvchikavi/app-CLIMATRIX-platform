export default function SettingsLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="pt-16 lg:pl-[280px]">
        <div className="p-4 md:p-6 lg:p-8 animate-pulse">
          {/* Header skeleton */}
          <div className="mb-8">
            <div className="h-8 w-32 bg-background-muted rounded-lg" />
            <div className="h-4 w-56 bg-background-muted rounded mt-2" />
          </div>

          {/* Settings cards skeleton */}
          <div className="space-y-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-background-elevated border border-border-muted rounded-xl p-6">
                <div className="h-5 w-40 bg-background-muted rounded mb-4" />
                <div className="space-y-3">
                  <div className="h-4 w-full bg-background-muted rounded" />
                  <div className="h-4 w-3/4 bg-background-muted rounded" />
                  <div className="h-10 w-full bg-background-muted rounded mt-2" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
