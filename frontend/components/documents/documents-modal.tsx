"use client";

import { DocumentSidebarPanel } from "@/components/documents/document-sidebar-panel";
import { useDocumentLibrary } from "@/hooks/use-documents";
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
  const library = useDocumentLibrary({ page, search, favoritesOnly });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="h-[90vh] max-w-2xl p-0">
        <DocumentSidebarPanel
          documents={library.documents}
          favoritesOnly={favoritesOnly}
          isLoading={library.isLoading}
          page={page}
          pageSize={library.pageSize}
          search={search}
          selectedDocumentIds={selectedDocumentIds}
          total={library.total}
          onFavoritesOnlyChange={onFavoritesOnlyChange}
          onPageChange={onPageChange}
          onSearchChange={onSearchChange}
          onSelectedDocumentIdsChange={onSelectedDocumentIdsChange}
        />
      </DialogContent>
    </Dialog>
  );
}
