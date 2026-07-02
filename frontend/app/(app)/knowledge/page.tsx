"use client";

import * as React from "react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { listOKFRecords, getOKFDocument } from "@/lib/api";
import { OKFRecord, OKFDocument } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";
import { BookOpen, Tag, ArrowLeft, Loader2, Filter, ChevronLeft, ChevronRight, Calendar } from "lucide-react";

export default function KnowledgePage() {
  const [records, setRecords] = React.useState<OKFRecord[]>([]);
  const [total, setTotal] = React.useState(0);
  const [page, setPage] = React.useState(1);
  const [pageSize] = React.useState(9);
  
  const [selectedType, setSelectedType] = React.useState<string>("");
  const [selectedRecordId, setSelectedRecordId] = React.useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = React.useState<OKFDocument | null>(null);
  
  const [loadingList, setLoadingList] = React.useState(true);
  const [loadingDetail, setLoadingDetail] = React.useState(false);

  // Fetch list of OKF records
  const fetchRecords = React.useCallback(async () => {
    setLoadingList(true);
    try {
      const data = await listOKFRecords({
        page,
        page_size: pageSize,
        type: selectedType || undefined,
      });
      setRecords(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load OKF records:", err);
    } finally {
      setLoadingList(false);
    }
  }, [page, selectedType, pageSize]);

  React.useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  // Fetch individual OKF document detail when a record is selected
  React.useEffect(() => {
    if (!selectedRecordId) {
      setSelectedDoc(null);
      return;
    }
    const fetchDetail = async () => {
      setLoadingDetail(true);
      try {
        const doc = await getOKFDocument(selectedRecordId);
        setSelectedDoc(doc);
      } catch (err) {
        console.error("Failed to load OKF document details:", err);
      } finally {
        setLoadingDetail(false);
      }
    };
    fetchDetail();
  }, [selectedRecordId]);

  // Helper to color badge based on concept type
  const getTypeBadgeStyles = (type: string) => {
    switch (type.toLowerCase()) {
      case "concept":
        return "bg-purple-500/10 text-purple-400 border border-purple-500/20";
      case "api":
        return "bg-blue-500/10 text-blue-400 border border-blue-500/20";
      case "policy":
        return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
      case "dataset":
        return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      default:
        return "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20";
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-background px-4 py-4 sm:px-6 lg:px-8 w-full">
      <div className="mx-auto grid max-w-7xl gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
        <AppSidebar />

        <main className="space-y-4">
          {/* Header Section */}
          <section className="rounded-[2rem] border border-border/60 bg-card/70 p-6 backdrop-blur">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-muted-foreground">
                  Knowledge Base
                </p>
                <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                  Open Knowledge Format (OKF) Browser
                </h1>
                <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                  Explore modular concepts, API specifications, and entity structures extracted directly from your uploaded documents using LLMs.
                </p>
              </div>
            </div>
          </section>

          {/* Details View */}
          {selectedRecordId ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Button
                  onClick={() => setSelectedRecordId(null)}
                  variant="ghost"
                  className="rounded-full flex items-center gap-2 hover:bg-secondary"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to Knowledge Base
                </Button>
              </div>

              {loadingDetail ? (
                <div className="flex h-64 items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : selectedDoc ? (
                <Card className="rounded-[2rem] border-border/60 bg-card/70 p-6 sm:p-8 shadow-xl backdrop-blur">
                  <div className="space-y-6">
                    {/* Header info */}
                    <div className="border-b border-border/60 pb-6">
                      <div className="flex flex-wrap items-center gap-3 mb-4">
                        <Badge className={`rounded-full px-3 py-1 font-medium capitalize text-xs ${getTypeBadgeStyles(selectedDoc.type)}`}>
                          {selectedDoc.type}
                        </Badge>
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Calendar className="h-3.5 w-3.5" />
                          <span>Updated {new Date(selectedDoc.updated_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                        {selectedDoc.title}
                      </h2>
                      {selectedDoc.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-4">
                          {selectedDoc.tags.map((tag) => (
                            <Badge
                              key={tag}
                              variant="secondary"
                              className="rounded-full text-xs flex items-center gap-1 bg-secondary/80 text-muted-foreground hover:text-foreground"
                            >
                              <Tag className="h-3 w-3" />
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Body Content */}
                    <div className="prose prose-invert max-w-none text-sm text-foreground/90 leading-relaxed py-2">
                      <ReactMarkdown>{selectedDoc.body}</ReactMarkdown>
                    </div>

                    {/* Related section */}
                    {selectedDoc.related && selectedDoc.related.length > 0 && (
                      <div className="border-t border-border/60 pt-6">
                        <h3 className="text-sm font-semibold tracking-wider text-muted-foreground uppercase mb-3">
                          Related Concepts
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {selectedDoc.related.map((rel) => (
                            <Badge
                              key={rel}
                              variant="outline"
                              className="rounded-full text-xs py-1 px-3 border-border bg-secondary/35 text-foreground hover:bg-secondary cursor-default"
                            >
                              {rel}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  Failed to load OKF document.
                </div>
              )}
            </div>
          ) : (
            /* Grid List View */
            <div className="space-y-4">
              {/* Filter controls */}
              <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-[1.5rem] border border-border/60 bg-card/30 backdrop-blur">
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Filter by type:</span>
                  <select
                    value={selectedType}
                    onChange={(e) => {
                      setSelectedType(e.target.value);
                      setPage(1);
                    }}
                    className="bg-secondary text-foreground text-sm rounded-xl py-1.5 px-3 border border-border outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer"
                  >
                    <option value="">All Types</option>
                    <option value="concept">Concept</option>
                    <option value="api">API</option>
                    <option value="policy">Policy</option>
                    <option value="dataset">Dataset</option>
                  </select>
                </div>
                <div className="text-sm text-muted-foreground">
                  Showing {records.length} of {total} concepts
                </div>
              </div>

              {/* Grid content */}
              {loadingList ? (
                <div className="flex h-64 items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : records.length === 0 ? (
                <div className="text-center py-20 rounded-[2rem] border border-border/60 bg-card/20 backdrop-blur">
                  <BookOpen className="mx-auto h-12 w-12 text-muted-foreground/30 mb-4" />
                  <h3 className="text-lg font-medium text-foreground">No concepts found</h3>
                  <p className="text-sm text-muted-foreground mt-2 max-w-sm mx-auto">
                    Try changing your filters or upload some documents to extract OKF concepts.
                  </p>
                </div>
              ) : (
                <>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {records.map((rec) => (
                      <Card
                        key={rec.id}
                        onClick={() => setSelectedRecordId(rec.id)}
                        className="rounded-[1.75rem] border-border/60 bg-card/70 hover:border-primary/50 hover:bg-card/90 transition-all duration-200 cursor-pointer group flex flex-col justify-between"
                      >
                        <CardHeader className="space-y-3 pb-3">
                          <div className="flex items-center justify-between">
                            <Badge className={`rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize ${getTypeBadgeStyles(rec.type)}`}>
                              {rec.type}
                            </Badge>
                          </div>
                          <CardTitle className="text-lg font-semibold tracking-tight text-foreground group-hover:text-primary transition-colors line-clamp-2">
                            {rec.title}
                          </CardTitle>
                        </CardHeader>
                        
                        <CardContent className="space-y-4 pt-0">
                          {rec.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {rec.tags.slice(0, 3).map((tag) => (
                                <span
                                  key={tag}
                                  className="inline-flex items-center gap-1 text-[10px] text-muted-foreground bg-secondary/50 rounded-full px-2 py-0.5"
                                >
                                  <Tag className="h-2.5 w-2.5" />
                                  {tag}
                                </span>
                              ))}
                              {rec.tags.length > 3 && (
                                <span className="text-[10px] text-muted-foreground px-1.5 py-0.5">
                                  +{rec.tags.length - 3} more
                                </span>
                              )}
                            </div>
                          )}
                          <div className="flex justify-between items-center text-[11px] text-muted-foreground border-t border-border/30 pt-3 mt-auto">
                            <span>Updated {new Date(rec.updated_at).toLocaleDateString()}</span>
                            <span className="text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                              Read &rarr;
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-center gap-4 py-4">
                      <Button
                        disabled={page === 1}
                        onClick={() => setPage(page - 1)}
                        variant="secondary"
                        className="rounded-xl px-3 py-1 flex items-center gap-1 disabled:opacity-50"
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </Button>
                      <span className="text-sm font-medium text-muted-foreground">
                        Page {page} of {totalPages}
                      </span>
                      <Button
                        disabled={page === totalPages}
                        onClick={() => setPage(page + 1)}
                        variant="secondary"
                        className="rounded-xl px-3 py-1 flex items-center gap-1 disabled:opacity-50"
                      >
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
