"use client";

import { ChatShell } from "@/components/chat/chat-shell";
import { useChat } from "@/hooks/use-chat";

// Render errors propagate to the ErrorBoundary in the root layout.
export default function DashboardPage() {
  const chat = useChat();

  return (
    <ChatShell
      activeConversationId={chat.activeConversationId}
      activeConversationTitle={chat.activeConversation?.title}
      generatedSummary={chat.generatedSummary}
      groupedConversations={chat.groupedConversations}
      historySearch={chat.historySearch}
      input={chat.input}
      isConversationLoading={chat.isConversationLoading}
      isHistoryLoading={chat.isHistoryLoading}
      isSettingsOpen={chat.isSettingsOpen}
      isSidebarOpen={chat.isSidebarOpen}
      isWorkingTools={chat.isWorkingTools}
      isAgentMode={chat.isAgentMode}
      messages={chat.activeConversation?.messages ?? []}
      quiz={chat.quiz}
      searchResults={chat.searchResults}
      selectedDocumentIds={chat.selectedDocumentIds}
      settings={chat.settings}
      suggestedPrompts={chat.suggestedPrompts}
      onCreateConversation={chat.createConversation}
      onDeleteConversation={chat.deleteConversation}
      onExportConversation={chat.exportConversation}
      onFavoriteConversation={chat.favoriteConversation}
      onGenerateQuiz={chat.generateQuiz}
      onGenerateSummary={chat.generateSummary}
      onHistorySearchChange={chat.setHistorySearch}
      onInputChange={chat.setInput}
      onRenameConversation={chat.renameConversation}
      onRunSemanticSearch={chat.runSemanticSearch}
      onSelectConversation={chat.selectConversation}
      onSelectedDocumentIdsChange={chat.setSelectedDocumentIds}
      onSendMessage={chat.sendMessage}
      onSettingsChange={chat.updateSettings}
      onAgentModeChange={chat.setIsAgentMode}
      onSettingsOpenChange={chat.setIsSettingsOpen}
      onSidebarOpenChange={chat.setIsSidebarOpen}
      onUseSuggestedPrompt={chat.useSuggestedPrompt}
    />
  );
}
