"use client";

import { Bot, Copy, Search, Brain, FileText } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { ChatMarkdown } from "@/components/chat/chat-markdown";

interface AgentMessageBubbleProps {
  content: string;
  toolUsed: string;
  createdAt: string;
  isStreaming?: boolean;
}

const TOOL_ICONS: Record<string, React.ReactNode> = {
  search_documents: <Search className="h-4 w-4" />,
  summarize_document: <FileText className="h-4 w-4" />,
  answer_general_knowledge: <Brain className="h-4 w-4" />,
};

const TOOL_LABELS: Record<string, string> = {
  search_documents: "🔍 Decided to search documents",
  summarize_document: "📄 Decided to summarize document",
  answer_general_knowledge: "💬 Answered from general knowledge",
};

export function AgentMessageBubble({
  content,
  toolUsed,
  createdAt,
  isStreaming = false,
}: AgentMessageBubbleProps) {
  async function copyMessage() {
    await navigator.clipboard.writeText(content);
    toast.success("Message copied");
  }

  const toolLabel = TOOL_LABELS[toolUsed] || `🔧 Used tool: ${toolUsed}`;
  const toolIcon = TOOL_ICONS[toolUsed] || <Bot className="h-4 w-4" />;

  return (
    <article className="flex w-full gap-3 justify-start">
      <div className="mt-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--assistant-bubble)] border border-[var(--border-color)] text-sm">
        🤖
      </div>

      <div className="flex flex-col items-start max-w-[72%]">
        <div className="group relative px-5 py-3 shadow-sm bg-[var(--assistant-bubble)] border border-[var(--border-color)] rounded-[18px_18px_18px_4px]">
          {/* Agent tool decision trace */}
          {toolUsed && (
            <div className="mb-3 rounded-lg bg-black/20 p-2.5 border border-border/10 text-[11px] font-medium leading-relaxed max-w-sm">
              <div className="flex items-center gap-2 text-indigo-400">
                <span className="text-indigo-400">{toolIcon}</span>
                <span className="text-muted-foreground">{toolLabel}</span>
              </div>
            </div>
          )}

          <ChatMarkdown
            content={content}
            invert={false}
            isStreaming={isStreaming}
            onCitationClick={undefined}
          />
        </div>

        <div className="mt-1.5 flex items-center gap-2 px-1 flex-row">
          <span className="text-[11px] font-medium text-[var(--text-secondary)]">{createdAt}</span>
          <button onClick={() => void copyMessage()} className="text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-secondary)]">
             {isStreaming ? "Streaming" : "Copy"}
          </button>
        </div>
      </div>
    </article>
  );
}
