"use client";

import * as React from "react";
import { ChatShell } from "@/components/chat/chat-shell";
import { useChat } from "@/hooks/use-chat";

export default function DashboardPage() {
  const [hasError, setHasError] = React.useState(false);

  React.useEffect(() => {
    window.onerror = (msg, src, line, col, err) => {
      console.error("Global error:", msg, err);
      // Optional: setHasError(true) if you want to show a fallback UI on global errors
    };
  }, []);

  let chat;
  try {
    chat = useChat();
  } catch (err) {
    console.error("Error in useChat:", err);
    return <div className="p-8 text-red-500">Failed to load chat hook. Check console.</div>;
  }

  if (hasError) {
    return <div className="p-8 text-red-500">Something went wrong. Check console.</div>;
  }

  try {
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
      onSettingsOpenChange={chat.setIsSettingsOpen}
      onSidebarOpenChange={chat.setIsSidebarOpen}
      onUseSuggestedPrompt={chat.useSuggestedPrompt}
    />
    );
  } catch (err) {
    console.error("Error rendering ChatShell:", err);
    return <div className="p-8 text-red-500">Error rendering ChatShell. Check console.</div>;
  }
}
