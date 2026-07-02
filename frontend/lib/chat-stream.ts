import { env } from "@/lib/env";

export interface StreamPayload {
  query: string;
  model: string;
  top_k?: number;
  hybrid?: boolean;
  conversation_id?: string;
  document_ids?: string[];
}

export interface StreamHandlers {
  onContext?: (data: any) => void;
  onToken?: (token: string) => void;
  onSuggestions?: (prompts: string[]) => void;
  onThinking?: (step: string, message: string, docs?: string[]) => void;
  onDone?: (data: any) => void;
  onError?: (message: string) => void;
}

export async function streamAssistantChat(
  payload: StreamPayload,
  handlers: StreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/assistant/chat/stream`,
    {
      method: "POST",
      credentials: "include", // send httpOnly access_token cookie
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${typeof window !== "undefined" ? localStorage.getItem("access_token") : ""}`
      },
      body: JSON.stringify(payload),
      signal
    }
  );

  if (!response.ok || !response.body) {
    let errorMessage = `HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      errorMessage = errorBody?.detail ?? errorMessage;
    } catch {
      errorMessage = (await response.text()) || errorMessage;
    }
    throw new Error(errorMessage);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const event of events) {
        const line = event.split("\n").find((entry) => entry.startsWith("data: "));
        if (!line) {
          continue;
        }

        let data: any;
        try {
          data = JSON.parse(line.slice(6));
        } catch {
          console.warn("[stream] Failed to parse SSE event:", line);
          continue;
        }

        switch (data.type) {
          case "context":
            handlers.onContext?.(data);
            break;
          case "thinking":
            handlers.onThinking?.(data.step ?? "", data.message ?? "", data.docs ?? []);
            break;
          case "token":
            handlers.onToken?.(data.content ?? "");
            break;
          case "suggestions":
            handlers.onSuggestions?.(data.prompts ?? []);
            break;
          case "done":
            handlers.onDone?.(data);
            break;
          case "error":
            const errorText = typeof data.message === "string" 
              ? data.message 
              : JSON.stringify(data.message);
            handlers.onError?.(errorText);
            break;
          default:
            break;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
