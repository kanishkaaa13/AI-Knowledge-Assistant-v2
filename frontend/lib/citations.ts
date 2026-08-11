import type { Citation } from "@/types/chat";

interface RawCitationChunk {
  content?: string;
  metadata?: {
    chunk_id?: string;
    document_id?: string;
    filename?: string;
    page?: string | number;
    chunk_index?: number;
    paragraph_index?: string | number;
  };
}

/** Normalize backend context/citation chunks into the chat Citation shape. */
export function mapCitations(chunks: RawCitationChunk[] | null | undefined): Citation[] {
  return (chunks ?? []).map((chunk) => ({
    chunk_id: chunk.metadata?.chunk_id || "",
    document_id: chunk.metadata?.document_id || "",
    filename: chunk.metadata?.filename || "Unknown Document",
    page: chunk.metadata?.page ? Number.parseInt(String(chunk.metadata.page), 10) : 1,
    chunk_index: chunk.metadata?.chunk_index ?? 0,
    paragraph_index: chunk.metadata?.paragraph_index
      ? Number.parseInt(String(chunk.metadata.paragraph_index), 10)
      : 1,
    content: chunk.content || ""
  }));
}
