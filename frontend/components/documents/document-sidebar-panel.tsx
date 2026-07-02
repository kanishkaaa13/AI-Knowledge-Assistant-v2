"use client";

import * as React from "react";
import { Eye, FileText, Heart, RefreshCcw, Search, Tag, Trash2, UploadCloud } from "lucide-react";

import type { UploadedDocument } from "@/types/api";

import { DocumentPreviewModal } from "@/components/documents/document-preview-modal";
import { DropzoneUploader } from "@/components/documents/dropzone-uploader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDeleteDocument, useReindexDocument, useUpdateDocumentMetadata } from "@/hooks/use-documents";
import { useVirtualList } from "@/hooks/use-virtual-list";

function formatBytes(bytes: number | null) {
  if (!bytes) {
    return "Unknown size";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentSidebarPanel({
  documents,
  favoritesOnly,
  isLoading,
  page,
  pageSize,
  search,
  selectedDocumentIds,
  total,
  onFavoritesOnlyChange,
  onPageChange,
  onSearchChange,
  onSelectedDocumentIdsChange
}: {
  documents: UploadedDocument[];
  favoritesOnly: boolean;
  isLoading: boolean;
  page: number;
  pageSize: number;
  search: string;
  selectedDocumentIds: string[];
  total: number;
  onFavoritesOnlyChange: (value: boolean) => void;
  onPageChange: (page: number) => void;
  onSearchChange: (value: string) => void;
  onSelectedDocumentIdsChange: (ids: string[]) => void;
}) {
  const [previewId, setPreviewId] = React.useState<string | null>(null);
  const deleteMutation = useDeleteDocument();
  const updateMetadataMutation = useUpdateDocumentMetadata();
  const reindexMutation = useReindexDocument();
  const { containerRef, offsetY, totalHeight, visibleItems } = useVirtualList({
    items: documents,
    itemHeight: 210
  });

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  function toggleSelected(documentId: string) {
    onSelectedDocumentIdsChange(
      selectedDocumentIds.includes(documentId)
        ? selectedDocumentIds.filter((id) => id !== documentId)
        : [...selectedDocumentIds, documentId]
    );
  }

  return (
    <>
      <div className="flex h-full min-h-0 flex-col">
        <div className="space-y-4 border-b border-border/60 p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <UploadCloud className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold">Document uploads</p>
              <p className="text-xs text-muted-foreground">Semantic search, tags, favorites</p>
            </div>
          </div>
          <DropzoneUploader />

          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search documents"
                value={search}
                onChange={(event) => {
                  onPageChange(1);
                  onSearchChange(event.target.value);
                }}
              />
            </div>
            <Button
              type="button"
              variant={favoritesOnly ? "default" : "secondary"}
              onClick={() => {
                onPageChange(1);
                onFavoritesOnlyChange(!favoritesOnly);
              }}
            >
              <Heart className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div ref={containerRef} className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="mb-3 rounded-3xl border border-border/60 p-4">
                <div className="h-4 w-2/3 animate-pulse rounded-full bg-secondary" />
                <div className="mt-3 h-3 w-full animate-pulse rounded-full bg-secondary" />
                <div className="mt-2 h-3 w-1/2 animate-pulse rounded-full bg-secondary" />
              </div>
            ))
          ) : documents.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-border/60 p-6 text-center">
              <FileText className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-4 font-medium">No matching documents</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Upload files or adjust the filters to expand your knowledge base.
              </p>
            </div>
          ) : (
            <div style={{ height: totalHeight, position: "relative" }}>
              <div style={{ transform: `translateY(${offsetY}px)` }} className="space-y-3">
                {visibleItems.map((document) => (
                  <article
                    key={document.id}
                    className={`rounded-3xl border p-4 transition ${
                      selectedDocumentIds.includes(document.id)
                        ? "border-primary/50 bg-primary/5"
                        : "border-border/60 bg-card/60"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <button className="min-w-0 text-left" type="button" onClick={() => toggleSelected(document.id)}>
                        <p className="line-clamp-1 text-sm font-medium">{document.title}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                          {document.file_extension.replace(".", "")}
                        </p>
                      </button>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() =>
                            void updateMetadataMutation.mutateAsync({
                              documentId: document.id,
                              tags: document.parsed_tags,
                              is_favorite: !document.is_favorite
                            })
                          }
                        >
                          <Heart
                            className={`h-4 w-4 ${document.is_favorite ? "fill-current text-rose-500" : "text-muted-foreground"}`}
                          />
                        </button>
                        <div className="rounded-full bg-secondary px-2.5 py-1 text-[11px] text-muted-foreground">
                          {document.status}
                        </div>
                      </div>
                    </div>

                    <p className="mt-3 line-clamp-3 text-sm text-muted-foreground">
                      {document.ai_summary ?? document.preview_text ?? "Preview will appear after extraction."}
                    </p>

                    {document.parsed_tags.length > 0 ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {document.parsed_tags.map((tag) => (
                          <span key={tag} className="inline-flex items-center rounded-full bg-secondary px-2 py-1 text-[11px] text-muted-foreground">
                            <Tag className="mr-1 h-3 w-3" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{formatBytes(document.file_size)}</span>
                      <span>{document.word_count ?? 0} words</span>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <Button size="sm" variant="secondary" onClick={() => setPreviewId(document.id)}>
                        <Eye className="mr-1 h-3.5 w-3.5" />
                        Preview
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => void reindexMutation.mutateAsync(document.id)}
                      >
                        <RefreshCcw className="mr-1 h-3.5 w-3.5" />
                        Reindex
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          void deleteMutation.mutateAsync(document.id);
                        }}
                      >
                        <Trash2 className="mr-1 h-3.5 w-3.5" />
                        Delete
                      </Button>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-border/60 p-4 text-sm">
          <span className="text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              Previous
            </Button>
            <Button size="sm" variant="secondary" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
              Next
            </Button>
          </div>
        </div>
      </div>

      <DocumentPreviewModal
        documentId={previewId}
        onOpenChange={(open) => {
          if (!open) {
            setPreviewId(null);
          }
        }}
        open={Boolean(previewId)}
      />
    </>
  );
}
