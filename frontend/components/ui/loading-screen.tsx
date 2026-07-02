export function LoadingScreen() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="glass-panel flex items-center gap-4 px-6 py-5">
        <div className="h-3 w-3 animate-pulse rounded-full bg-primary" />
        <p className="text-sm text-muted-foreground">
          Warming up your knowledge workspace...
        </p>
      </div>
    </div>
  );
}
