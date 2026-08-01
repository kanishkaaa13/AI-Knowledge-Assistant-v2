"use client";

import * as React from "react";
import { ArrowUp, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { AgentChatBubble } from "@/components/chat/agent-chat-bubble";
import { callAgentChat } from "@/lib/agent-chat";

// -----------------------------------------------------------------------
// Local message shape — completely independent from the main chat state.
// -----------------------------------------------------------------------
interface AgentMessage {
  id: string;
  query: string;
  answer: string;
  toolUsed: string;
  createdAt: string;
}

// -----------------------------------------------------------------------
// AgentChatPanel — a self-contained panel that hits /agent/chat.
// It owns its own local state and never touches the main chat messages,
// onSendMessage, or any existing chat state.
// -----------------------------------------------------------------------
export function AgentChatPanel() {
  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState<AgentMessage[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [pendingQuery, setPendingQuery] = React.useState<string | null>(null);
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const abortRef = React.useRef<AbortController | null>(null);

  // Auto-scroll to bottom on new message
  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  async function handleSend() {
    const query = input.trim();
    if (!query || isLoading) return;

    setInput("");
    setIsLoading(true);
    setPendingQuery(query);

    abortRef.current = new AbortController();

    try {
      const result = await callAgentChat({ query }, abortRef.current.signal);
      const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}`,
          query,
          answer: result.answer,
          toolUsed: result.tool_used,
          createdAt: now,
        },
      ]);
    } catch (err: any) {
      if (err?.name === "AbortError") return;
      const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}`,
          query,
          answer: `⚠️ Error: ${err?.message ?? "Unknown error"}`,
          toolUsed: "",
          createdAt: now,
        },
      ]);
    } finally {
      setIsLoading(false);
      setPendingQuery(null);
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header badge */}
      <div className="flex-shrink-0 border-b border-[var(--border-color)] px-6 py-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-widest text-indigo-400">
          ⚡ Agent Mode
        </span>
        <span className="rounded-full bg-indigo-600/20 px-2 py-0.5 text-[10px] font-medium text-indigo-400">
          LangGraph ReAct
        </span>
        <span className="ml-auto text-[10px] text-muted-foreground">
          Agent picks the right tool automatically
        </span>
      </div>

      {/* Message list */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 min-h-0"
      >
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-8">
          {messages.length === 0 && !isLoading && (
            <div className="mt-20 flex flex-col items-center gap-3 text-center text-muted-foreground">
              <span className="text-4xl">⚡</span>
              <p className="text-sm font-medium text-white">Ask anything — the agent decides how to answer</p>
              <p className="text-xs max-w-xs leading-relaxed">
                It will search your documents, summarize them, or answer from general knowledge depending on your question.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <AgentChatBubble
              key={msg.id}
              query={msg.query}
              answer={msg.answer}
              toolUsed={msg.toolUsed}
              createdAt={msg.createdAt}
            />
          ))}

          {/* Pending bubble — shown while loading */}
          {isLoading && pendingQuery && (
            <AgentChatBubble
              query={pendingQuery}
              answer=""
              toolUsed=""
              isLoading
              createdAt={new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            />
          )}
        </div>
      </div>

      {/* Input bar — same visual style as ChatInput, own state */}
      <div className="border-t border-[var(--border-color)] bg-[var(--bg-panel)] p-4 flex-shrink-0 sticky bottom-0">
        <form
          className="mx-auto flex w-full max-w-4xl items-end gap-2"
          onSubmit={(e) => { e.preventDefault(); void handleSend(); }}
        >
          <div className="flex-1 rounded-[12px] border border-[var(--border-color)] bg-[var(--input-bg)] overflow-hidden">
            <Textarea
              className="max-h-[120px] min-h-[44px] w-full resize-none border-0 bg-transparent px-4 py-3 text-sm text-[var(--text-primary)] shadow-none focus-visible:ring-0 placeholder:text-[var(--text-secondary)]"
              style={{ resize: "none", maxHeight: "120px", overflowY: "auto" }}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void handleSend();
                }
              }}
              placeholder="Ask the agent anything…"
              rows={1}
            />
          </div>
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="mb-[2px] h-10 w-10 shrink-0 rounded-[10px] bg-[var(--bg-message-user)] p-0 text-white hover:opacity-90"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowUp className="h-5 w-5" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
