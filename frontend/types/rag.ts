export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  document_title: string;
  filename: string;
  page: number | null;
  content: string;
  score: number;
  semantic_score: number;
  keyword_score: number;
  chunk_index: number;
  upload_timestamp: string;
}
