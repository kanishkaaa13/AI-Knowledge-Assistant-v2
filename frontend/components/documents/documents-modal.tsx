"use client";

import { DocumentSidebarPanel } from "@/components/documents/document-sidebar-panel";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useDocuments } from "@/hooks/use-documents";
import { Dialog, DialogContent } from "@/components/ui/dialog";

export function DocumentsModal({
  favoritesOnly,
  onFavoritesOnlyChange,
  onOpenChange,
  onPageChange,
  onSearchChange,
  onSelectedDocumentIdsChange,
  open,
  page,
  search,
  selectedDocumentIds
}: {
  favoritesOnly: boolean;
  onFavoritesOnlyChange: (value: boolean) => void;
  onOpenChange: (open: boolean) => void;
  onPageChange: (page: number) => void;
  onSearchChange: (value: string) => void;
  onSelectedDocumentIdsChange: (ids: string[]) => void;
  open: boolean;
  page: number;
  search: string;
  selectedDocumentIds: string[];
}) {
  const debouncedSearch = useDebouncedValue(search, 250);
  const documentsQuery = useDocuments({
    page,
    page_size: 12,
    search: debouncedSearch || undefined,
    favorites_only: favoritesOnly
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="h-[90vh] max-w-2xl p-0">
        <DocumentSidebarPanel
          documents={documentsQuery.data?.items ?? []}
          favoritesOnly={favoritesOnly}
          isLoading={documentsQuery.isLoading}
          page={page}
          pageSize={documentsQuery.data?.page_size ?? 12}
          search={search}
          selectedDocumentIds={selectedDocumentIds}
          total={documentsQuery.data?.total ?? 0}
          onFavoritesOnlyChange={onFavoritesOnlyChange}
          onPageChange={onPageChange}
          onSearchChange={onSearchChange}
          onSelectedDocumentIdsChange={onSelectedDocumentIdsChange}
        />
      </DialogContent>
    </Dialog>
  );
}
