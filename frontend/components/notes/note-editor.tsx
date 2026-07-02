"use client";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import { Note } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Pin, Eye, Edit3, Save, Tag, Loader2 } from "lucide-react";
import { useDebouncedValue } from "@/hooks/use-debounced-value";

interface NoteEditorProps {
  note: Note;
  onSave: (payload: { title?: string; content?: string; tags?: string | null }) => Promise<any>;
  onTogglePin: () => Promise<any>;
}

export function NoteEditor({ note, onSave, onTogglePin }: NoteEditorProps) {
  const [title, setTitle] = React.useState(note.title);
  const [content, setContent] = React.useState(note.content);
  const [tags, setTags] = React.useState(note.tags ?? "");
  const [mode, setMode] = React.useState<"edit" | "preview">("edit");
  const [isSaving, setIsSaving] = React.useState(false);

  // Sync state when active note changes
  React.useEffect(() => {
    setTitle(note.title);
    setContent(note.content);
    setTags(note.tags ?? "");
  }, [note]);

  // Debounced auto-save content changes
  const debouncedContent = useDebouncedValue(content, 1000);
  const debouncedTitle = useDebouncedValue(title, 1000);
  const debouncedTags = useDebouncedValue(tags, 1000);

  React.useEffect(() => {
    const hasChanged = 
      debouncedTitle !== note.title || 
      debouncedContent !== note.content || 
      debouncedTags !== (note.tags ?? "");

    if (hasChanged) {
      setIsSaving(true);
      onSave({
        title: debouncedTitle,
        content: debouncedContent,
        tags: debouncedTags ? debouncedTags.trim() : null
      }).finally(() => setIsSaving(false));
    }
  }, [debouncedContent, debouncedTitle, debouncedTags, note, onSave]);

  const handleManualSave = () => {
    setIsSaving(true);
    onSave({ title, content, tags: tags ? tags.trim() : null })
      .finally(() => setIsSaving(false));
  };

  return (
    <div className="flex h-full flex-col bg-[var(--bg-chat)] border border-border/40 rounded-2xl shadow-xl overflow-hidden">
      {/* Editor Header Bar */}
      <div className="flex items-center justify-between border-b border-border/40 p-4 bg-[var(--assistant-bubble)] shrink-0">
        <div className="flex-1 mr-4">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Untitled Note"
            className="w-full bg-transparent text-sm font-semibold text-white focus:outline-none placeholder:text-muted-foreground"
          />
        </div>

        <div className="flex items-center gap-1.5">
          {/* Status Label */}
          {isSaving ? (
            <span className="flex items-center gap-1 text-[10px] text-muted-foreground mr-1.5 font-medium">
              <Loader2 className="h-3 w-3 animate-spin text-indigo-400" /> Saving...
            </span>
          ) : (
            <span className="text-[10px] text-muted-foreground mr-1.5 font-medium">
              Auto-saved
            </span>
          )}

          {/* Toggle Pinned */}
          <Button
            size="icon"
            variant="ghost"
            onClick={onTogglePin}
            className={`h-8 w-8 rounded-lg ${note.is_pinned ? "text-indigo-400 hover:text-indigo-300" : "text-muted-foreground hover:bg-[var(--border-color)]"}`}
            title={note.is_pinned ? "Unpin Note" : "Pin Note"}
          >
            <Pin className={`h-4 w-4 ${note.is_pinned ? "fill-current" : ""}`} />
          </Button>

          {/* Toggle View Mode */}
          <Button
            size="sm"
            variant="outline"
            onClick={() => setMode(mode === "edit" ? "preview" : "edit")}
            className="rounded-lg bg-[var(--border-color)] hover:bg-[#333333] border-0 text-xs font-semibold text-white gap-1.5 h-8"
          >
            {mode === "edit" ? (
              <>
                <Eye className="h-3.5 w-3.5" /> Preview
              </>
            ) : (
              <>
                <Edit3 className="h-3.5 w-3.5" /> Edit
              </>
            )}
          </Button>

          <Button
            size="sm"
            onClick={handleManualSave}
            className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-xs font-semibold text-white gap-1.5 h-8"
          >
            <Save className="h-3.5 w-3.5" /> Save
          </Button>
        </div>
      </div>

      {/* Editor Content Area */}
      <div className="flex-1 overflow-auto flex flex-col min-h-0 bg-[var(--bg-primary)]">
        {mode === "edit" ? (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Start writing notes in markdown format..."
            className="flex-1 w-full bg-transparent p-6 text-sm text-white resize-none focus:outline-none font-mono leading-relaxed placeholder:text-muted-foreground/60"
          />
        ) : (
          <div className="flex-1 p-6 overflow-auto markdown-body prose prose-invert max-w-none text-sm text-white/95 leading-relaxed">
            {content.trim() ? (
              <ReactMarkdown>{content}</ReactMarkdown>
            ) : (
              <span className="text-muted-foreground/60 italic">No content to preview.</span>
            )}
          </div>
        )}
      </div>

      {/* Editor Footer / Tag Input */}
      <div className="border-t border-border/40 p-3 bg-[var(--assistant-bubble)] flex items-center gap-2 shrink-0">
        <Tag className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
        <input
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="Add comma-separated tags (e.g. math, project-management, unit-4)"
          className="flex-1 bg-transparent text-xs text-white focus:outline-none placeholder:text-muted-foreground/60"
        />
      </div>
    </div>
  );
}
