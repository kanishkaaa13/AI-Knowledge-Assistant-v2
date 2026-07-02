import Link from "next/link";
import { Sparkles } from "lucide-react";

import { ThemeToggle } from "@/components/ui/theme-toggle";

export function AuthFormShell({
  title,
  description,
  footer,
  children
}: {
  title: string;
  description: string;
  footer: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="absolute inset-0 bg-hero-grid bg-hero-grid opacity-80" />
      <div className="absolute left-1/2 top-0 h-[28rem] w-[28rem] -translate-x-1/2 rounded-full bg-primary/15 blur-3xl" />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 font-semibold">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p>AI Knowledge Assistant</p>
              <p className="text-xs font-normal text-muted-foreground">
                Secure access to your workspace
              </p>
            </div>
          </Link>
          <ThemeToggle />
        </div>

        <div className="flex flex-1 items-center justify-center py-10">
          <div className="grid w-full max-w-6xl gap-10 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="hidden flex-col justify-center gap-6 lg:flex">
              <div className="inline-flex w-fit rounded-full border border-border/60 bg-background/80 px-4 py-2 text-sm text-muted-foreground backdrop-blur">
                Authentication flow ready
              </div>
              <h1 className="max-w-xl text-5xl font-semibold tracking-tight">
                Sign in to manage knowledge, sessions, and assistant workflows.
              </h1>
              <p className="max-w-xl text-lg text-muted-foreground">
                This starter includes secure JWT cookies, refresh sessions, protected
                routes, and a scalable auth foundation for production features.
              </p>
            </div>

            <div className="glass-panel mx-auto w-full max-w-lg rounded-[2rem] p-6 shadow-2xl shadow-primary/10 sm:p-8">
              <div className="space-y-2">
                <h2 className="text-3xl font-semibold">{title}</h2>
                <p className="text-sm text-muted-foreground">{description}</p>
              </div>
              <div className="mt-8">{children}</div>
              <div className="mt-6 text-sm text-muted-foreground">{footer}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
