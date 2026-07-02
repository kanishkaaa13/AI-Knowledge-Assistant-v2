"use client";

import { useAutoScroll } from "@/hooks/use-auto-scroll";
import type { ChatMessage } from "@/types/chat";

import { ChatEmptyState } from "@/components/chat/chat-empty-state";
import { ChatMessageBubble } from "@/components/chat/chat-message-bubble";
import { ChatSkeleton } from "@/components/chat/chat-skeleton";

export function ChatThread({
  isLoading,
  messages,
  userName,
  onUsePrompt,
  onCitationClick,
  allDocsCount,
  chatCount
}: {
  isLoading?: boolean;
  messages: ChatMessage[];
  userName: string;
  onUsePrompt?: (prompt: string) => void;
  onCitationClick?: (filename: string, page: number, content: string) => void;
  allDocsCount?: number;
  chatCount?: number;
}) {
  const scrollRef = useAutoScroll<HTMLDivElement>(messages);
  const hasStreamingMessage = messages.some((message) => message.isStreaming);

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
          <ChatSkeleton />
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return <ChatEmptyState onUsePrompt={onUsePrompt} allDocsCount={allDocsCount} chatCount={chatCount} />;
  }

  const hasEmptyStreamingMessage = messages.some((m) => m.isStreaming && m.role !== 'user' && m.content.trim().length === 0);

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 min-h-0">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        {messages.map((message) => (
          <ChatMessageBubble key={message.id} message={message} userName={userName} onCitationClick={onCitationClick} />
        ))}
        {hasStreamingMessage && !hasEmptyStreamingMessage ? <ChatSkeleton /> : null}
        {hasEmptyStreamingMessage && (
          <div className="flex items-center gap-2 px-4 py-2">
            <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{animationDelay:'0ms'}}/>
            <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{animationDelay:'150ms'}}/>
            <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{animationDelay:'300ms'}}/>
          </div>
        )}
      </div>
    </div>
  );
}
