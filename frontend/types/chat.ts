export type ChatRole = "user" | "assistant" | "system";

export interface Citation {
  chunk_id?: string;
  document_id: string;
  filename: string;
  page: number;
  chunk_index: number;
  content: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  sequenceNumber?: number;
  isStreaming?: boolean;
  citations?: Citation[];
  suggestions?: string[];
  thinkingState?: {
    step: string;
    message: string;
    docs?: string[];
  };
}

export interface ConversationPreview {
  id: string;
  title: string;
  summary: string | null;
  updatedAt: string;
  createdAt: string;
  isFavorite: boolean;
  messageCount: number;
  lastMessagePreview?: string | null;
}

export interface ConversationDetail extends ConversationPreview {
  userId: string;
  messages: ChatMessage[];
}

export interface AssistantSettings {
  theme: "light" | "dark" | "oled" | "purple" | "blue" | "system";
  model: string;
  webSearch: boolean;
  streamResponses: boolean;
}

export interface ConversationGroup {
  label: string;
  conversations: ConversationPreview[];
}

export interface AssistantWorkspaceState {
  selectedDocumentIds: string[];
  suggestedPrompts: string[];
  generatedSummary: string | null;
}
