"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  deleteDocument,
  getDocumentPreview,
  listDocuments,
  reindexDocument,
  updateDocumentMetadata,
  uploadDocument
} from "@/lib/api";

export function useDocuments(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  tag?: string;
  favorites_only?: boolean;
}) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: () => listDocuments(params)
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      file,
      title,
      onProgress
    }: {
      file: File;
      title: string;
      onProgress?: (progress: number) => void;
    }) => {
      const doc = await uploadDocument(file, title, onProgress);
      return reindexDocument(doc.id);
    },
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Document uploaded and indexed.");
    },
    onError(error: any) {
      const detail = error?.response?.data?.detail 
        || (error instanceof Error ? error.message : null) 
        || (typeof error === "string" ? error : null);
      
      const message = detail 
        ? (typeof detail === "string" ? detail : JSON.stringify(detail)) 
        : "Upload failed.";
        
      toast.error(message);
    }
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Document deleted.");
    },
    onError(error: any) {
      const detail = error?.response?.data?.detail 
        || (error instanceof Error ? error.message : null) 
        || (typeof error === "string" ? error : null);
      
      const message = detail 
        ? (typeof detail === "string" ? detail : JSON.stringify(detail)) 
        : "Unable to delete document.";
        
      toast.error(message);
    }
  });
}

export function useUpdateDocumentMetadata() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ documentId, tags, is_favorite }: { documentId: string; tags: string[]; is_favorite?: boolean }) =>
      updateDocumentMetadata(documentId, { tags, is_favorite }),
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
    }
  });
}

export function useReindexDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: reindexDocument,
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Re-indexing started.");
    }
  });
}

export function useDocumentPreview(documentId?: string) {
  return useQuery({
    queryKey: ["document-preview", documentId],
    queryFn: () => getDocumentPreview(documentId as string),
    enabled: Boolean(documentId)
  });
}
