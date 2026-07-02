"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { useTheme } from "next-themes";
import { X } from "lucide-react";

import type { AssistantSettings } from "@/types/chat";

const models: AssistantSettings["model"][] = [
  "llama3.2:3b",
  "llama3", 
  "mistral",
  "deepseek-r1:7b",
  "deepseek-r1:1.5b"
];

export function SettingsModal({
  onOpenChange,
  onSave,
  open,
  settings
}: {
  onOpenChange: (open: boolean) => void;
  onSave: (settings: AssistantSettings) => void;
  open: boolean;
  settings: AssistantSettings;
}) {
  const [draft, setDraft] = React.useState(settings);
  const { setTheme } = useTheme();

  React.useEffect(() => {
    setDraft(settings);
  }, [settings]);

  React.useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };

    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, onOpenChange]);

  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);

  if (!open || !mounted) return null;

  return createPortal(
    <div 
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg max-h-[80vh] overflow-y-auto rounded-[16px] border border-[var(--border-color)] bg-[var(--assistant-bubble)] p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Workspace Settings</h2>
          <button
            onClick={() => onOpenChange(false)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">Preferred Model</label>
            <select
              value={draft.model}
              onChange={(e) => setDraft((curr) => ({ ...curr, model: e.target.value as any }))}
              className="w-full rounded-lg border border-[var(--border-color)] bg-[var(--bg-panel)] px-3 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">Workspace Theme</label>
            <select
              value={draft.theme}
              onChange={(e) => setDraft((curr) => ({ ...curr, theme: e.target.value as any }))}
              className="w-full rounded-lg border border-[var(--border-color)] bg-[var(--bg-panel)] px-3 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="oled">OLED Black</option>
              <option value="purple">Midnight Purple</option>
              <option value="blue">Deep Ocean Blue</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-200">Response Mode</label>
            <div className="flex rounded-lg border border-[var(--border-color)] bg-[var(--bg-panel)] p-1">
              <button
                type="button"
                onClick={() => setDraft((curr) => ({ ...curr, streamResponses: true }))}
                className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  draft.streamResponses ? "bg-[#2d2d2d] text-white shadow" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Streaming
              </button>
              <button
                type="button"
                onClick={() => setDraft((curr) => ({ ...curr, streamResponses: false }))}
                className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  !draft.streamResponses ? "bg-[#2d2d2d] text-white shadow" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Complete
              </button>
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-3">
          <button
            onClick={() => {
              setTheme(draft.theme);
              onSave(draft);
              onOpenChange(false);
            }}
            className="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-indigo-700"
          >
            Save Changes
          </button>
          <button
            onClick={() => onOpenChange(false)}
            className="w-full rounded-lg border border-[var(--border-color)] bg-transparent px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-white/5"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
