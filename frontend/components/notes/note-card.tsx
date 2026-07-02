"use client";

import { Note } from "@/types/api";
import { Pin, Calendar, Tag, Trash } from "lucide-react";
import { Button } from "@/components/ui/button";

interface NoteCardProps {
  note: Note;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onTogglePin: (e: React.MouseEvent) => void;
}

export function NoteCard({ note, isActive, onSelect, onDelete, onTogglePin }: NoteCardProps) {
  const formattedDate = new Date(note.updated_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  });

  return (
    <div
      onClick={onSelect}
      className={`group relative flex flex-col rounded-xl border p-4 cursor-pointer transition-all duration-200 select-none ${
        isActive
          ? "border-indigo-500/50 bg-indigo-500/5 shadow-md"
          : "border-border/40 bg-[var(--assistant-bubble)] hover:border-border hover:bg-[var(--border-color)]"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <h4 className="truncate text-sm font-semibold text-white/95 flex-1 pr-6">
          {note.title || "Untitled Note"}
        </h4>
        
        <button
          onClick={onTogglePin}
          className={`absolute top-4 right-4 h-6 w-6 flex items-center justify-center rounded hover:bg-white/5 transition-colors ${
            note.is_pinned ? "text-indigo-400" : "text-muted-foreground opacity-0 group-hover:opacity-100"
          }`}
          title={note.is_pinned ? "Unpin Note" : "Pin Note"}
          type="button"
        >
          <Pin className="h-3.5 w-3.5 fill-current" />
        </button>
      </div>

      <p className="mt-1.5 text-xs text-muted-foreground line-clamp-2 leading-relaxed flex-1">
        {note.content || "Empty content..."}
      </p>

      <div className="mt-3 flex items-center justify-between border-t border-border/10 pt-2.5 text-[10px] text-muted-foreground shrink-0">
        <span className="flex items-center gap-1.5 font-medium">
          <Calendar className="h-3 w-3 text-indigo-400" />
          {formattedDate}
        </span>

        <div className="flex items-center gap-1.5">
          {note.tags && (
            <span className="flex items-center gap-1 bg-indigo-500/10 text-indigo-400 px-1.5 py-0.5 rounded font-medium">
              <Tag className="h-2.5 w-2.5" />
              {note.tags.split(",")[0]}
            </span>
          )}

          <Button
            size="icon"
            variant="ghost"
            onClick={onDelete}
            className="h-6 w-6 text-muted-foreground hover:bg-destructive/20 hover:text-destructive rounded opacity-0 group-hover:opacity-100 transition-opacity"
            title="Delete Note"
          >
            <Trash className="h-3 w-3" />
          </Button>
        </div>
      </div>
    </div>
  );
}
