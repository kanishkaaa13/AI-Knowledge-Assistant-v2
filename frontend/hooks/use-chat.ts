"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  createConversation,
  deleteConversation,
  exportConversation,
  favoriteConversation,
  generateAssistantQuiz,
  getConversation,
  getSuggestedPrompts,
  listConversations,
  pinConversation,
  queryAssistant,
  renameConversation,
  semanticDocumentSearch,
  summarizeAssistantKnowledge
} from "@/lib/api";
import { streamAssistantChat } from "@/lib/chat-stream";
import type { StreamPayload } from "@/lib/chat-stream";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useDocuments } from "@/hooks/use-documents";
import type {
  AssistantQuizItem,
  ConversationDetail as ApiConversationDetail,
  ConversationListItem as ApiConversationListItem,
  SemanticDocumentSearchItem,
  StoredMessage
} from "@/types/api";
import type {
  AssistantSettings,
  ChatMessage,
  ConversationDetail,
  ConversationGroup,
  ConversationPreview
} from "@/types/chat";

const starterSettings: AssistantSettings = {
  theme: "system",
  model: "llama3",
  webSearch: true,
  streamResponses: true
};

function createId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

function formatMessageTime(timestamp: string) {
  return new Intl.DateTimeFormat("en", {
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(timestamp));
}

function mapMessage(message: any): ChatMessage {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    createdAt: formatMessageTime(message.created_at),
    sequenceNumber: message.sequence_number,
    citations: message.citations ?? []
  };
}

function mapConversationPreview(conversation: ApiConversationListItem): ConversationPreview {
  return {
    id: conversation.id,
    title: conversation.title,
    summary: conversation.summary,
    updatedAt: conversation.updated_at,
    createdAt: conversation.created_at,
    isFavorite: conversation.is_favorite,
    messageCount: conversation.message_count,
    lastMessagePreview: conversation.last_message_preview
  };
}

function mapConversationDetail(conversation: ApiConversationDetail): ConversationDetail {
  return {
    id: conversation.id,
    userId: conversation.user_id,
    title: conversation.title,
    summary: conversation.summary,
    createdAt: conversation.created_at,
    updatedAt: conversation.updated_at,
    isFavorite: conversation.is_favorite,
    messageCount: conversation.messages.length,
    lastMessagePreview: conversation.messages.at(-1)?.content ?? conversation.summary,
    messages: conversation.messages.map(mapMessage)
  };
}

function groupConversations(conversations: ConversationPreview[]): ConversationGroup[] {
  const groups: Record<string, ConversationPreview[]> = {
    Favorites: conversations.filter((item) => item.isFavorite),
    Recent: conversations.filter((item) => !item.isFavorite)
  };

  return Object.entries(groups)
    .filter(([, items]) => items.length > 0)
    .map(([label, items]) => ({ label, conversations: items }));
}

export function useChat() {
  const queryClient = useQueryClient();
  const [activeConversationId, setActiveConversationId] = React.useState<string | undefined>();
  const [input, setInput] = React.useState("");
  const [historySearch, setHistorySearch] = React.useState("");
  const [isFilterFavorites, setIsFilterFavorites] = React.useState<boolean | undefined>(undefined);
  const [filterDateFrom, setFilterDateFrom] = React.useState<string | undefined>(undefined);
  const [filterDateTo, setFilterDateTo] = React.useState<string | undefined>(undefined);
  const [isDraftConversation, setIsDraftConversation] = React.useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = React.useState(false);
  const [settings, setSettings] = React.useState(starterSettings);
  const [selectedDocumentIds, setSelectedDocumentIds] = React.useState<string[]>([]);
  const [generatedSummary, setGeneratedSummary] = React.useState<string | null>(null);
  const [quiz, setQuiz] = React.useState<AssistantQuizItem[]>([]);
  const [searchResults, setSearchResults] = React.useState<SemanticDocumentSearchItem[]>([]);
  const [localSuggestions, setLocalSuggestions] = React.useState<string[]>([]);
  const debouncedSearch = useDebouncedValue(historySearch, 250);
  const { data: allDocsResponse } = useDocuments();
  const allDocs = allDocsResponse?.items ?? [];

  const conversationsQuery = useQuery({
    queryKey: ["conversations", debouncedSearch, isFilterFavorites, filterDateFrom, filterDateTo],
    queryFn: async () => {
      const data = await listConversations({
        search: debouncedSearch || undefined,
        is_favorite: isFilterFavorites,
        date_from: filterDateFrom || undefined,
        date_to: filterDateTo || undefined
      });
      return data.map(mapConversationPreview);
    },
    staleTime: 30_000
  });

  const activeConversationQuery = useQuery({
    queryKey: ["conversation", activeConversationId],
    queryFn: async () => {
      const data = await getConversation(activeConversationId!);
      return mapConversationDetail(data);
    },
    enabled: Boolean(activeConversationId)
  });

  const activeConversation = activeConversationQuery.data;
  // Detect whether any assistant message is currently streaming
  const isCurrentlyStreaming = React.useMemo(
    () => (activeConversation?.messages ?? []).some((m) => m.isStreaming),
    [activeConversation?.messages]
  );

  // Only use the last message content once streaming is fully done
  const latestReferenceText = React.useMemo(() => {
    if (isCurrentlyStreaming) return null; // Don't recompute during stream
    return (
      input.trim() ||
      [...(activeConversation?.messages || [])].reverse().find((m) => !m.isStreaming)?.content ||
      activeConversation?.summary ||
      "Summarize my selected documents"
    );
  }, [
    isCurrentlyStreaming,
    input,
    // Only update when the conversation itself changes (id or message count), NOT on content changes
    activeConversation?.id,
    activeConversation?.messageCount,
    activeConversation?.summary,
  ]);

  const suggestedPromptsQuery = useQuery({
    queryKey: ["assistant-suggested-prompts", latestReferenceText, settings.model, selectedDocumentIds],
    queryFn: async () => {
      const result = await getSuggestedPrompts({
        query: latestReferenceText!,
        model: settings.model,
        document_ids: selectedDocumentIds
      });
      let prompts = result.prompts;
      if (typeof prompts === "string") {
        try {
          prompts = JSON.parse(prompts);
        } catch {
          // Keep as string if parsing fails
        }
      }
      return prompts;
    },
    // Guard: only call when NOT streaming AND we have a reference text
    enabled: Boolean(latestReferenceText) && !isCurrentlyStreaming,
    staleTime: 60_000,       // Don't refetch for 60s after a successful fetch
    gcTime: 120_000,         // Keep in cache for 2 min
    refetchOnWindowFocus: false, // Never refetch just because the user switched tabs
    retry: false,            // Don't retry on 429 — just let it be
  });

  React.useEffect(() => {
    if (
      !isDraftConversation &&
      !activeConversationId &&
      conversationsQuery.data &&
      conversationsQuery.data.length > 0
    ) {
      setActiveConversationId(conversationsQuery.data[0].id);
    }
  }, [activeConversationId, conversationsQuery.data, isDraftConversation]);

  const renameMutation = useMutation({
    mutationFn: async ({ conversationId, title }: { conversationId: string; title: string }) =>
      renameConversation(conversationId, title),
    onSuccess: async (_, variables) => {
      await queryClient.invalidateQueries({ queryKey: ["conversations"] });
      await queryClient.invalidateQueries({ queryKey: ["conversation", variables.conversationId] });
      toast.success("Conversation renamed");
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: async (_, conversationId) => {
      if (activeConversationId === conversationId) {
        React.startTransition(() => {
          setIsDraftConversation(false);
          setActiveConversationId(undefined);
        });
      }
      queryClient.removeQueries({ queryKey: ["conversation", conversationId] });
      await queryClient.invalidateQueries({ queryKey: ["conversations"] });
      toast.success("Conversation deleted");
    }
  });

  const favoriteMutation = useMutation({
    mutationFn: ({ conversationId, favorite }: { conversationId: string; favorite: boolean }) =>
      favoriteConversation(conversationId, favorite),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["conversations"] });
      await queryClient.invalidateQueries({ queryKey: ["conversation", activeConversationId] });
    }
  });

  const pinMutation = useMutation({
    mutationFn: ({ conversationId, pin }: { conversationId: string; pin: boolean }) =>
      pinConversation(conversationId, pin),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["conversations"] });
      await queryClient.invalidateQueries({ queryKey: ["conversation", activeConversationId] });
      toast.success("Conversation pin status updated");
    }
  });

  const updateConversationCache = React.useCallback(
    (conversationId: string, updater: (current: ConversationDetail | undefined) => ConversationDetail) => {
      queryClient.setQueryData<ConversationDetail>(["conversation", conversationId], (current) =>
        updater(current)
      );
    },
    [queryClient]
  );

  const createConversationDraft = React.useCallback(() => {
    React.startTransition(() => {
      setIsDraftConversation(true);
      setActiveConversationId(undefined);
      setInput("");
      setIsSidebarOpen(false);
    });
    setTimeout(() => {
      document.getElementById("chat-input")?.focus();
    }, 0);
  }, []);

  const selectConversation = React.useCallback((conversationId: string) => {
    React.startTransition(() => {
      setIsDraftConversation(false);
      setActiveConversationId(conversationId);
      setIsSidebarOpen(false);
    });
  }, []);

  const exportCurrentConversation = React.useCallback(async (conversationId: string) => {
    if (conversationId.startsWith("temp-")) return;
    
    // Check if we have messages in cache
    const currentCache = queryClient.getQueryData<ConversationDetail>(["conversation", conversationId]);
    if (!currentCache || !currentCache.messages || currentCache.messages.length === 0) {
      toast.error("Start a conversation first to export");
      return;
    }

    const dateStr = new Date().toLocaleString();
    let text = `AI Knowledge Assistant - Conversation Export\nDate: ${dateStr}\n─────────────────────────────────────────\n\n`;
    
    currentCache.messages.forEach((msg) => {
      text += `[${msg.role.toUpperCase()}] ${msg.createdAt}\n${msg.content}\n\n`;
    });
    text += `─────────────────────────────────────────\n`;

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `conversation-export-${new Date().toISOString().slice(0, 10)}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
  }, [queryClient]);

  const updateSettings = React.useCallback((nextSettings: AssistantSettings) => {
    setSettings(nextSettings);
  }, []);

  const renameStoredConversation = React.useCallback(
    async (conversationId: string, title: string) => {
      if (conversationId.startsWith("temp-")) return;
      await renameMutation.mutateAsync({ conversationId, title });
    },
    [renameMutation]
  );

  const removeConversation = React.useCallback(
    async (conversationId: string) => {
      if (conversationId.startsWith("temp-")) {
        setActiveConversationId(undefined);
        return;
      }
      await deleteMutation.mutateAsync(conversationId);
    },
    [deleteMutation]
  );

  const markFavoriteConversation = React.useCallback(
    async (conversationId: string, favorite: boolean) => {
      if (conversationId.startsWith("temp-")) return;
      await favoriteMutation.mutateAsync({ conversationId, favorite });
    },
    [favoriteMutation]
  );

  const togglePinConversation = React.useCallback(
    async (conversationId: string, pin: boolean) => {
      if (conversationId.startsWith("temp-")) return;
      await pinMutation.mutateAsync({ conversationId, pin });
    },
    [pinMutation]
  );

  const toolMutation = useMutation({
    mutationFn: async (tool: "summary" | "quiz" | "search") => {
      const effectiveDocumentIds = selectedDocumentIds.length > 0 ? selectedDocumentIds : allDocs.map(d => d.id);
      const basePayload = {
        query: latestReferenceText ?? "",
        model: settings.model,
        document_ids: effectiveDocumentIds
      };
      if (tool === "summary") {
        return {
          tool,
          result: await summarizeAssistantKnowledge(basePayload)
        };
      }
      if (tool === "quiz") {
        return {
          tool,
          result: await generateAssistantQuiz(basePayload)
        };
      }
      return {
        tool,
        result: await semanticDocumentSearch(basePayload)
      };
    },
    onSuccess(data) {
      if (data.tool === "summary") {
        setGeneratedSummary(data.result.summary);
      }
      if (data.tool === "quiz") {
        let quizData = data.result.questions;
        if (typeof quizData === "string") {
          try {
            quizData = JSON.parse(quizData);
          } catch {
            // Keep as string if parsing fails
          }
        }
        setQuiz(quizData);
      }
      if (data.tool === "search") {
        let searchData = data.result.results;
        if (typeof searchData === "string") {
          try {
            searchData = JSON.parse(searchData);
          } catch {
            // Keep as string if parsing fails
          }
        }
        setSearchResults(searchData);
      }
    },
    onError(error: any) {
      toast.error(error?.response?.data?.detail ?? "Unable to run assistant tool.");
    }
  });

  const sendMessage = React.useCallback(async (overrideText?: string | React.FormEvent | React.MouseEvent) => {
    if (overrideText && typeof overrideText !== "string" && 'preventDefault' in (overrideText as any)) {
      (overrideText as any).preventDefault();
    }
    const promptText = typeof overrideText === "string" ? overrideText : input;
    const prompt = promptText.trim();
    if (!prompt) {
      return;
    }
    setLocalSuggestions([]);

    if (typeof overrideText !== "string") {
      setInput("");
    }
    const optimisticAssistantId = createId("assistant");
    const optimisticUserMessage: ChatMessage = {
      id: createId("user"),
      role: "user",
      content: prompt,
      createdAt: formatMessageTime(new Date().toISOString())
    };

    setInput("");

    let conversationId = activeConversationId;
    const isNewConversation = !conversationId;
    if (isNewConversation) {
      conversationId = "temp-" + Date.now();
      React.startTransition(() => {
        setIsDraftConversation(false);
        setActiveConversationId(conversationId);
      });
      setTimeout(() => {
        document.getElementById("chat-input")?.focus();
      }, 0);
    }

    updateConversationCache(conversationId!, (current) => ({
      ...(current ?? {
        id: conversationId!,
        userId: "",
        title: "New conversation",
        summary: prompt,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isFavorite: false,
        messageCount: 0,
        lastMessagePreview: prompt,
        messages: []
      }),
      summary: prompt,
      updatedAt: new Date().toISOString(),
      messageCount: (current?.messageCount ?? 0) + 1,
      lastMessagePreview: prompt,
      messages: [...(current?.messages ?? []), optimisticUserMessage]
    }));

    updateConversationCache(conversationId!, (current) => ({
      ...(current as ConversationDetail),
      messages: [
        ...((current as ConversationDetail).messages ?? []),
        {
          id: optimisticAssistantId,
          role: "assistant",
          content: "",
          createdAt: formatMessageTime(new Date().toISOString()),
          isStreaming: settings.streamResponses
        }
      ]
    }));

    const updateAssistantMessage = (updater: (current: string) => string, done = false, targetId = conversationId!) => {
      updateConversationCache(targetId, (current) => ({
        ...(current as ConversationDetail),
        messages: (current?.messages ?? []).map((message) =>
          message.id !== optimisticAssistantId
            ? message
            : {
                ...message,
                content: updater(message.content),
                isStreaming: !done && settings.streamResponses
              }
        )
      }));
    };

    const handleNewConversationFinalized = (finalId: string, title?: string, summary?: string) => {
      setActiveConversationId(finalId);
      queryClient.setQueryData<ConversationPreview[]>(["conversations"], (old) => {
        return [
          {
            id: finalId,
            title: title || prompt.substring(0, 40),
            summary: summary || prompt,
            updatedAt: new Date().toISOString(),
            createdAt: new Date().toISOString(),
            isFavorite: false,
            messageCount: 2,
            lastMessagePreview: summary || prompt
          },
          ...(old ?? [])
        ];
      });

      const tempCache = queryClient.getQueryData<ConversationDetail>(["conversation", conversationId!]);
      if (tempCache) {
        queryClient.setQueryData(["conversation", finalId], {
          ...tempCache,
          id: finalId,
          title: title || prompt.substring(0, 40),
          summary: summary || prompt,
          lastMessagePreview: summary || prompt,
          updatedAt: new Date().toISOString(),
          messageCount: 2
        });
        queryClient.removeQueries({ queryKey: ["conversation", conversationId!] });
      }
    };

    try {
      const effectiveDocumentIds = selectedDocumentIds;
      console.log("[SEND] Selected doc IDs being sent:", effectiveDocumentIds);
      console.log("[SEND] Full payload:", { query: prompt, document_ids: effectiveDocumentIds, model: "llama3.2:3b" });
      if (settings.streamResponses) {
        await streamAssistantChat(
          {
            query: prompt,
            model: "llama3.2:3b" as StreamPayload["model"],
            top_k: 4,
            hybrid: true,
            conversation_id: isNewConversation ? undefined : conversationId,
            document_ids: effectiveDocumentIds
          } satisfies StreamPayload,
          {
            onThinking(step, message, docs) {
              updateConversationCache(conversationId!, (current) => {
                if (!current) return current as any;
                return {
                  ...current,
                  messages: (current.messages ?? []).map((message) =>
                    message.id !== optimisticAssistantId
                      ? message
                      : {
                          ...message,
                          thinkingState: { step, message, docs }
                        }
                  )
                };
              });
            },
            onContext(data) {
              const citations = (data.chunks || []).map((chunk: any) => ({
                chunk_id: chunk.metadata?.chunk_id || "",
                document_id: chunk.metadata?.document_id || "",
                filename: chunk.metadata?.filename || "Unknown Document",
                page: chunk.metadata?.page ? parseInt(chunk.metadata.page) : 1,
                chunk_index: chunk.metadata?.chunk_index ?? 0,
                paragraph_index: chunk.metadata?.paragraph_index ? parseInt(chunk.metadata.paragraph_index) : 1,
                content: chunk.content || ""
              }));

              updateConversationCache(conversationId!, (current) => {
                if (!current) return current as any;
                return {
                  ...current,
                  messages: (current.messages ?? []).map((message) =>
                    message.id !== optimisticAssistantId
                      ? message
                      : {
                          ...message,
                          citations: citations
                        }
                  )
                };
              });
            },
            onSuggestions(prompts) {
              setLocalSuggestions(prompts);
            },
            onToken(token) {
              updateAssistantMessage((current) => current + token);
            },
            onDone(data) {
              const finalId = data.conversation_id || conversationId;
              
              const citations = (data.citations || []).map((chunk: any) => ({
                chunk_id: chunk.metadata?.chunk_id || "",
                document_id: chunk.metadata?.document_id || "",
                filename: chunk.metadata?.filename || "Unknown Document",
                page: chunk.metadata?.page ? parseInt(chunk.metadata.page) : 1,
                chunk_index: chunk.metadata?.chunk_index ?? 0,
                paragraph_index: chunk.metadata?.paragraph_index ? parseInt(chunk.metadata.paragraph_index) : 1,
                content: chunk.content || ""
              }));

              if (data.suggestions) {
                setLocalSuggestions(data.suggestions);
              }

              if (isNewConversation && finalId) {
                handleNewConversationFinalized(finalId, data.conversation_title, data.answer);
                updateConversationCache(finalId, (current) => {
                  if (!current) return current as any;
                  return {
                    ...current,
                    messages: (current.messages ?? []).map((message) =>
                      message.id !== optimisticAssistantId
                        ? message
                        : {
                            ...message,
                            content: data.answer !== undefined ? data.answer : message.content,
                            isStreaming: false,
                            citations: citations.length > 0 ? citations : message.citations
                          }
                    )
                  };
                });
              } else {
                updateConversationCache(conversationId!, (current) => ({
                  ...(current as ConversationDetail),
                  title: data.conversation_title ?? current?.title ?? "New conversation",
                  summary: data.answer ?? current?.summary,
                  lastMessagePreview: data.answer ?? current?.lastMessagePreview,
                  updatedAt: new Date().toISOString(),
                  messageCount: current?.messageCount ?? 0
                }));
                updateConversationCache(conversationId!, (current) => {
                  if (!current) return current as any;
                  return {
                    ...current,
                    messages: (current.messages ?? []).map((message) =>
                      message.id !== optimisticAssistantId
                        ? message
                        : {
                            ...message,
                            content: data.answer !== undefined ? data.answer : message.content,
                            isStreaming: false,
                            citations: citations.length > 0 ? citations : message.citations
                          }
                    )
                  };
                });
              }
            },
            onError(message) {
              updateAssistantMessage(() => `⚠️ Error: ${message}`, true);
            }
          }
        );
      } else {
        const response = await queryAssistant({
          query: prompt,
          model: "llama3.2:3b",
          top_k: 4,
          hybrid: true,
          conversation_id: isNewConversation ? undefined : conversationId,
          document_ids: effectiveDocumentIds
        });
        
        const finalId = response.conversation_id || conversationId;
        if (isNewConversation && finalId) {
          handleNewConversationFinalized(finalId, response.conversation_title, response.answer);
          updateAssistantMessage(() => response.answer, true, finalId);
        } else {
          updateAssistantMessage(() => response.answer, true);
        }
      }

      await queryClient.invalidateQueries({ queryKey: ["conversations"] });
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail 
        || (error instanceof Error ? error.message : null)
        || (typeof error === "string" ? error : null)
        || "An unexpected error occurred";
        
      const finalMessage = typeof errorMessage !== "string" ? JSON.stringify(errorMessage) : errorMessage;
      
      updateAssistantMessage(() => `⚠️ Error: ${finalMessage}`, true);
      toast.error(finalMessage);
    }
  }, [
    activeConversationId,
    input,
    queryClient,
    selectedDocumentIds,
    settings.model,
    settings.streamResponses,
    updateConversationCache,
    allDocs
  ]);

  return {
    groupedConversations: groupConversations(conversationsQuery.data ?? []),
    activeConversation,
    activeConversationId,
    generatedSummary,
    historySearch,
    input,
    isConversationLoading: activeConversationQuery.isLoading,
    isHistoryLoading: conversationsQuery.isLoading,
    isSettingsOpen,
    isSidebarOpen,
    isWorkingTools: toolMutation.isPending,
    quiz,
    searchResults,
    selectedDocumentIds,
    settings,
    suggestedPrompts: localSuggestions.length > 0 ? localSuggestions : (suggestedPromptsQuery.data ?? []),
    setHistorySearch,
    setInput,
    setIsSidebarOpen,
    setIsSettingsOpen,
    setSelectedDocumentIds,
    createConversation: createConversationDraft,
    deleteConversation: removeConversation,
    exportConversation: exportCurrentConversation,
    favoriteConversation: markFavoriteConversation,
    pinConversation: togglePinConversation,
    isFilterFavorites,
    setIsFilterFavorites,
    filterDateFrom,
    setFilterDateFrom,
    filterDateTo,
    setFilterDateTo,
    generateQuiz: async () => toolMutation.mutateAsync("quiz").then(() => undefined),
    generateSummary: async () => toolMutation.mutateAsync("summary").then(() => undefined),
    renameConversation: renameStoredConversation,
    runSemanticSearch: async () => toolMutation.mutateAsync("search").then(() => undefined),
    selectConversation,
    updateSettings,
    useSuggestedPrompt: setInput,
    sendMessage
  };
}
