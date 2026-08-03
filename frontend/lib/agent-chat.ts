import { env } from "@/lib/env";
import { getAuthToken } from "@/lib/api-client";

export interface AgentChatPayload {
  query: string;
}

export interface AgentChatResult {
  answer: string;
  tool_used: string;
}

/**
 * Call POST /api/v1/agent/chat and return { answer, tool_used }.
 * Uses the same auth pattern as the existing chat-stream.ts.
 */
export async function callAgentChat(
  payload: AgentChatPayload,
  signal?: AbortSignal
): Promise<AgentChatResult> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/agent/chat`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getAuthToken() ?? ""}`,
      },
      body: JSON.stringify(payload),
      signal,
    }
  );

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      errorMessage = body?.detail ?? errorMessage;
    } catch {
      errorMessage = (await response.text()) || errorMessage;
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return {
    answer: data.answer ?? "",
    tool_used: data.tool_used ?? "",
  };
}
