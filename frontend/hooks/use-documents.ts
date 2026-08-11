"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { extractErrorMessage } from "@/lib/errors";

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

export const DOCUMENT_LIBRARY_PAGE_SIZE = 12;

/** Debounced, paginated document listing shared by the sidebar panel and its modal. */
export function useDocumentLibrary({
  page,
  search,
  favoritesOnly,
  pageSize = DOCUMENT_LIBRARY_PAGE_SIZE
}: {
  page: number;
  search: string;
  favoritesOnly: boolean;
  pageSize?: number;
}) {
  const debouncedSearch = useDebouncedValue(search, 250);
  const query = useDocuments({
    page,
    page_size: pageSize,
    search: debouncedSearch || undefined,
    favorites_only: favoritesOnly
  });

  return {
    documents: query.data?.items ?? [],
    isLoading: query.isLoading,
    pageSize: query.data?.page_size ?? pageSize,
    total: query.data?.total ?? 0
  };
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
    onError(error: unknown) {
      toast.error(extractErrorMessage(error, "Upload failed."));
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
    onError(error: unknown) {
      toast.error(extractErrorMessage(error, "Unable to delete document."));
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
