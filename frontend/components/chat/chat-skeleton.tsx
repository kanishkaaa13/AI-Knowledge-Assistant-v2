export function ChatSkeleton() {
  return (
    <div className="flex gap-4">
      <div className="h-10 w-10 rounded-2xl bg-primary/10" />
      <div className="w-full max-w-2xl rounded-[2rem] border border-border/60 bg-card/80 p-5">
        <div className="space-y-3">
          <div className="h-3 w-24 animate-pulse rounded-full bg-secondary" />
          <div className="h-4 w-full animate-pulse rounded-full bg-secondary" />
          <div className="h-4 w-5/6 animate-pulse rounded-full bg-secondary" />
          <div className="h-4 w-3/5 animate-pulse rounded-full bg-secondary" />
        </div>
      </div>
    </div>
  );
}
