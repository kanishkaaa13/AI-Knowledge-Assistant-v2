"use client";

import * as React from "react";
import { FileUp, X, Loader2 } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import { useUploadDocument } from "@/hooks/use-documents";

const allowedExtensions = [".pdf", ".docx", ".txt", ".md"];

type QueueItem = {
  id: string;
  file: File;
  progress: number;
  status: "queued" | "uploading" | "indexing" | "Ready" | "error";
};

function createQueueItem(file: File): QueueItem {
  return {
    id: `${file.name}-${file.lastModified}`,
    file,
    progress: 0,
    status: "queued"
  };
}

export function DropzoneUploader() {
  const [isDragging, setIsDragging] = React.useState(false);
  const [queue, setQueue] = React.useState<QueueItem[]>([]);
  const uploadMutation = useUploadDocument();
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  const uploadFiles = React.useCallback(
    async (files: File[]) => {
      const filtered = files.filter((file) =>
        allowedExtensions.some((extension) => file.name.toLowerCase().endsWith(extension))
      );

      const queued = filtered.map(createQueueItem);
      setQueue((current) => [...queued, ...current]);

      for (const item of queued) {
        setQueue((current) =>
          current.map((entry) =>
            entry.id === item.id ? { ...entry, status: "uploading", progress: 0 } : entry
          )
        );

        try {
          await uploadMutation.mutateAsync({
            file: item.file,
            title: item.file.name.replace(/\.[^.]+$/, ""),
            onProgress(progress) {
              setQueue((current) =>
                current.map((entry) =>
                  entry.id === item.id ? { ...entry, progress, status: progress === 100 ? "indexing" : entry.status } : entry
                )
              );
            }
          });

          setQueue((current) =>
            current.map((entry) =>
              entry.id === item.id ? { ...entry, status: "Ready", progress: 100 } : entry
            )
          );
        } catch {
          setQueue((current) =>
            current.map((entry) =>
              entry.id === item.id ? { ...entry, status: "error" } : entry
            )
          );
        }
      }
    },
    [uploadMutation]
  );

  const onDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const files = Array.from(event.dataTransfer.files);
    await uploadFiles(files);
  };

  return (
    <div className="space-y-4">
      <div
        className={`rounded-3xl border border-dashed p-5 text-center transition ${
          isDragging ? "border-primary bg-primary/10" : "border-border/60 bg-secondary/40"
        }`}
        onClick={() => fileInputRef.current?.click()}
        onDragEnter={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setIsDragging(false);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => void onDrop(event)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={0}
      >
        <FileUp className="mx-auto h-8 w-8 text-primary" />
        <p className="mt-3 text-sm font-medium">Drop documents here or click to upload</p>
        <p className="mt-2 text-xs text-muted-foreground">
          Supports PDF, DOCX, TXT, and Markdown up to 10 MB.
        </p>
        <input
          ref={fileInputRef}
          multiple
          accept=".pdf,.docx,.txt,.md,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="hidden"
          onChange={(event) => {
            const files = Array.from(event.target.files ?? []);
            void uploadFiles(files);
            event.target.value = "";
          }}
          type="file"
        />
      </div>

      {queue.length > 0 ? (
        <div className="space-y-3">
          {queue.map((item) => (
            <div key={item.id} className="rounded-2xl border border-border/60 bg-card/60 p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{item.file.name}</p>
                  <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                    {item.status === "indexing" && <Loader2 className="h-3 w-3 animate-spin" />}
                    {item.status === "indexing" ? "Indexing..." : item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                  </p>
                </div>
                <button
                  className="rounded-full p-1 text-muted-foreground transition hover:bg-secondary"
                  onClick={() =>
                    setQueue((current) => current.filter((entry) => entry.id !== item.id))
                  }
                  type="button"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <Progress className="mt-3" value={item.progress} />
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
