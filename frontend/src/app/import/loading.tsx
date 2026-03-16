export default function ImportLoading() {
  return (
    <div className="min-h-screen bg-background">
      <div className="pt-16 lg:pl-[280px]">
        <div className="p-4 md:p-6 lg:p-8 animate-pulse">
          {/* Header skeleton */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="h-8 w-16 bg-background-muted rounded-lg" />
              <div>
                <div className="h-8 w-40 bg-background-muted rounded-lg" />
                <div className="h-4 w-48 bg-background-muted rounded mt-2" />
              </div>
            </div>
          </div>

          {/* Upload area skeleton */}
          <div className="bg-background-elevated border-2 border-dashed border-border rounded-xl p-16 flex flex-col items-center justify-center mb-8">
            <div className="h-16 w-16 bg-background-muted rounded-full mb-4" />
            <div className="h-5 w-48 bg-background-muted rounded mb-2" />
            <div className="h-4 w-64 bg-background-muted rounded" />
          </div>

          {/* History skeleton */}
          <div className="bg-background-elevated border border-border-muted rounded-xl p-6">
            <div className="h-5 w-32 bg-background-muted rounded mb-6" />
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex gap-4 py-3 border-b border-border-muted last:border-0">
                <div className="h-5 w-40 bg-background-muted rounded flex-1" />
                <div className="h-5 w-24 bg-background-muted rounded" />
                <div className="h-5 w-20 bg-background-muted rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
