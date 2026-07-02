"use client";

import * as React from "react";
import { ArrowUp, Mic, Paperclip, Sparkles, StopCircle, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

declare global {
  interface Window {
    webkitSpeechRecognition?: any;
    SpeechRecognition?: any;
  }
}

export function ChatInput({
  input,
  onInputChange,
  onSendMessage,
  streamResponses
}: {
  input: string;
  onInputChange: (value: string) => void;
  onSendMessage: () => Promise<void>;
  streamResponses: boolean;
}) {
  const [isSending, setIsSending] = React.useState(false);
  const [isRecording, setIsRecording] = React.useState(false);
  const recognitionRef = React.useRef<any>(null);

  async function handleSubmit(event?: React.FormEvent) {
    event?.preventDefault();
    if (!input.trim() || isSending) {
      return;
    }

    setIsSending(true);
    try {
      await onSendMessage();
    } finally {
      setIsSending(false);
    }
  }

  function toggleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      return;
    }

    if (isRecording) {
      recognitionRef.current?.stop?.();
      setIsRecording(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0]?.transcript ?? "")
        .join(" ");
      onInputChange(transcript);
    };
    recognition.onend = () => setIsRecording(false);
    recognition.onerror = () => setIsRecording(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
  }

  return (
    <form className="mx-auto flex w-full max-w-4xl items-end gap-2" onSubmit={handleSubmit}>
      <Button
        type="button"
        className="mb-[2px] h-10 w-10 shrink-0 rounded-[10px] border border-[var(--border-color)] bg-[var(--bg-panel)] text-[var(--text-secondary)] hover:bg-[var(--border-color)] hover:text-[var(--text-primary)]"
        variant="ghost"
        title="Attach Document"
      >
        <Paperclip className="h-4 w-4" />
      </Button>

      <div className="flex-1 rounded-[12px] border border-[var(--border-color)] bg-[var(--input-bg)] overflow-hidden">
        <Textarea
          id="chat-input"
          className="max-h-[120px] min-h-[44px] w-full resize-none border-0 bg-transparent px-4 py-3 text-sm text-[var(--text-primary)] shadow-none focus-visible:ring-0 placeholder:text-[var(--text-secondary)]"
          style={{ resize: 'none', maxHeight: '120px', overflowY: 'auto' }}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void handleSubmit();
            }
          }}
          placeholder="Message your knowledge assistant..."
          value={input}
          rows={1}
        />
      </div>

      <Button
        type="submit"
        disabled={isSending || !input.trim()}
        className="mb-[2px] h-10 w-10 shrink-0 rounded-[10px] bg-[var(--bg-message-user)] p-0 text-white hover:opacity-90"
      >
        {isSending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <ArrowUp className="h-5 w-5" />
        )}
      </Button>
    </form>
  );
}
