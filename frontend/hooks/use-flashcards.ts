"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listFlashcards,
  createFlashcard,
  generateFlashcards as generateApi,
  updateFlashcard,
  deleteFlashcard
} from "@/lib/api";
import type { FlashcardCreate, FlashcardUpdate, FlashcardGenerateRequest } from "@/types/api";

export function useFlashcards(documentId?: string) {
  const queryClient = useQueryClient();

  const flashcardsQuery = useQuery({
    queryKey: ["flashcards", documentId],
    queryFn: () => listFlashcards(documentId),
    staleTime: 10000
  });

  const createMutation = useMutation({
    mutationFn: (payload: FlashcardCreate) => createFlashcard(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["flashcards"] });
      toast.success("Flashcard added");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to create flashcard");
    }
  });

  const generateMutation = useMutation({
    mutationFn: (payload: FlashcardGenerateRequest) => generateApi(payload),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["flashcards"] });
      toast.success(`Generated ${data.length} flashcards successfully!`);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to generate flashcards");
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ cardId, payload }: { cardId: string; payload: FlashcardUpdate }) =>
      updateFlashcard(cardId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["flashcards"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to update flashcard");
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (cardId: string) => deleteFlashcard(cardId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["flashcards"] });
      toast.success("Flashcard deleted");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to delete flashcard");
    }
  });

  return {
    flashcards: flashcardsQuery.data ?? [],
    isLoading: flashcardsQuery.isLoading,
    isGenerating: generateMutation.isPending,
    createFlashcard: createMutation.mutateAsync,
    generateFlashcards: generateMutation.mutateAsync,
    updateFlashcard: (cardId: string, payload: FlashcardUpdate) =>
      updateMutation.mutateAsync({ cardId, payload }),
    deleteFlashcard: deleteMutation.mutateAsync
  };
}
