import Link from "next/link";
import { ArrowRight, Bot, Database, SearchCheck } from "lucide-react";

import { SiteHeader } from "@/components/layout/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    title: "Knowledge ingestion",
    description: "Organize documents, notes, and domain data into a searchable assistant context.",
    icon: Database
  },
  {
    title: "Smart retrieval",
    description: "Bridge frontend workflows and backend APIs with a scalable query and response layer.",
    icon: SearchCheck
  },
  {
    title: "AI workflows",
    description: "Ship an assistant-ready product foundation with app routing, theming, and reusable UI.",
    icon: Bot
  }
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <section className="overflow-hidden">
        <div className="mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.2fr_0.8fr] lg:px-8 lg:py-24">
          <div className="space-y-8">
            <Badge className="bg-primary/10 text-primary">Full-stack starter kit</Badge>
            <div className="space-y-6">
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
                Build an AI knowledge assistant with a frontend your users will enjoy.
              </h1>
              <p className="max-w-2xl text-lg text-muted-foreground">
                This project scaffold combines Next.js App Router, Tailwind, shadcn/ui,
                FastAPI, PostgreSQL, and SQLAlchemy into a clean foundation for
                conversational knowledge products.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg">
                <Link href="/dashboard">
                  Open dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="secondary" size="lg">
                <Link href="/register">Create account</Link>
              </Button>
            </div>
          </div>

          <div className="glass-panel bg-hero-grid bg-hero-grid p-6">
            <div className="rounded-[28px] border border-border/60 bg-background/80 p-6 shadow-2xl shadow-primary/5">
              <div className="grid gap-4 sm:grid-cols-2">
                {features.map((feature) => (
                  <Card key={feature.title} className="border-border/60 bg-card/80">
                    <CardHeader>
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                        <feature.icon className="h-5 w-5" />
                      </div>
                      <CardTitle>{feature.title}</CardTitle>
                      <CardDescription>{feature.description}</CardDescription>
                    </CardHeader>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="grid gap-6 md:grid-cols-3">
          {features.map((feature) => (
            <Card key={feature.title} className="h-full">
              <CardHeader>
                <CardTitle>{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Designed for responsive layouts, reusable modules, and future AI
                  product expansion.
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
