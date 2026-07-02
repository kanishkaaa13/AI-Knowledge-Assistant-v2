"use client";

import * as React from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RotateCw, X, Loader2, FileText } from "lucide-react";
import { env } from "@/lib/env";

import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

// Configure pdfjs worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs`;

interface PDFViewerPanelProps {
  filename: string;
  initialPage?: number;
  highlightText?: string;
  onClose?: () => void;
}

export function PDFViewerPanel({ filename, initialPage = 1, highlightText, onClose }: PDFViewerPanelProps) {
  const [numPages, setNumPages] = React.useState<number | null>(null);
  const [pageNumber, setPageNumber] = React.useState(initialPage);
  const [scale, setScale] = React.useState(1.0);
  const [rotation, setRotation] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(true);

  // Clean filename to remove path/prefix if any
  const cleanFilename = React.useMemo(() => {
    return filename.split("/").pop() ?? filename;
  }, [filename]);

  const fileUrl = React.useMemo(() => {
    // Construct the backend uploads mount URL
    const baseUrl = env.NEXT_PUBLIC_API_BASE_URL.replace("/api/v1", "");
    return `${baseUrl}/uploads/${cleanFilename}`;
  }, [cleanFilename]);

  React.useEffect(() => {
    if (initialPage) {
      setPageNumber(initialPage);
    }
  }, [initialPage]);

  React.useEffect(() => {
    if (!highlightText) return;
    
    // Set a timeout to wait for the Page text layer to render
    const timer = setTimeout(() => {
      const textLayer = document.querySelector(".react-pdf__Page__textLayer");
      if (!textLayer) return;

      const spans = Array.from(textLayer.querySelectorAll("span"));
      
      // Clean query
      const query = highlightText.toLowerCase().replace(/\s+/g, " ").trim();
      if (!query) return;

      // Find spans that contain the text
      let matchedSpan: HTMLElement | null = null;

      // 1. Try exact or partial match on single span
      for (const span of spans) {
        const text = span.textContent?.toLowerCase().replace(/\s+/g, " ") || "";
        if (text.includes(query) || query.includes(text)) {
          matchedSpan = span;
          break;
        }
      }

      // 2. If not found, try to find a span that starts with the query or has high overlap
      if (!matchedSpan) {
        const queryWords = query.split(" ").slice(0, 3).join(" "); // First few words
        for (const span of spans) {
          const text = span.textContent?.toLowerCase().replace(/\s+/g, " ") || "";
          if (text.includes(queryWords)) {
            matchedSpan = span;
            break;
          }
        }
      }

      if (matchedSpan) {
        // Scroll into view
        matchedSpan.scrollIntoView({ behavior: "smooth", block: "center" });

        // Add highlight styling
        matchedSpan.classList.add("pdf-highlight-flash");
        
        // Remove highlight styling after 4 seconds
        const clearTimer = setTimeout(() => {
          matchedSpan?.classList.remove("pdf-highlight-flash");
        }, 4000);

        return () => clearTimeout(clearTimer);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [pageNumber, highlightText]);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    setIsLoading(false);
  }

  function changePage(offset: number) {
    setPageNumber((prevPageNumber) => {
      const next = prevPageNumber + offset;
      return Math.min(Math.max(1, next), numPages ?? 1);
    });
  }

  return (
    <div className="flex h-full flex-col border border-border/40 bg-[var(--bg-secondary)] rounded-2xl overflow-hidden shadow-2xl">
      {/* Viewer Header */}
      <div className="flex items-center justify-between border-b border-border/40 p-4 bg-[var(--assistant-bubble)] shrink-0">
        <div className="flex items-center gap-2.5 min-w-0">
          <FileText className="h-4 w-4 text-indigo-400 shrink-0" />
          <span className="truncate text-xs font-semibold text-white max-w-[200px]" title={cleanFilename}>
            {cleanFilename}
          </span>
          {numPages && (
            <span className="rounded bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-400 shrink-0">
              Page {pageNumber} of {numPages}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <Button size="icon" variant="ghost" className="h-8 w-8 text-white rounded-lg hover:bg-[var(--border-color)]" onClick={() => setScale(s => Math.max(0.5, s - 0.1))}>
            <ZoomOut className="h-3.5 w-3.5" />
          </Button>
          <Button size="icon" variant="ghost" className="h-8 w-8 text-white rounded-lg hover:bg-[var(--border-color)]" onClick={() => setScale(s => Math.min(2.0, s + 0.1))}>
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
          <Button size="icon" variant="ghost" className="h-8 w-8 text-white rounded-lg hover:bg-[var(--border-color)]" onClick={() => setRotation(r => (r + 90) % 360)}>
            <RotateCw className="h-3.5 w-3.5" />
          </Button>
          {onClose && (
            <>
              <div className="h-4 w-px bg-border/40 mx-0.5" />
              <Button size="icon" variant="ghost" className="h-8 w-8 text-muted-foreground rounded-lg hover:bg-destructive/20 hover:text-destructive" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Main PDF Scroll Container */}
      <div className="flex-1 overflow-auto p-4 flex justify-center bg-[var(--bg-chat)] relative">
        {isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--bg-chat)]/90 z-10 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
            <span className="text-xs text-muted-foreground">Loading PDF Document...</span>
          </div>
        )}

        <Document
          file={fileUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={null}
          className="shadow-lg border border-border/20 rounded-xl overflow-hidden bg-white"
        >
          <Page
            pageNumber={pageNumber}
            scale={scale}
            rotate={rotation}
            renderTextLayer={true}
            renderAnnotationLayer={false}
            loading={null}
          />
        </Document>

        <style dangerouslySetInnerHTML={{__html: `
          @keyframes highlight-flash {
            0% {
              background-color: rgba(234, 179, 8, 0.65);
              box-shadow: 0 0 12px rgba(234, 179, 8, 0.85);
              border-radius: 4px;
            }
            100% {
              background-color: transparent;
              box-shadow: none;
            }
          }
          .pdf-highlight-flash {
            animation: highlight-flash 4.5s ease-out forwards !important;
            mix-blend-mode: multiply;
          }
          .dark .pdf-highlight-flash {
            mix-blend-mode: screen;
          }
          .react-pdf__Page__textLayer {
            opacity: 0.3;
          }
        `}} />
      </div>

      {/* Footer Navigation */}
      {numPages && (
        <div className="flex items-center justify-between border-t border-border/40 p-3 bg-[var(--assistant-bubble)] shrink-0">
          <Button
            size="sm"
            variant="outline"
            disabled={pageNumber <= 1}
            onClick={() => changePage(-1)}
            className="rounded-lg bg-[var(--border-color)] hover:bg-[#333333] text-xs font-semibold border-0 text-white"
          >
            <ChevronLeft className="mr-1 h-3.5 w-3.5" /> Previous
          </Button>

          <span className="text-xs font-semibold text-muted-foreground">
            Page {pageNumber} of {numPages}
          </span>

          <Button
            size="sm"
            variant="outline"
            disabled={pageNumber >= numPages}
            onClick={() => changePage(1)}
            className="rounded-lg bg-[var(--border-color)] hover:bg-[#333333] text-xs font-semibold border-0 text-white"
          >
            Next <ChevronRight className="ml-1 h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  );
}
export default PDFViewerPanel;
