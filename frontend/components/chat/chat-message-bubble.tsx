"use client";

import { Bot, Check, Copy, User2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types/chat";

import { ChatMarkdown } from "@/components/chat/chat-markdown";

export function ChatMessageBubble({
  message,
  userName,
  onCitationClick
}: {
  message: ChatMessage;
  userName: string;
  onCitationClick?: (filename: string, page: number, content: string) => void;
}) {
  const isUser = message.role === "user";
  const isError = !isUser && typeof message.content === 'string' && (message.content.startsWith('{"detail":') || message.content.startsWith("⚠️ Error:"));

  async function copyMessage() {
    await navigator.clipboard.writeText(message.content);
    toast.success("Message copied");
  }

  const handleCitationClick = (filename: string, page: number, paragraph: number) => {
    if (onCitationClick) {
      const match = (message.citations || []).find((c: any) => {
        const cFile = c.filename?.split("/").pop()?.toLowerCase();
        const targetFile = filename.split("/").pop()?.toLowerCase();
        return cFile === targetFile && c.page === page && c.paragraph_index === paragraph;
      });
      const highlightContent = match ? match.content : "";
      onCitationClick(filename, page, highlightContent);
    }
  };

  if (isError) {
    const errorText = message.content.replace(/^⚠️ Error: /, "").replace(/^\{"detail":\s*"(.*)"\}$/, "$1");
    return (
      <article className="flex gap-4 justify-start">
        <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
          <Bot className="h-5 w-5" />
        </div>
        <div className="max-w-3xl rounded-[2rem] border border-destructive/30 bg-destructive/5 px-5 py-4 shadow-sm">
          <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.24em] text-destructive">
            <Bot className="h-3.5 w-3.5" />
            Error
          </div>
          <div className="text-sm text-destructive/90">{errorText}</div>
          <div className="mt-4 flex items-center justify-between gap-3 text-xs text-muted-foreground">
            <span>{message.createdAt}</span>
          </div>
        </div>
      </article>
    );
  }

  if (!isUser && message.content.trim().length === 0 && !message.thinkingState) {
    return null;
  }

  return (
    <article className={cn("flex w-full gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="mt-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--assistant-bubble)] border border-[var(--border-color)] text-sm">
          🤖
        </div>
      )}

      <div className={cn("flex flex-col", isUser ? "items-end max-w-[68%]" : "items-start max-w-[72%]")}>
        <div
          className={cn(
            "group relative px-5 py-3 shadow-sm",
            isUser
              ? "bg-[var(--bg-message-user)] text-white rounded-[18px_18px_4px_18px]"
              : "bg-[var(--assistant-bubble)] border border-[var(--border-color)] rounded-[18px_18px_18px_4px]"
          )}
        >
          {/* Render thinking process if present */}
          {!isUser && message.thinkingState && message.thinkingState.step !== 'done' && (
            <div className="mb-3 rounded-lg bg-black/20 p-2.5 border border-border/10 space-y-1.5 text-[11px] font-medium leading-relaxed max-w-sm">
              {message.thinkingState.step === 'searching' && (
                <div className="flex items-center gap-2 text-indigo-400">
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
                  <span>🧠 Searching documents...</span>
                </div>
              )}
              {message.thinkingState.step === 'reading' && (
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2 text-indigo-400">
                    <span className="text-emerald-500 font-bold">✓</span>
                    <span className="text-muted-foreground">Searched documents</span>
                  </div>
                  <div className="flex items-center gap-2 text-indigo-400">
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
                    <span>📄 {message.thinkingState.message}</span>
                  </div>
                </div>
              )}
              {message.thinkingState.step === 'generating' && (
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2 text-indigo-400">
                    <span className="text-emerald-500 font-bold">✓</span>
                    <span className="text-muted-foreground">Searched documents</span>
                  </div>
                  <div className="flex items-center gap-2 text-indigo-400">
                    <span className="text-emerald-500 font-bold">✓</span>
                    <span className="text-muted-foreground">Read matching context</span>
                  </div>
                  <div className="flex items-center gap-2 text-indigo-400">
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
                    <span>🤖 Generating answer...</span>
                  </div>
                </div>
              )}
            </div>
          )}

          <ChatMarkdown
            content={message.content}
            invert={isUser}
            isStreaming={message.isStreaming}
            onCitationClick={handleCitationClick}
          />
        </div>

        {/* Render citation cards below assistant message if citations are present */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-2.5 flex flex-wrap gap-2">
            {message.citations.map((cit: any, idx: number) => (
              <button
                key={cit.chunk_id || idx}
                onClick={() => {
                  if (onCitationClick) {
                    onCitationClick(cit.filename, cit.page, cit.content);
                  }
                }}
                className="flex items-center gap-2 rounded-xl bg-[var(--bg-panel)] border border-[var(--border-color)] p-2 hover:bg-[var(--border-color)] transition text-left max-w-[180px] shrink-0"
              >
                <div className="h-6 w-6 rounded bg-indigo-500/10 flex items-center justify-center text-indigo-400 text-xs shrink-0">
                  📄
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] font-semibold text-white truncate">
                    {cit.filename?.split("/").pop()}
                  </p>
                  <p className="text-[9px] text-muted-foreground">
                    Page {cit.page || 1} • Para {cit.paragraph_index || 1}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}

        <div className={cn("mt-1.5 flex items-center gap-2 px-1", isUser ? "flex-row-reverse" : "flex-row")}>
          <span className="text-[11px] font-medium text-[var(--text-secondary)]">{message.createdAt}</span>
          <button onClick={() => void copyMessage()} className="text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-secondary)]">
             {message.isStreaming ? "Streaming" : "Copy"}
          </button>
        </div>
      </div>

      {isUser && (
        <div className="mt-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 text-xs font-semibold uppercase">
          {userName.charAt(0) || "U"}
        </div>
      )}
    </article>
  );
}
