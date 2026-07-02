"use client";

import { FileText } from "lucide-react";
import type { Citation } from "@/types/chat";

interface CitationCardProps {
  citation: Citation;
  onClick?: (citation: Citation) => void;
}

export function CitationCard({ citation, onClick }: CitationCardProps) {
  const { filename, page, chunk_index } = citation;

  return (
    <button
      onClick={() => onClick?.(citation)}
      className="flex items-center gap-2 rounded-lg border border-border/40 bg-[var(--border-color)] px-3 py-1.5 text-left text-xs transition hover:bg-[#333333] hover:text-white text-muted-foreground max-w-full"
      title={`${filename} (Page ${page})`}
      type="button"
    >
      <FileText className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
      <span className="truncate flex-1 max-w-[150px] font-medium text-white/95">
        {filename}
      </span>
      <span className="shrink-0 bg-indigo-500/10 text-indigo-400 px-1.5 py-0.5 rounded text-[10px] font-semibold">
        Page {page}
      </span>
    </button>
  );
}
