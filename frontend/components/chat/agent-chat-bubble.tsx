"use client";

import * as React from "react";
import { Bot } from "lucide-react";

import { cn } from "@/lib/utils";

// -----------------------------------------------------------------------
// Tool-decision chip config
// Maps tool_used values from the backend to a human-readable label + emoji.
// New tools can be added here without touching any other file.
// -----------------------------------------------------------------------
const TOOL_LABELS: Record<string, { emoji: string; label: string; color: string }> = {
  search_documents: {
    emoji: "🔍",
    label: "Decided to search documents",
    color: "text-indigo-400",
  },
  summarize_document: {
    emoji: "📄",
    label: "Decided to summarize a document",
    color: "text-blue-400",
  },
  answer_general_knowledge: {
    emoji: "💬",
    label: "Answered from general knowledge",
    color: "text-emerald-400",
  },
};

function getToolMeta(toolUsed: string) {
  return (
    TOOL_LABELS[toolUsed] ?? {
      emoji: "🤖",
      label: toolUsed ? `Used tool: ${toolUsed}` : "No tool invoked",
      color: "text-muted-foreground",
    }
  );
}

// -----------------------------------------------------------------------
// AgentTraceChip — the visual variant of the existing thinking-state chips
// from chat-message-bubble.tsx. Standalone; does NOT import or modify that file.
// -----------------------------------------------------------------------
export function AgentTraceChip({
  toolUsed,
  isLoading,
}: {
  toolUsed: string;
  isLoading?: boolean;
}) {
  const meta = getToolMeta(toolUsed);

  return (
    <div className="mb-3 rounded-lg bg-black/20 p-2.5 border border-border/10 space-y-1.5 text-[11px] font-medium leading-relaxed max-w-sm">
      {isLoading ? (
        <div className="flex items-center gap-2 text-indigo-400">
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
          <span>🧠 Agent is thinking...</span>
        </div>
      ) : (
        <div className={cn("flex items-center gap-2", meta.color)}>
          <span className="text-emerald-500 font-bold">✓</span>
          <span>
            {meta.emoji} {meta.label}
          </span>
        </div>
      )}
    </div>
  );
}

// -----------------------------------------------------------------------
// AgentChatBubble — renders one agent response message.
// A new variant; chat-message-bubble.tsx is not touched.
// -----------------------------------------------------------------------
export function AgentChatBubble({
  query,
  answer,
  toolUsed,
  isLoading,
  createdAt,
}: {
  query: string;
  answer: string;
  toolUsed: string;
  isLoading?: boolean;
  createdAt: string;
}) {
  return (
    <div className="flex w-full flex-col gap-4">
      {/* User query */}
      <article className="flex w-full gap-3 justify-end">
        <div className="flex flex-col items-end max-w-[68%]">
          <div className="px-5 py-3 shadow-sm bg-[var(--bg-message-user)] text-white rounded-[18px_18px_4px_18px] text-sm">
            {query}
          </div>
          <span className="mt-1.5 text-[11px] font-medium text-[var(--text-secondary)] px-1">
            {createdAt}
          </span>
        </div>
        <div className="mt-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 text-xs font-semibold uppercase">
          Y
        </div>
      </article>

      {/* Agent response */}
      <article className="flex w-full gap-3 justify-start">
        <div className="mt-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--assistant-bubble)] border border-[var(--border-color)] text-sm">
          ⚡
        </div>
        <div className="flex flex-col items-start max-w-[72%]">
          <div className="px-5 py-3 shadow-sm bg-[var(--assistant-bubble)] border border-[var(--border-color)] rounded-[18px_18px_18px_4px]">
            {/* Tool trace chip — variant of the existing thinking-state section */}
            <AgentTraceChip toolUsed={toolUsed} isLoading={isLoading} />

            {/* Answer text */}
            {isLoading ? (
              <div className="flex items-center gap-1.5 py-1">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            ) : (
              <p className="text-sm text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed">
                {answer}
              </p>
            )}
          </div>
          <span className="mt-1.5 text-[11px] font-medium text-[var(--text-secondary)] px-1">
            {createdAt}
          </span>
        </div>
      </article>
    </div>
  );
}
