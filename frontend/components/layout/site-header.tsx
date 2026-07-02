import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link className="flex items-center gap-3 font-semibold" href="/">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p>AI Knowledge Assistant</p>
            <p className="text-xs font-normal text-muted-foreground">
              Research, retrieval, and response workflows
            </p>
          </div>
        </Link>
        <div className="flex items-center gap-3">
          <Button asChild variant="secondary" size="sm">
            <Link href="/login">Log in</Link>
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
