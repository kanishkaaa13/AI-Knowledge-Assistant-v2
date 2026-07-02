"use client";

import * as React from "react";
import { PanelRightOpen } from "lucide-react";

import { DocumentsModal } from "@/components/documents/documents-modal";
import { DocumentSidebarPanel } from "@/components/documents/document-sidebar-panel";
import { Button } from "@/components/ui/button";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useDocuments } from "@/hooks/use-documents";

export function DocumentManager({
  selectedDocumentIds,
  onSelectedDocumentIdsChange
}: {
  selectedDocumentIds: string[];
  onSelectedDocumentIdsChange: (ids: string[]) => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [favoritesOnly, setFavoritesOnly] = React.useState(false);
  const debouncedSearch = useDebouncedValue(search, 250);

  const documentsQuery = useDocuments({
    page,
    page_size: 12,
    search: debouncedSearch || undefined,
    favorites_only: favoritesOnly
  });

  return (
    <>
      <div className="hidden 2xl:flex 2xl:w-[380px] 2xl:flex-col 2xl:border-l 2xl:border-border/60 2xl:bg-card/30">
        <DocumentSidebarPanel
          documents={documentsQuery.data?.items ?? []}
          favoritesOnly={favoritesOnly}
          isLoading={documentsQuery.isLoading}
          page={page}
          pageSize={documentsQuery.data?.page_size ?? 12}
          search={search}
          selectedDocumentIds={selectedDocumentIds}
          total={documentsQuery.data?.total ?? 0}
          onFavoritesOnlyChange={setFavoritesOnly}
          onPageChange={setPage}
          onSearchChange={setSearch}
          onSelectedDocumentIdsChange={onSelectedDocumentIdsChange}
        />
      </div>

      <div className="fixed bottom-5 right-5 z-30 2xl:hidden">
        <Button className="rounded-full px-5 shadow-xl" onClick={() => setOpen(true)}>
          <PanelRightOpen className="mr-2 h-4 w-4" />
          Documents
        </Button>
      </div>

      <DocumentsModal
        favoritesOnly={favoritesOnly}
        onFavoritesOnlyChange={setFavoritesOnly}
        onOpenChange={setOpen}
        onPageChange={setPage}
        onSearchChange={setSearch}
        onSelectedDocumentIdsChange={onSelectedDocumentIdsChange}
        open={open}
        page={page}
        search={search}
        selectedDocumentIds={selectedDocumentIds}
      />
    </>
  );
}
