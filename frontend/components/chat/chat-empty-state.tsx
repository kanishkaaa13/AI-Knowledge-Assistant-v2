"use client";

import * as React from "react";
import { Sparkles, FileText, Layers, FileEdit, HelpCircle, MessageSquare, Flame } from "lucide-react";

interface ChatEmptyStateProps {
  onUsePrompt?: (prompt: string) => void;
  allDocsCount?: number;
  chatCount?: number;
}

const prompts = [
  "Summarize my Java docs",
  "Explain JDBC connection pooling",
  "What is the difference between Statement and ResultSet?"
];

export function ChatEmptyState({ onUsePrompt, allDocsCount = 2, chatCount = 5 }: ChatEmptyStateProps) {
  // Mock data for weekly study hours
  const studyData = [
    { day: "Mon", minutes: 45, height: "30%" },
    { day: "Tue", minutes: 90, height: "60%" },
    { day: "Wed", minutes: 120, height: "80%" },
    { day: "Thu", minutes: 60, height: "40%" },
    { day: "Fri", minutes: 150, height: "100%" },
    { day: "Sat", minutes: 80, height: "55%" },
    { day: "Sun", minutes: 30, height: "20%" }
  ];

  const stats = [
    { label: "Uploaded Docs", value: allDocsCount, icon: FileText, color: "text-indigo-400" },
    { label: "Flashcards", value: 320, icon: Layers, color: "text-emerald-400" },
    { label: "Study Notes", value: 12, icon: FileEdit, color: "text-cyan-400" },
    { label: "Quizzes", value: 18, icon: HelpCircle, color: "text-amber-400" },
    { label: "Chat Sessions", value: chatCount, icon: MessageSquare, color: "text-rose-400" }
  ];

  const hotTopics = [
    { label: "JDBC Drivers", size: "text-xs font-semibold px-2.5 py-1.5 bg-indigo-500/10 border-indigo-500/20 text-indigo-400" },
    { label: "Java Swing", size: "text-xs font-semibold px-2.5 py-1.5 bg-rose-500/10 border-rose-500/20 text-rose-400" },
    { label: "SQL Queries", size: "text-xs font-semibold px-2.5 py-1.5 bg-emerald-500/10 border-emerald-500/20 text-emerald-400" },
    { label: "ResultSet Handling", size: "text-xs font-semibold px-2.5 py-1.5 bg-amber-500/10 border-amber-500/20 text-amber-400" },
    { label: "Servlet Lifecycle", size: "text-xs font-semibold px-2.5 py-1.5 bg-cyan-500/10 border-cyan-500/20 text-cyan-400" },
    { label: "Connection Pool", size: "text-xs font-semibold px-2.5 py-1.5 bg-purple-500/10 border-purple-500/20 text-purple-400" }
  ];

  return (
    <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-6 scrollbar-thin">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        {/* Header section */}
        <div className="flex flex-col items-center text-center space-y-2 py-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.15)]">
            <Sparkles className="h-6 w-6 animate-pulse" />
          </div>
          <h1 className="text-xl font-semibold text-white tracking-tight sm:text-2xl">
            Welcome to Your AI Study Workspace
          </h1>
          <p className="text-xs text-muted-foreground max-w-md">
            Query your library, study custom flashcard decks, and compile structured notebooks using local AI.
          </p>
        </div>

        {/* 1. Stats Grid */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {stats.map((stat, idx) => (
            <div
              key={idx}
              className="rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-3.5 flex flex-col justify-between hover:border-indigo-500/30 transition-all duration-300 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">
                  {stat.label}
                </span>
                <stat.icon className={`h-4 w-4 ${stat.color} group-hover:scale-110 transition-transform`} />
              </div>
              <div className="mt-3 flex items-baseline">
                <span className="text-2xl font-bold text-white tracking-tight">
                  {stat.value}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* 2. Charts / Analytics Row */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Study Time Activity */}
          <div className="rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-4 flex flex-col justify-between h-[220px]">
            <div className="flex items-center justify-between border-b border-border/10 pb-2">
              <span className="text-xs font-semibold text-white">Study Time Activity</span>
              <span className="text-[10px] text-muted-foreground">This Week</span>
            </div>
            
            {/* Simple CSS Bar Chart */}
            <div className="flex-1 flex items-end justify-between px-2 pt-4 pb-2 h-full">
              {studyData.map((data, idx) => (
                <div key={idx} className="flex flex-col items-center gap-1.5 flex-1 group">
                  <div className="relative w-full flex justify-center">
                    {/* Tooltip on hover */}
                    <span className="absolute -top-7 scale-0 group-hover:scale-100 transition-all duration-200 bg-neutral-900 border border-border/40 text-[9px] px-1.5 py-0.5 rounded text-white z-10">
                      {data.minutes}m
                    </span>
                    <div
                      style={{ height: data.height }}
                      className="w-4 bg-indigo-600 hover:bg-indigo-500 rounded-t transition-all duration-300"
                    />
                  </div>
                  <span className="text-[9px] text-muted-foreground font-semibold">
                    {data.day}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Hot Topics tag cloud */}
          <div className="rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-4 flex flex-col justify-between h-[220px]">
            <div className="flex items-center justify-between border-b border-border/10 pb-2">
              <span className="text-xs font-semibold text-white flex items-center gap-1">
                <Flame className="h-3.5 w-3.5 text-amber-500" /> Hot Concept Topics
              </span>
              <span className="text-[10px] text-muted-foreground">Most Visited</span>
            </div>

            <div className="flex-1 flex flex-wrap gap-2 items-center justify-center p-3">
              {hotTopics.map((topic, idx) => (
                <span
                  key={idx}
                  className={`rounded-full border transition-all duration-300 hover:scale-105 cursor-default ${topic.size}`}
                >
                  {topic.label}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* 3. Quickstart Prompts */}
        <div className="flex flex-col items-center pt-2">
          <p className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground mb-3.5">
            Or begin with a query
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {prompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => onUsePrompt?.(prompt)}
                className="rounded-full border border-border/40 bg-[var(--assistant-bubble)] px-4 py-2 text-xs text-white/90 transition-all duration-200 hover:border-indigo-500 hover:bg-indigo-500/10 text-center"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
