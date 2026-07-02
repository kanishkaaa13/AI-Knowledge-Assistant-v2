"use client";

import { ExternalLink, FileText } from "lucide-react";

import { env } from "@/lib/env";
import { useDocumentPreview } from "@/hooks/use-documents";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";

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

export function DocumentPreviewModal({
  documentId,
  onOpenChange,
  open
}: {
  documentId: string | null;
  onOpenChange: (open: boolean) => void;
  open: boolean;
}) {
  const previewQuery = useDocumentPreview(documentId ?? undefined);
  const preview = previewQuery.data;
  const isPdf = preview?.file_extension === ".pdf";
  const downloadUrl = documentId
    ? `${env.NEXT_PUBLIC_API_BASE_URL}/documents/${documentId}/download`
    : null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>{preview?.title ?? "Document preview"}</DialogTitle>
          <DialogDescription>
            Review extracted text and metadata from the uploaded file.
          </DialogDescription>
        </DialogHeader>

        {previewQuery.isLoading ? (
          <div className="space-y-3">
            <div className="h-4 w-40 animate-pulse rounded-full bg-secondary" />
            <div className="h-4 w-full animate-pulse rounded-full bg-secondary" />
            <div className="h-4 w-5/6 animate-pulse rounded-full bg-secondary" />
          </div>
        ) : preview ? (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span>{preview.file_name}</span>
              <span>{formatBytes(preview.file_size)}</span>
              <span>{preview.word_count ?? 0} words</span>
              {preview.page_count ? <span>{preview.page_count} pages</span> : null}
            </div>

            {preview.ai_summary ? (
              <div className="rounded-3xl border border-border/60 bg-card/70 p-5">
                <p className="text-sm font-medium">AI summary</p>
                <p className="mt-3 whitespace-pre-wrap text-sm text-muted-foreground">
                  {preview.ai_summary}
                </p>
              </div>
            ) : null}

            {preview.parsed_tags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {preview.parsed_tags.map((tag) => (
                  <span key={tag} className="rounded-full bg-secondary px-3 py-1 text-xs text-muted-foreground">
                    {tag}
                  </span>
                ))}
              </div>
            ) : null}

            {isPdf && downloadUrl ? (
              <div className="overflow-hidden rounded-3xl border border-border/60">
                <iframe className="h-[420px] w-full" src={downloadUrl} title={preview.title} />
              </div>
            ) : null}

            <div className="rounded-3xl border border-border/60 bg-card/70 p-5">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  <p className="text-sm font-medium">Extracted preview</p>
                </div>
                {downloadUrl ? (
                  <Button asChild size="sm" variant="secondary">
                    <a href={downloadUrl} rel="noreferrer" target="_blank">
                      <ExternalLink className="mr-1 h-3.5 w-3.5" />
                      Open file
                    </a>
                  </Button>
                ) : null}
              </div>
              <pre className="max-h-[320px] overflow-auto whitespace-pre-wrap text-sm text-muted-foreground">
                {preview.preview_text ?? "No preview available for this file yet."}
              </pre>
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
