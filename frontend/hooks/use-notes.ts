"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listNotes,
  createNote,
  getNote,
  updateNote,
  deleteNote,
  togglePinNote
} from "@/lib/api";
import type { NoteCreate, NoteUpdate } from "@/types/api";

export function useNotes(search?: string, pinnedOnly = false) {
  const queryClient = useQueryClient();

  const notesQuery = useQuery({
    queryKey: ["notes", search, pinnedOnly],
    queryFn: () => listNotes({ search, pinned_only: pinnedOnly }),
    staleTime: 5000
  });

  const createMutation = useMutation({
    mutationFn: (payload: NoteCreate) => createNote(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notes"] });
      toast.success("Note created successfully");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to create note");
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ noteId, payload }: { noteId: string; payload: NoteUpdate }) =>
      updateNote(noteId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notes"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to save note");
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (noteId: string) => deleteNote(noteId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notes"] });
      toast.success("Note deleted successfully");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to delete note");
    }
  });

  const togglePinMutation = useMutation({
    mutationFn: (noteId: string) => togglePinNote(noteId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notes"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to pin/unpin note");
    }
  });

  return {
    notes: notesQuery.data ?? [],
    isLoading: notesQuery.isLoading,
    isCreating: createMutation.isPending,
    isDeleting: deleteMutation.isPending,
    createNote: createMutation.mutateAsync,
    updateNote: (noteId: string, payload: NoteUpdate) =>
      updateMutation.mutateAsync({ noteId, payload }),
    deleteNote: deleteMutation.mutateAsync,
    togglePinNote: togglePinMutation.mutateAsync
  };
}
