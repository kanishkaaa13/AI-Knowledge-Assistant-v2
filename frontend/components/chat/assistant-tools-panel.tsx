"use client";

import * as React from "react";
import { BookOpenText, Download, FileText, Lightbulb, SearchCode, Sparkles, Trash2, Cpu, CheckSquare, Square, UploadCloud } from "lucide-react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";
import type { AssistantQuizItem, SemanticDocumentSearchItem } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDocuments, useDeleteDocument, useUploadDocument } from "@/hooks/use-documents";
import { MindMap } from "@/components/visual/mind-map";
import { KnowledgeGraph } from "@/components/visual/knowledge-graph";

function formatBytes(bytes: number | null) {
  if (!bytes) return "Unknown size";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AssistantToolsPanel({
  generatedSummary,
  isWorking,
  quiz,
  searchResults,
  selectedDocumentIds,
  suggestedPrompts,
  onExportConversation,
  onGenerateQuiz,
  onGenerateSummary,
  onRunSemanticSearch,
  onUsePrompt,
  onSelectedDocumentIdsChange,
  onSendMessage,
  className
}: {
  generatedSummary: string | null;
  isWorking: boolean;
  quiz: AssistantQuizItem[];
  searchResults: SemanticDocumentSearchItem[];
  selectedDocumentIds: string[];
  suggestedPrompts: string[];
  onExportConversation: () => Promise<void>;
  onGenerateQuiz: () => Promise<void>;
  onGenerateSummary: () => Promise<void>;
  onRunSemanticSearch: () => Promise<void>;
  onUsePrompt: (prompt: string) => void;
  onSelectedDocumentIdsChange: (ids: string[]) => void;
  onSendMessage?: (text: string) => Promise<void>;
  className?: string;
}) {
  const { data: allDocsResponse } = useDocuments();
  const allDocs = allDocsResponse?.items ?? [];
  const deleteMutation = useDeleteDocument();
  const uploadMutation = useUploadDocument();
  
  const [isDragging, setIsDragging] = React.useState(false);
  const [uploadProgress, setUploadProgress] = React.useState(0);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      await handleUpload(file);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      await handleUpload(file);
    }
  };

  const handleUpload = async (file: File) => {
    try {
      await uploadMutation.mutateAsync({
        file,
        title: file.name,
        onProgress: (progress) => setUploadProgress(Math.round(progress))
      });
    } catch (error) {
      console.error(error);
    } finally {
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };
  
  const toggleDocument = React.useCallback((id: string) => {
    if (selectedDocumentIds.includes(id)) {
      onSelectedDocumentIdsChange(selectedDocumentIds.filter(docId => docId !== id));
    } else {
      onSelectedDocumentIdsChange([...selectedDocumentIds, id]);
    }
  }, [selectedDocumentIds, onSelectedDocumentIdsChange]);

  const toggleAll = React.useCallback(() => {
    if (selectedDocumentIds.length === allDocs.length) {
      onSelectedDocumentIdsChange([]);
    } else {
      onSelectedDocumentIdsChange(allDocs.map(d => d.id));
    }
  }, [allDocs, selectedDocumentIds.length, onSelectedDocumentIdsChange]);
  
  const selectedDocs = React.useMemo(() => {
    return allDocs.filter((doc) => selectedDocumentIds.includes(doc.id));
  }, [allDocs, selectedDocumentIds]);

  function handleSummarize() {
    if (selectedDocumentIds.length === 0) {
      toast.error("Please select at least one document first");
      return;
    }
    if (onSendMessage) {
      onSendMessage("Please provide a comprehensive summary of the selected documents, including key points, main topics, and important details.");
    }
  }

  function handleQuiz() {
    if (selectedDocumentIds.length === 0) {
      toast.error("Please select at least one document first");
      return;
    }
    if (onSendMessage) {
      onSendMessage("Generate 5 quiz questions with answers based on the content of the selected documents. Format as: Q1: [question] A1: [answer]");
    }
  }

  function handleSearch() {
    if (selectedDocumentIds.length === 0) {
      onSelectedDocumentIdsChange(allDocs.map((doc) => doc.id));
    }
    const input = document.getElementById('chat-input') as HTMLTextAreaElement;
    if (input) {
      input.placeholder = "Search your documents: type your question...";
      input.focus();
    }
  }

  return (
    <aside className={cn("h-full w-[320px] shrink-0 flex-col border-l border-border/40 bg-[var(--bg-secondary)]", className)}>
      <Tabs defaultValue="tools" className="flex h-full flex-col">
        <div className="flex-shrink-0 p-4 border-b border-border/40">
          <TabsList className="flex items-center gap-1 bg-[var(--assistant-bubble)] p-1 rounded-lg w-full overflow-x-auto select-none shrink-0 scrollbar-none">
            <TabsTrigger value="tools" className="flex-1 py-1 px-1.5 text-[10px] font-semibold rounded-md transition-all duration-150 data-[state=active]:bg-[var(--border-color)] data-[state=active]:text-white text-muted-foreground">Tools</TabsTrigger>
            <TabsTrigger value="documents" className="flex-1 py-1 px-1.5 text-[10px] font-semibold rounded-md transition-all duration-150 data-[state=active]:bg-[var(--border-color)] data-[state=active]:text-white text-muted-foreground">Docs</TabsTrigger>
            <TabsTrigger value="memory" className="flex-1 py-1 px-1.5 text-[10px] font-semibold rounded-md transition-all duration-150 data-[state=active]:bg-[var(--border-color)] data-[state=active]:text-white text-muted-foreground">Memory</TabsTrigger>
            <TabsTrigger value="mindmap" className="flex-1 py-1 px-1.5 text-[10px] font-semibold rounded-md transition-all duration-150 data-[state=active]:bg-[var(--border-color)] data-[state=active]:text-white text-muted-foreground">Map</TabsTrigger>
            <TabsTrigger value="graph" className="flex-1 py-1 px-1.5 text-[10px] font-semibold rounded-md transition-all duration-150 data-[state=active]:bg-[var(--border-color)] data-[state=active]:text-white text-muted-foreground">Graph</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <TabsContent value="tools" className="m-0 space-y-4">
            <div className="rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <Sparkles className="h-4 w-4 text-indigo-500" />
                Assistant Actions
              </div>
              <div className="mt-3 flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  Select documents to search:
                </p>
                <button
                  type="button"
                  onClick={toggleAll}
                  className="text-[10px] uppercase font-semibold tracking-wider text-indigo-400 hover:text-indigo-300"
                >
                  {selectedDocumentIds.length === allDocs.length && allDocs.length > 0 ? "Deselect All" : "Select All"}
                </button>
              </div>
              
              {allDocs.length > 0 ? (
                <div className="mt-2 max-h-40 overflow-y-auto space-y-1 rounded-lg bg-[var(--border-color)] p-2">
                  {allDocs.map((doc) => (
                    <div 
                      key={doc.id} 
                      className="flex items-center gap-2 rounded px-2 py-1.5 hover:bg-[#333333] cursor-pointer"
                      onClick={() => toggleDocument(doc.id)}
                    >
                      {selectedDocumentIds.includes(doc.id) ? (
                        <CheckSquare className="h-4 w-4 text-indigo-400 shrink-0" />
                      ) : (
                        <Square className="h-4 w-4 text-muted-foreground shrink-0" />
                      )}
                      <span className="truncate text-xs text-white flex-1">{doc.title}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-xs text-muted-foreground italic">No documents uploaded.</p>
              )}
              
              <div className="mt-4 grid grid-cols-2 gap-2">
                <Button className="h-16 flex-col gap-1 rounded-xl bg-[var(--border-color)] hover:bg-[#333333] border-0 text-[var(--text-primary)] shadow-none" variant="outline" disabled={isWorking} onClick={handleSummarize}>
                  <BookOpenText className="h-5 w-5 text-indigo-400" />
                  <span className="text-xs">Summarize</span>
                </Button>
                <Button className="h-16 flex-col gap-1 rounded-xl bg-[var(--border-color)] hover:bg-[#333333] border-0 text-[var(--text-primary)] shadow-none" variant="outline" disabled={isWorking} onClick={handleQuiz}>
                  <Cpu className="h-5 w-5 text-indigo-400" />
                  <span className="text-xs">Quiz</span>
                </Button>
                <Button className="h-16 flex-col gap-1 rounded-xl bg-[var(--border-color)] hover:bg-[#333333] border-0 text-[var(--text-primary)] shadow-none" variant="outline" disabled={isWorking} onClick={handleSearch}>
                  <SearchCode className="h-5 w-5 text-indigo-400" />
                  <span className="text-xs">Search</span>
                </Button>
                <Button className="h-16 flex-col gap-1 rounded-xl bg-[var(--border-color)] hover:bg-[#333333] border-0 text-[var(--text-primary)] shadow-none" variant="outline" onClick={() => void onExportConversation()}>
                  <Download className="h-5 w-5 text-indigo-400" />
                  <span className="text-xs">Export</span>
                </Button>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="documents" className="m-0 flex flex-col space-y-4">
            {/* Upload Zone */}
            <div
              className={cn(
                "relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors",
                isDragging ? "border-indigo-500 bg-indigo-500/10" : "border-border/40 hover:bg-[var(--assistant-bubble)]"
              )}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input type="file" ref={fileInputRef} className="hidden" onChange={(e) => void handleFileChange(e)} />
              
              {uploadMutation.isPending ? (
                <div className="flex flex-col items-center gap-2 text-indigo-400">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  <span className="text-xs font-medium">Uploading {uploadProgress}%</span>
                </div>
              ) : (
                <>
                  <UploadCloud className="mb-2 h-6 w-6 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">Drop files here or click to upload</span>
                </>
              )}
            </div>

            {/* Header with Select All */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 cursor-pointer" onClick={toggleAll}>
                {selectedDocumentIds.length === allDocs.length && allDocs.length > 0 ? (
                  <CheckSquare className="h-4 w-4 text-indigo-400 shrink-0" />
                ) : (
                  <Square className="h-4 w-4 text-muted-foreground shrink-0" />
                )}
                <span className="text-xs font-medium text-white">Select All</span>
              </div>
              <span className="rounded-lg bg-indigo-600/20 px-2 py-0.5 text-xs font-medium text-indigo-400 shrink-0">
                {selectedDocumentIds.length} / {allDocs.length}
              </span>
            </div>
            
            {allDocs.length > 0 ? (
              <div className="space-y-2 flex-1 overflow-y-auto">
                {allDocs.map((doc) => {
                  const ext = (doc.file_name || "").split('.').pop()?.toLowerCase();
                  return (
                    <div 
                      key={doc.id} 
                      className="flex items-center gap-3 rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-3 transition-colors hover:bg-[var(--border-color)] cursor-pointer"
                      onClick={() => toggleDocument(doc.id)}
                    >
                      <div className="shrink-0">
                        {selectedDocumentIds.includes(doc.id) ? (
                          <CheckSquare className="h-4 w-4 text-indigo-400" />
                        ) : (
                          <Square className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                      
                      <div className="flex min-w-0 flex-1 items-center gap-3">
                        <div className={cn(
                          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-500/10",
                          ext === 'pdf' ? "text-red-400" : ext === 'doc' || ext === 'docx' ? "text-blue-400" : "text-indigo-400"
                        )}>
                          <FileText className="h-4 w-4" />
                        </div>
                        <div className="flex flex-col min-w-0 flex-1 overflow-hidden">
                          <span className="truncate text-sm font-medium text-white" title={doc.title}>{doc.title}</span>
                          <span className="text-xs text-muted-foreground">{formatBytes(doc.file_size)}</span>
                        </div>
                      </div>
                      
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 shrink-0 rounded-lg text-muted-foreground hover:bg-destructive/20 hover:text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          void deleteMutation.mutateAsync(doc.id);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-border/40 p-6 text-center text-sm text-muted-foreground">
                No documents uploaded yet.
              </div>
            )}
          </TabsContent>

          <TabsContent value="memory" className="m-0 space-y-4">
            <section className="rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <Lightbulb className="h-4 w-4 text-indigo-500" />
                Suggested Prompts
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {Array.isArray(suggestedPrompts) && suggestedPrompts.length > 0 ? (
                  suggestedPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      className="rounded-lg bg-[var(--border-color)] px-3 py-2 text-left text-xs text-muted-foreground transition hover:bg-[#333333] hover:text-white"
                      onClick={() => onUsePrompt(prompt)}
                      type="button"
                    >
                      {prompt}
                    </button>
                  ))
                ) : typeof suggestedPrompts === "string" ? (
                  <p className="text-xs text-muted-foreground whitespace-pre-wrap">{suggestedPrompts}</p>
                ) : (
                  <p className="text-xs text-muted-foreground">Suggested prompts will appear here.</p>
                )}
              </div>
            </section>

            <section className="rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <BookOpenText className="h-4 w-4 text-indigo-500" />
                AI Summary
              </div>
              <p className="mt-3 whitespace-pre-wrap text-xs text-muted-foreground leading-relaxed">
                {generatedSummary ?? "Generate a summary from your selected documents or current query."}
              </p>
            </section>

            <section className="rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <SearchCode className="h-4 w-4 text-indigo-500" />
                Semantic Results
              </div>
              <div className="mt-3 space-y-3">
                {Array.isArray(searchResults) && searchResults.length > 0 ? (
                  searchResults.map((item) => (
                    <div key={item.document_id} className="rounded-lg bg-[var(--border-color)] p-3">
                      <p className="text-xs font-medium text-white">{item.title}</p>
                      <p className="mt-1 text-[10px] text-muted-foreground">{item.filename}</p>
                      <p className="mt-2 text-xs text-muted-foreground line-clamp-3">{item.excerpt}</p>
                    </div>
                  ))
                ) : typeof searchResults === "string" ? (
                  <p className="text-xs text-muted-foreground whitespace-pre-wrap">{searchResults}</p>
                ) : (
                  <p className="text-xs text-muted-foreground">Run semantic document search to inspect top matches.</p>
                )}
              </div>
            </section>

            <section className="rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <BookOpenText className="h-4 w-4 text-indigo-500" />
                Quiz
              </div>
              <div className="mt-3 space-y-3">
                {Array.isArray(quiz) && quiz.length > 0 ? (
                  quiz.map((item, index) => (
                    <div key={`${item.question}-${index}`} className="rounded-lg bg-[var(--border-color)] p-3">
                      <p className="text-xs font-medium text-white">{item.question}</p>
                      <p className="mt-1 text-[10px] uppercase tracking-[0.2em] text-indigo-400">
                        {item.difficulty}
                      </p>
                      <p className="mt-2 text-xs text-muted-foreground">{item.answer}</p>
                    </div>
                  ))
                ) : typeof quiz === "string" ? (
                  <p className="text-xs text-muted-foreground whitespace-pre-wrap">{quiz}</p>
                ) : (
                  <p className="text-xs text-muted-foreground">Generate a quiz from your knowledge base.</p>
                )}
              </div>
            </section>
          </TabsContent>
          <TabsContent value="mindmap" className="m-0 space-y-4">
            <MindMap />
          </TabsContent>
          <TabsContent value="graph" className="m-0 space-y-4">
            <KnowledgeGraph />
          </TabsContent>
        </div>
      </Tabs>
    </aside>
  );
}
