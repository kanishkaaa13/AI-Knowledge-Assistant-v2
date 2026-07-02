import { apiClient } from "@/lib/api-client";
import {
  AuthFormValues,
  AuthResponse,
  AnalyticsOverview,
  AssistantQuizResponse,
  AssistantSummaryResponse,
  ConversationDetail,
  ConversationListItem,
  DocumentListResponse,
  DocumentPreview,
  DashboardSummary,
  HealthResponse,
  SemanticDocumentSearchItem,
  SuggestedPromptsResponse,
  UploadedDocument,
  User,
  Note,
  NoteCreate,
  NoteUpdate,
  Flashcard,
  FlashcardCreate,
  FlashcardUpdate,
  FlashcardGenerateRequest,
  OKFRecordListResponse,
  OKFDocument
} from "@/types/api";
import type { RetrievedChunk } from "@/types/rag";

export async function getHealth() {
  const { data } = await apiClient.get<HealthResponse>("/health");
  return data;
}

export async function getDashboardSummary() {
  const { data } = await apiClient.get<DashboardSummary>("/assistant/summary");
  return data;
}

export async function getAnalyticsOverview() {
  const { data } = await apiClient.get<AnalyticsOverview>("/assistant/analytics");
  return data;
}

export async function login(payload: AuthFormValues) {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", payload);
  return data;
}

export async function register(payload: AuthFormValues) {
  const { data } = await apiClient.post<AuthResponse>("/auth/register", payload);
  return data;
}

export async function logout() {
  const { data } = await apiClient.post<{ message: string }>("/auth/logout");
  return data;
}

export async function getCurrentUser() {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}

export async function refreshSession() {
  const { data } = await apiClient.post<AuthResponse>("/auth/refresh");
  return data;
}

export async function listDocuments(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  tag?: string;
  favorites_only?: boolean;
}) {
  const { data } = await apiClient.get<DocumentListResponse>("/documents", {
    params
  });
  return data;
}

export async function uploadDocument(
  file: File,
  title: string,
  onProgress?: (progress: number) => void
) {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);

  const { data } = await apiClient.post<UploadedDocument>("/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    },
    onUploadProgress(progressEvent) {
      if (!progressEvent.total || !onProgress) {
        return;
      }
      onProgress(Math.round((progressEvent.loaded / progressEvent.total) * 100));
    }
  });

  return data;
}

export async function deleteDocument(documentId: string) {
  const { data } = await apiClient.delete<{ message: string }>(`/documents/${documentId}`);
  return data;
}

export async function getDocumentPreview(documentId: string) {
  const { data } = await apiClient.get<DocumentPreview>(`/documents/${documentId}/preview`);
  return data;
}

export async function updateDocumentMetadata(
  documentId: string,
  payload: { tags: string[]; is_favorite?: boolean }
) {
  const { data } = await apiClient.patch<UploadedDocument>(`/documents/${documentId}/metadata`, payload);
  return data;
}

export async function reindexDocument(documentId: string) {
  const { data } = await apiClient.post<UploadedDocument>(`/documents/${documentId}/reindex`);
  return data;
}

export async function listConversations(params?: {
  search?: string;
  is_favorite?: boolean;
  date_from?: string;
  date_to?: string;
}) {
  const { data } = await apiClient.get<ConversationListItem[]>("/conversations", {
    params: params
  });
  return data;
}

export async function pinConversation(conversationId: string, isPinned: boolean) {
  const { data } = await apiClient.patch<ConversationListItem>(`/conversations/${conversationId}/pin`, {
    is_pinned: isPinned
  });
  return data;
}

export async function getConversation(conversationId: string) {
  const { data } = await apiClient.get<ConversationDetail>(`/conversations/${conversationId}`);
  return data;
}

export async function createConversation(payload?: {
  title?: string;
  initial_message?: string;
}) {
  const { data } = await apiClient.post<ConversationDetail>("/conversations", payload ?? {});
  return data;
}

export async function renameConversation(conversationId: string, title: string) {
  const { data } = await apiClient.patch<ConversationListItem>(`/conversations/${conversationId}`, {
    title
  });
  return data;
}

export async function favoriteConversation(conversationId: string, is_favorite: boolean) {
  const { data } = await apiClient.patch<ConversationListItem>(`/conversations/${conversationId}/favorite`, {
    is_favorite
  });
  return data;
}

export async function exportConversation(conversationId: string) {
  const { data } = await apiClient.get<string>(`/conversations/${conversationId}/export`, {
    responseType: "text" as const
  });
  return data;
}

export async function deleteConversation(conversationId: string) {
  const { data } = await apiClient.delete<{ message: string }>(`/conversations/${conversationId}`);
  return data;
}

export async function queryAssistant(payload: {
  query: string;
  model: string;
  top_k?: number;
  hybrid?: boolean;
  conversation_id?: string;
  document_ids?: string[];
}) {
  const { data } = await apiClient.post<{
    query: string;
    answer: string;
    context: string;
    chunks: RetrievedChunk[];
    prompt: string;
    model: string;
    conversation_id: string;
    conversation_title: string;
  }>("/assistant/query", payload);
  return data;
}

export async function summarizeAssistantKnowledge(payload: {
  query?: string | null;
  model: string;
  document_ids?: string[];
}) {
  const { data } = await apiClient.post<AssistantSummaryResponse>("/assistant/summaries", payload);
  return data;
}

export async function generateAssistantQuiz(payload: {
  query?: string | null;
  model: string;
  document_ids?: string[];
}) {
  const { data } = await apiClient.post<AssistantQuizResponse>("/assistant/quiz", payload);
  return data;
}

export async function getSuggestedPrompts(payload: {
  query: string;
  model: string;
  document_ids?: string[];
}) {
  const { data } = await apiClient.post<SuggestedPromptsResponse>("/assistant/suggested-prompts", payload);
  return data;
}

export async function semanticDocumentSearch(payload: {
  query: string;
  model: "llama3" | "mistral";
  document_ids?: string[];
}) {
  const { data } = await apiClient.post<{ results: SemanticDocumentSearchItem[] }>(
    "/assistant/document-search",
    payload
  );
  return data;
}

// ==========================================
// NOTES API
// ==========================================

export async function listNotes(params?: { search?: string; pinned_only?: boolean }) {
  const { data } = await apiClient.get<Note[]>("/notes", { params });
  return data;
}

export async function createNote(payload: NoteCreate) {
  const { data } = await apiClient.post<Note>("/notes", payload);
  return data;
}

export async function getNote(noteId: string) {
  const { data } = await apiClient.get<Note>(`/notes/${noteId}`);
  return data;
}

export async function updateNote(noteId: string, payload: NoteUpdate) {
  const { data } = await apiClient.patch<Note>(`/notes/${noteId}`, payload);
  return data;
}

export async function deleteNote(noteId: string) {
  await apiClient.delete(`/notes/${noteId}`);
}

export async function togglePinNote(noteId: string) {
  const { data } = await apiClient.post<Note>(`/notes/${noteId}/pin`);
  return data;
}

// ==========================================
// FLASHCARDS API
// ==========================================

export async function listFlashcards(documentId?: string) {
  const { data } = await apiClient.get<Flashcard[]>("/flashcards", {
    params: documentId ? { document_id: documentId } : undefined
  });
  return data;
}

export async function createFlashcard(payload: FlashcardCreate) {
  const { data } = await apiClient.post<Flashcard>("/flashcards", payload);
  return data;
}

export async function generateFlashcards(payload: FlashcardGenerateRequest) {
  const { data } = await apiClient.post<Flashcard[]>("/flashcards/generate", payload);
  return data;
}

export async function updateFlashcard(cardId: string, payload: FlashcardUpdate) {
  const { data } = await apiClient.patch<Flashcard>(`/flashcards/${cardId}`, payload);
  return data;
}

export async function deleteFlashcard(cardId: string) {
  await apiClient.delete(`/flashcards/${cardId}`);
}

export async function generateStudyNotes(payload: { query: string; model: string; document_ids: string[] }) {
  const { data } = await apiClient.post<{ notes: string; context: string; chunks: any[] }>("/assistant/notes", payload);
  return data;
}

export async function listOKFRecords(params?: {
  type?: string;
  tag?: string;
  page?: number;
  page_size?: number;
}) {
  const { data } = await apiClient.get<OKFRecordListResponse>("/okf", { params });
  return data;
}

export async function getOKFDocument(recordId: string) {
  const { data } = await apiClient.get<OKFDocument>(`/okf/${recordId}`);
  return data;
}


