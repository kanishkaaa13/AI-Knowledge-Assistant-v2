"use client";

import {
  Activity,
  Database,
  FileClock,
  HardDrive,
  Lock,
  MessageSquareText
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
  BarChart
} from "recharts";

import { AppSidebar } from "@/components/layout/app-sidebar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnalyticsOverview } from "@/hooks/use-analytics-overview";

const metricIcons = [Database, MessageSquareText, HardDrive, Activity];

function formatBytes(size: number) {
  const units = ["B", "KB", "MB", "GB"];
  let value = size;
  let unit = units[0];
  for (const nextUnit of units) {
    unit = nextUnit;
    if (value < 1024 || nextUnit === units.at(-1)) {
      break;
    }
    value /= 1024;
  }
  return `${value.toFixed(1)} ${unit}`;
}

export function AnalyticsDashboard() {
  const { data, isLoading } = useAnalyticsOverview();

  return (
    <div className="min-h-screen bg-background px-4 py-4 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
        <AppSidebar />

        <main className="space-y-4">
          <section className="rounded-[2rem] border border-border/60 bg-card/70 p-6 backdrop-blur">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-muted-foreground">
                  Analytics
                </p>
                <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                  Privacy-first workspace insights
                </h1>
                <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                  Track uploads, chat activity, storage usage, and local-only AI behavior without
                  sending your analytics data to a remote service.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <Badge className="rounded-full bg-primary/10 px-3 py-1 text-primary">
                  <Lock className="mr-1 h-3.5 w-3.5" />
                  Local-only inference
                </Badge>
                <Badge className="rounded-full bg-emerald-500/10 px-3 py-1 text-emerald-600 dark:text-emerald-300">
                  Secure uploads enabled
                </Badge>
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {(data?.metrics ?? Array.from({ length: 4 }).map(() => null)).map((metric, index) => {
              const Icon = metricIcons[index] ?? Activity;

              return (
                <Card key={metric?.label ?? index} className="rounded-[1.75rem] border-border/60 bg-card/70">
                  <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
                    <div>
                      <CardTitle className="text-sm font-medium text-muted-foreground">
                        {metric?.label ?? "Loading metric"}
                      </CardTitle>
                      <div className="mt-2 text-3xl font-semibold">
                        {isLoading ? <div className="h-9 w-24 animate-pulse rounded bg-secondary/60" /> : metric?.value}
                      </div>
                    </div>
                    <div className="rounded-2xl bg-primary/10 p-3 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      {metric?.detail ?? "Preparing your private workspace analytics..."}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.35fr_1fr]">
            <Card className="rounded-[1.75rem] border-border/60 bg-card/70">
              <CardHeader>
                <CardTitle>Document uploads over time</CardTitle>
              </CardHeader>
              <CardContent className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data?.uploads_timeline ?? []}>
                    <defs>
                      <linearGradient id="uploadsGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.45} />
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="label" stroke="hsl(var(--muted-foreground))" />
                    <YAxis stroke="hsl(var(--muted-foreground))" allowDecimals={false} />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2.5}
                      fill="url(#uploadsGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="rounded-[1.75rem] border-border/60 bg-card/70">
              <CardHeader>
                <CardTitle>Chat creation trend</CardTitle>
              </CardHeader>
              <CardContent className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data?.chats_timeline ?? []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="label" stroke="hsl(var(--muted-foreground))" />
                    <YAxis stroke="hsl(var(--muted-foreground))" allowDecimals={false} />
                    <Tooltip />
                    <Bar
                      dataKey="value"
                      radius={[12, 12, 0, 0]}
                      fill="hsl(var(--primary))"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <Card className="rounded-[1.75rem] border-border/60 bg-card/70">
              <CardHeader>
                <CardTitle>Recent uploads</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-hidden rounded-3xl border border-border/60">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-secondary/60 text-muted-foreground">
                      <tr>
                        <th className="px-4 py-3 font-medium">Document</th>
                        <th className="px-4 py-3 font-medium">Size</th>
                        <th className="px-4 py-3 font-medium">Status</th>
                        <th className="px-4 py-3 font-medium">Uploaded</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(data?.recent_uploads ?? []).map((item) => (
                        <tr key={item.id} className="border-t border-border/60">
                          <td className="px-4 py-3">
                            <div className="font-medium">{item.title}</div>
                            <div className="text-xs text-muted-foreground">{item.file_name}</div>
                          </td>
                          <td className="px-4 py-3">{formatBytes(item.file_size)}</td>
                          <td className="px-4 py-3">
                            <Badge variant="secondary" className="rounded-full">
                              {item.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {new Date(item.uploaded_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!data?.recent_uploads?.length && !isLoading ? (
                    <div className="px-4 py-10 text-center text-sm text-muted-foreground">
                      No uploads yet. Add documents to start building knowledge analytics.
                    </div>
                  ) : null}
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-[1.75rem] border-border/60 bg-card/70">
              <CardHeader>
                <CardTitle>AI usage stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-3xl bg-secondary/50 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      Assistant replies
                    </p>
                    <p className="mt-2 text-2xl font-semibold">
                      {data?.ai_usage.assistant_messages ?? 0}
                    </p>
                  </div>
                  <div className="rounded-3xl bg-secondary/50 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      User prompts
                    </p>
                    <p className="mt-2 text-2xl font-semibold">
                      {data?.ai_usage.user_messages ?? 0}
                    </p>
                  </div>
                </div>

                <div className="rounded-3xl border border-border/60 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium">Primary local model</p>
                      <p className="text-sm text-muted-foreground">
                        {data?.ai_usage.primary_model ?? "llama3"}
                      </p>
                    </div>
                    <Badge className="rounded-full bg-primary/10 px-3 py-1 text-primary">
                      {data?.ai_usage.local_only_inference ? "Local only" : "External"}
                    </Badge>
                  </div>
                  <div className="mt-4 flex items-center gap-3 text-sm text-muted-foreground">
                    <FileClock className="h-4 w-4 text-primary" />
                    Avg. messages per chat: {data?.ai_usage.average_messages_per_chat ?? 0}
                  </div>
                </div>

                <div className="h-[180px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data?.messages_timeline ?? []}>
                      <defs>
                        <linearGradient id="messagesGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.45} />
                          <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.02} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="label" stroke="hsl(var(--muted-foreground))" />
                      <YAxis stroke="hsl(var(--muted-foreground))" allowDecimals={false} />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="#0ea5e9"
                        strokeWidth={2.5}
                        fill="url(#messagesGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </section>
        </main>
      </div>
    </div>
  );
}
