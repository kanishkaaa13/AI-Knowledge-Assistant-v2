export function ChatHeader({
  title,
  subtitle
}: {
  title: string;
  subtitle: string;
}) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-[0.24em] text-muted-foreground">
        Personal AI Workspace
      </p>
      <h1 className="text-lg font-semibold sm:text-xl">{title}</h1>
      <p className="text-sm text-muted-foreground">{subtitle}</p>
    </div>
  );
}
