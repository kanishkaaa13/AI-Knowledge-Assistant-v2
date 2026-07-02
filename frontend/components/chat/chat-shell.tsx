"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import dynamic from "next/dynamic";
import { Menu, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import type { AssistantQuizItem, SemanticDocumentSearchItem } from "@/types/api";
import type { AssistantSettings, ConversationGroup } from "@/types/chat";

import { AssistantToolsPanel } from "@/components/chat/assistant-tools-panel";
import { ChatHeader } from "@/components/chat/chat-header";
import { ChatInput } from "@/components/chat/chat-input";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { ChatThread } from "@/components/chat/chat-thread";
import { MobileSidebar } from "@/components/chat/mobile-sidebar";
import { ProfileDropdown } from "@/components/chat/profile-dropdown";
import { SettingsModal } from "@/components/chat/settings-modal";
import { useAuth } from "@/components/providers/auth-provider";
import type { ChatMessage } from "@/types/chat";
import { FlashcardPanel } from "@/components/chat/flashcard-panel";
import { NotesShell } from "@/components/notes/notes-shell";
import { useDocuments } from "@/hooks/use-documents";

const DocumentManager = dynamic(
  () => import("@/components/documents/document-manager").then((mod) => mod.DocumentManager),
  { ssr: false }
);

interface ChatShellProps {
  activeConversationId?: string;
  activeConversationTitle?: string;
  generatedSummary: string | null;
  groupedConversations: ConversationGroup[];
  historySearch: string;
  input: string;
  isConversationLoading: boolean;
  isHistoryLoading: boolean;
  isSettingsOpen: boolean;
  isSidebarOpen: boolean;
  isWorkingTools: boolean;
  messages: ChatMessage[];
  quiz: AssistantQuizItem[];
  searchResults: SemanticDocumentSearchItem[];
  selectedDocumentIds: string[];
  settings: AssistantSettings;
  suggestedPrompts: string[];
  onCreateConversation: () => void;
  onDeleteConversation: (conversationId: string) => Promise<void>;
  onExportConversation: (conversationId: string) => Promise<void>;
  onFavoriteConversation: (conversationId: string, favorite: boolean) => Promise<void>;
  onGenerateQuiz: () => Promise<void>;
  onGenerateSummary: () => Promise<void>;
  onHistorySearchChange: (value: string) => void;
  onInputChange: (value: string) => void;
  onRenameConversation: (conversationId: string, title: string) => Promise<void>;
  onRunSemanticSearch: () => Promise<void>;
  onSelectConversation: (conversationId: string) => void;
  onSelectedDocumentIdsChange: (ids: string[]) => void;
  onSendMessage: () => Promise<void>;
  onSettingsChange: (settings: AssistantSettings) => void;
  onSettingsOpenChange: (open: boolean) => void;
  onSidebarOpenChange: (open: boolean) => void;
  onUseSuggestedPrompt: (prompt: string) => void;
}

export function ChatShell({
  activeConversationId,
  activeConversationTitle,
  generatedSummary,
  groupedConversations,
  historySearch,
  input,
  isConversationLoading,
  isHistoryLoading,
  isSettingsOpen,
  isSidebarOpen,
  isWorkingTools,
  messages,
  quiz,
  searchResults,
  selectedDocumentIds,
  settings,
  suggestedPrompts,
  onCreateConversation,
  onDeleteConversation,
  onExportConversation,
  onFavoriteConversation,
  onGenerateQuiz,
  onGenerateSummary,
  onHistorySearchChange,
  onInputChange,
  onRenameConversation,
  onRunSemanticSearch,
  onSelectConversation,
  onSelectedDocumentIdsChange,
  onSendMessage,
  onSettingsChange,
  onSettingsOpenChange,
  onSidebarOpenChange,
  onUseSuggestedPrompt
}: ChatShellProps) {
  const { user } = useAuth();
  const { data: allDocsResponse } = useDocuments();
  const allDocsCount = allDocsResponse?.items?.length ?? 0;
  const chatCount = React.useMemo(() => {
    return groupedConversations.reduce((sum, g) => sum + g.conversations.length, 0);
  }, [groupedConversations]);

  const [isToolsOpen, setIsToolsOpen] = React.useState(false);
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const [activeTab, setActiveTab] = React.useState<"chat" | "notes" | "flashcards">("chat");
  const [activePdf, setActivePdf] = React.useState<{
    filename: string;
    page: number;
    highlightText: string;
  } | null>(null);

  React.useEffect(() => {
    const saved = localStorage.getItem('sidebarOpen');
    if (saved !== null) {
      setSidebarOpen(saved === 'true');
    } else {
      setSidebarOpen(window.innerWidth >= 768);
    }
  }, []);

  React.useEffect(() => {
    localStorage.setItem('sidebarOpen', String(sidebarOpen));
  }, [sidebarOpen]);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)]">
      <ChatSidebar
        activeConversationId={activeConversationId}
        groupedConversations={groupedConversations}
        historySearch={historySearch}
        isLoading={isHistoryLoading}
        onCreateConversation={onCreateConversation}
        onDeleteConversation={onDeleteConversation}
        onExportConversation={onExportConversation}
        onFavoriteConversation={onFavoriteConversation}
        onHistorySearchChange={onHistorySearchChange}
        onRenameConversation={onRenameConversation}
        onSelectConversation={onSelectConversation}
        onOpenSettings={() => onSettingsOpenChange(true)}
        sidebarOpen={sidebarOpen}
      />

      <div className="flex h-full min-w-0 flex-1 flex-col overflow-hidden bg-[var(--bg-chat)]">
        <header className="sticky top-0 z-20 border-b border-[var(--border-color)] bg-[var(--bg-primary)]/80 backdrop-blur-xl flex-shrink-0">
          <div className="flex items-center justify-between gap-3 px-4 py-4 sm:px-6">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(prev => !prev)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#6b7280',
                  cursor: 'pointer',
                  padding: '6px 8px',
                  borderRadius: '8px',
                  fontSize: '18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  transition: 'color 0.15s',
                }}
                onMouseEnter={e => (e.currentTarget.style.color = '#d1d1d1')}
                onMouseLeave={e => (e.currentTarget.style.color = '#6b7280')}
                title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
              >
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <rect x="2" y="3" width="14" height="2" rx="1" fill="currentColor"/>
                  <rect x="2" y="8" width="14" height="2" rx="1" fill="currentColor"/>
                  <rect x="2" y="13" width="14" height="2" rx="1" fill="currentColor"/>
                </svg>
              </button>
              <ChatHeader
                title={activeConversationTitle ?? "New conversation"}
                subtitle="Chat with your private knowledge assistant"
              />
            </div>
            
            {/* Segmented Control / Navigation Tabs */}
            <div className="flex items-center bg-[var(--bg-panel)] border border-[var(--border-color)] rounded-lg p-0.5 shadow-sm">
              <button
                onClick={() => setActiveTab("chat")}
                className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
                  activeTab === "chat"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-muted-foreground hover:text-white hover:bg-[var(--border-color)]"
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setActiveTab("flashcards")}
                className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
                  activeTab === "flashcards"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-muted-foreground hover:text-white hover:bg-[var(--border-color)]"
                }`}
              >
                Study Flashcards
              </button>
              <button
                onClick={() => setActiveTab("notes")}
                className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
                  activeTab === "notes"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-muted-foreground hover:text-white hover:bg-[var(--border-color)]"
                }`}
              >
                My Notes
              </button>
            </div>

            <div className="flex items-center gap-3">
              <Button
                className="xl:hidden"
                size="sm"
                variant="secondary"
                onClick={() => setIsToolsOpen(true)}
              >
                <Sparkles className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </header>

        <main className="flex min-h-0 flex-1 overflow-hidden">
          {activeTab === "chat" && (
            <div className="flex flex-1 min-w-0 h-full relative">
              <div className={cn("flex flex-col h-full min-w-0 transition-all duration-300", activePdf ? "w-1/2 border-r border-[var(--border-color)]" : "flex-1")}>
                <ChatThread
                  isLoading={isConversationLoading}
                  messages={messages}
                  userName={user?.name ?? "You"}
                  onUsePrompt={onUseSuggestedPrompt}
                  onCitationClick={(filename, page, content) => {
                    setActivePdf({ filename, page, highlightText: content });
                  }}
                  allDocsCount={allDocsCount}
                  chatCount={chatCount}
                />
                <div className="border-t border-[var(--border-color)] bg-[var(--bg-panel)] p-4 flex-shrink-0 sticky bottom-0 min-h-[64px] max-h-[160px] overflow-hidden">
                  <ChatInput
                    input={input}
                    onInputChange={onInputChange}
                    onSendMessage={onSendMessage}
                    streamResponses={settings.streamResponses}
                  />
                </div>
              </div>

              {activePdf && (
                <div className="w-1/2 h-full p-4 overflow-hidden bg-[var(--bg-panel)] flex flex-col shrink-0">
                  <PDFViewerPanel
                    filename={activePdf.filename}
                    initialPage={activePdf.page}
                    highlightText={activePdf.highlightText}
                    onClose={() => setActivePdf(null)}
                  />
                </div>
              )}
            </div>
          )}

          {activeTab === "flashcards" && (
            <div className="flex-1 h-full overflow-hidden">
              <FlashcardPanel selectedDocumentIds={selectedDocumentIds} />
            </div>
          )}

          {activeTab === "notes" && (
            <div className="flex-1 h-full overflow-hidden">
              <NotesShell />
            </div>
          )}
        </main>
      </div>

      <AssistantToolsPanel
        generatedSummary={generatedSummary}
        isWorking={isWorkingTools}
        quiz={quiz}
        searchResults={searchResults}
        selectedDocumentIds={selectedDocumentIds}
        suggestedPrompts={suggestedPrompts}
        onExportConversation={() => activeConversationId ? onExportConversation(activeConversationId) : Promise.resolve()}
        onGenerateQuiz={onGenerateQuiz}
        onGenerateSummary={onGenerateSummary}
        onRunSemanticSearch={onRunSemanticSearch}
        onUsePrompt={onUseSuggestedPrompt}
        onSelectedDocumentIdsChange={onSelectedDocumentIdsChange}
        onSendMessage={onSendMessage}
        className="hidden xl:flex h-full"
      />

      <DocumentManager
        selectedDocumentIds={selectedDocumentIds}
        onSelectedDocumentIdsChange={onSelectedDocumentIdsChange}
      />



      <Dialog open={isToolsOpen} onOpenChange={setIsToolsOpen}>
        <DialogContent className="right-0 top-0 h-screen max-w-[340px] translate-x-0 translate-y-0 rounded-none border-l p-0 xl:hidden">
          <AssistantToolsPanel
            generatedSummary={generatedSummary}
            isWorking={isWorkingTools}
            quiz={quiz}
            searchResults={searchResults}
            selectedDocumentIds={selectedDocumentIds}
            suggestedPrompts={suggestedPrompts}
            onExportConversation={() => activeConversationId ? onExportConversation(activeConversationId) : Promise.resolve()}
            onGenerateQuiz={onGenerateQuiz}
            onGenerateSummary={onGenerateSummary}
            onRunSemanticSearch={onRunSemanticSearch}
            onUsePrompt={onUseSuggestedPrompt}
            onSelectedDocumentIdsChange={onSelectedDocumentIdsChange}
            onSendMessage={onSendMessage}
            className="flex"
          />
        </DialogContent>
      </Dialog>

      <SettingsModal
        onOpenChange={onSettingsOpenChange}
        onSave={onSettingsChange}
        open={isSettingsOpen}
        settings={settings}
      />
    </div>
  );
}
