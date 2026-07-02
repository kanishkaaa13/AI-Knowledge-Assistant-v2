export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at?: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type?: string;
  message: string;
}

export interface AuthFormValues {
  name?: string;
  email: string;
  password: string;
}

export interface DashboardSummary {
  title: string;
  description: string;
  stats: Array<{
    label: string;
    value: string;
  }>;
}

export interface AnalyticsMetric {
  label: string;
  value: string;
  detail: string;
}

export interface AnalyticsSeriesPoint {
  label: string;
  value: number;
}

export interface RecentUploadItem {
  id: string;
  title: string;
  file_name: string;
  file_size: number;
  uploaded_at: string;
  status: string;
}

export interface AIUsageStats {
  total_messages: number;
  assistant_messages: number;
  user_messages: number;
  average_messages_per_chat: number;
  local_only_inference: boolean;
  primary_model: string;
}

export interface AnalyticsOverview {
  metrics: AnalyticsMetric[];
  uploads_timeline: AnalyticsSeriesPoint[];
  chats_timeline: AnalyticsSeriesPoint[];
  messages_timeline: AnalyticsSeriesPoint[];
  recent_uploads: RecentUploadItem[];
  ai_usage: AIUsageStats;
}

export interface UploadedDocument {
  id: string;
  user_id: string;
  title: string;
  file_name: string;
  file_extension: string;
  file_path: string | null;
  mime_type: string | null;
  file_size: number | null;
  checksum: string;
  page_count: number | null;
  word_count: number | null;
  status: string;
  extracted_text: string | null;
  ai_summary: string | null;
  tags: string | null;
  parsed_tags: string[];
  is_favorite: boolean;
  processing_error: string | null;
  created_at: string;
  updated_at: string;
  preview_text?: string | null;
}

export interface DocumentListResponse {
  items: UploadedDocument[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentPreview {
  id: string;
  title: string;
  file_name: string;
  file_extension: string;
  mime_type: string | null;
  file_size: number | null;
  page_count: number | null;
  word_count: number | null;
  preview_text: string | null;
  ai_summary: string | null;
  parsed_tags: string[];
  is_favorite: boolean;
}

export interface StoredMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sequence_number: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationListItem {
  id: string;
  user_id: string;
  title: string;
  summary: string | null;
  is_favorite: boolean;
  message_count: number;
  last_message_preview: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: string;
  user_id: string;
  title: string;
  summary: string | null;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
  messages: StoredMessage[];
}

export interface AssistantSummaryResponse {
  summary: string;
  context: string;
}

export interface AssistantQuizItem {
  question: string;
  answer: string;
  difficulty: string;
}

export interface AssistantQuizResponse {
  questions: AssistantQuizItem[];
  context: string;
}

export interface SuggestedPromptsResponse {
  prompts: string[];
}

export interface SemanticDocumentSearchItem {
  document_id: string;
  title: string;
  filename: string;
  excerpt: string;
  score: number;
  tags: string[];
}

export interface Note {
  id: string;
  user_id: string;
  title: string;
  content: string;
  is_pinned: boolean;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export interface NoteCreate {
  title: string;
  content?: string;
  is_pinned?: boolean;
  tags?: string | null;
}

export interface NoteUpdate {
  title?: string;
  content?: string;
  is_pinned?: boolean;
  tags?: string | null;
}

export interface Flashcard {
  id: string;
  user_id: string;
  document_id: string | null;
  front: string;
  back: string;
  difficulty: "easy" | "medium" | "hard";
  is_starred?: boolean;
  tags: string | null;
  source_context: string | null;
  created_at: string;
  updated_at: string;
}

export interface FlashcardCreate {
  front: string;
  back: string;
  difficulty?: "easy" | "medium" | "hard";
  is_starred?: boolean;
  tags?: string | null;
  source_context?: string | null;
  document_id?: string | null;
}

export interface FlashcardUpdate {
  front?: string;
  back?: string;
  difficulty?: "easy" | "medium" | "hard";
  is_starred?: boolean;
  tags?: string | null;
  source_context?: string | null;
}

export interface FlashcardGenerateRequest {
  query?: string;
  document_ids: string[];
  count: number;
  model?: string;
}

export interface OKFRecord {
  id: string;
  source_document_id: string;
  file_path: string;
  type: string;
  title: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface OKFRecordListResponse {
  items: OKFRecord[];
  total: number;
  page: number;
  page_size: number;
}

export interface OKFDocument {
  type: string;
  title: string;
  tags: string[];
  related: string[];
  source_document_id: string | null;
  created_at: string;
  updated_at: string;
  body: string;
}
