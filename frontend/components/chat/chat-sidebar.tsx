"use client";

import * as React from "react";
import {
  Clock3,
  Download,
  Edit3,
  Heart,
  LogOut,
  MessageSquare,
  MoreHorizontal,
  Plus,
  Search,
  Settings,
  Sparkles,
  Trash2,
  Sun,
  Moon
} from "lucide-react";

import { useTheme } from "next-themes";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { ConversationGroup, ConversationPreview } from "@/types/chat";
import { ProfileDropdown } from "@/components/chat/profile-dropdown";

function formatRelativeTime(timestamp: string) {
  const date = new Date(timestamp);
  const diffMs = date.getTime() - Date.now();
  const diffMinutes = Math.round(diffMs / 60000);
  const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

  if (Math.abs(diffMinutes) < 60) {
    return formatter.format(diffMinutes, "minute");
  }

  const diffHours = Math.round(diffMinutes / 60);
  if (Math.abs(diffHours) < 24) {
    return formatter.format(diffHours, "hour");
  }

  return formatter.format(Math.round(diffHours / 24), "day");
}

function ConversationItem({
  conversation,
  active,
  onSelect,
  onFavorite,
  onRename,
  onExport,
  onDelete
}: {
  conversation: ConversationPreview;
  active: boolean;
  onSelect: () => void;
  onFavorite: () => void;
  onRename: () => void;
  onExport: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      className={cn(
        "group rounded-xl border-l-[3px] transition-all duration-150 p-3",
        active
          ? "border-[#6366f1] bg-[var(--bg-panel)] shadow-md"
          : "border-transparent bg-transparent hover:bg-[var(--bg-panel)]"
      )}
    >
      <div className="flex items-start gap-3">
        <button
          className="min-w-0 flex-1 text-left"
          onClick={onSelect}
          type="button"
        >
          <div className="flex items-start justify-between gap-3">
            <p className="line-clamp-1 text-sm font-medium">
              {conversation.title.length > 35 ? conversation.title.substring(0, 35) + "..." : conversation.title}
            </p>
            <span className="shrink-0 text-[11px] text-muted-foreground">
              {formatRelativeTime(conversation.updatedAt)}
            </span>
          </div>
          <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
            {conversation.lastMessagePreview ??
              conversation.summary ??
              "Open this conversation to continue chatting."}
          </p>
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              className="mt-1 h-8 w-8 rounded-full opacity-0 transition group-hover:opacity-100"
              size="icon"
              variant="ghost"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            <DropdownMenuItem onClick={onFavorite}>
              <Heart
                className={cn(
                  "mr-2 h-4 w-4",
                  conversation.isFavorite ? "fill-current text-rose-500" : ""
                )}
              />
              {conversation.isFavorite ? "Unfavorite" : "Favorite"}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onRename}>
              <Edit3 className="mr-2 h-4 w-4" />
              Rename
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onExport}>
              <Download className="mr-2 h-4 w-4" />
              Export
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={onDelete}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

export function ChatSidebar({
  activeConversationId,
  groupedConversations,
  historySearch,
  isLoading,
  onCreateConversation,
  onDeleteConversation,
  onExportConversation,
  onFavoriteConversation,
  onHistorySearchChange,
  onRenameConversation,
  onSelectConversation,
  onOpenSettings,
  sidebarOpen,
}: {
  activeConversationId?: string;
  groupedConversations: ConversationGroup[];
  historySearch: string;
  isLoading: boolean;
  onCreateConversation: () => void;
  onDeleteConversation: (conversationId: string) => Promise<void>;
  onExportConversation: (conversationId: string) => Promise<void>;
  onFavoriteConversation: (conversationId: string, favorite: boolean) => Promise<void>;
  onHistorySearchChange: (value: string) => void;
  onRenameConversation: (conversationId: string, title: string) => Promise<void>;
  onSelectConversation: (conversationId: string) => void;
  onOpenSettings?: () => void;
  sidebarOpen?: boolean;
}) {
  const [renameTarget, setRenameTarget] = React.useState<{
    id: string;
    title: string;
  } | null>(null);
  const [renameValue, setRenameValue] = React.useState("");
  const [isMounted, setIsMounted] = React.useState(false);
  const [hoveredConvId, setHoveredConvId] = React.useState<string | null>(null);
  const { user, logoutUser } = useAuth();
  const { theme, setTheme } = useTheme();

  React.useEffect(() => {
    setIsMounted(true);
  }, []);

  // Client-side search filter on top of whatever groupedConversations provides
  const searchLower = historySearch.toLowerCase().trim();
  const filteredGroups: ConversationGroup[] = React.useMemo(() => {
    if (!searchLower) return groupedConversations;
    return groupedConversations
      .map((group) => ({
        ...group,
        conversations: group.conversations.filter(
          (c) =>
            c.title.toLowerCase().includes(searchLower) ||
            (c.lastMessagePreview ?? "").toLowerCase().includes(searchLower) ||
            (c.summary ?? "").toLowerCase().includes(searchLower)
        )
      }))
      .filter((group) => group.conversations.length > 0);
  }, [groupedConversations, searchLower]);

  const totalConversations = filteredGroups.reduce(
    (sum, g) => sum + g.conversations.length,
    0
  );
  const hasConversations = totalConversations > 0;

  async function handleRenameSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!renameTarget || !renameValue.trim()) return;
    await onRenameConversation(renameTarget.id, renameValue.trim());
    setRenameTarget(null);
    setRenameValue("");
  }

  const flattenedConversations = filteredGroups.flatMap(g => g.conversations);

  return (
    <>
      <aside className="sidebar-panel" style={{
        width: sidebarOpen ? '240px' : '0px',
        minWidth: sidebarOpen ? '240px' : '0px',
        height: '100vh',
        background: '#0d0d0d',
        borderRight: sidebarOpen ? '1px solid #1e1e1e' : 'none',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        transition: 'width 0.25s ease, min-width 0.25s ease, border-right 0.25s ease',
        flexShrink: 0,
      }}>
        <div style={{ width: '240px', height: '100%', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
          {/* ── Header ── */}
          <div style={{
            padding: '20px 16px 12px',
            borderBottom: '1px solid #1a1a1a',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <span style={{ fontSize: '20px' }}>✦</span>
            <span style={{ fontSize: '15px', fontWeight: 600, color: '#f1f1f1', letterSpacing: '-0.2px' }}>
              AI Assistant
            </span>
          </div>
          
          {/* New Chat button */}
          <button
            onClick={onCreateConversation}
            style={{
              width: '100%',
              padding: '9px 14px',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              border: 'none',
              borderRadius: '10px',
              color: '#fff',
              fontSize: '13px',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              marginBottom: '10px',
            }}
          >
            <span style={{ fontSize: '16px', lineHeight: 1 }}>+</span>
            New Chat
          </button>

          {/* Search */}
          <div style={{ position: 'relative' }}>
            <span style={{
              position: 'absolute', left: '10px', top: '50%',
              transform: 'translateY(-50%)', color: '#555', fontSize: '13px',
            }}>🔍</span>
            <input
              type="text"
              placeholder="Search..."
              value={historySearch}
              onChange={e => onHistorySearchChange(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px 8px 30px',
                background: '#1a1a1a',
                border: '1px solid #252525',
                borderRadius: '8px',
                color: '#d1d1d1',
                fontSize: '12px',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>
        </div>

        {/* ── Conversation List ── */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '8px 8px',
          scrollbarWidth: 'thin',
          scrollbarColor: '#2a2a2a transparent',
        }}>
          {flattenedConversations.length === 0 ? (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              justifyContent: 'center', height: '200px', gap: '10px',
            }}>
              <span style={{ fontSize: '28px', opacity: 0.3 }}>💬</span>
              <span style={{ fontSize: '12px', color: '#444', textAlign: 'center' }}>
                No conversations yet
              </span>
            </div>
          ) : (
            <>
              <div style={{
                fontSize: '10px', fontWeight: 600, color: '#444',
                letterSpacing: '0.8px', padding: '4px 8px 6px', textTransform: 'uppercase',
              }}>
                Recent
              </div>
              {flattenedConversations.map(conv => (
                <div
                  key={conv.id}
                  style={{ position: 'relative' }}
                  className="conv-item-wrapper"
                  onMouseEnter={() => setHoveredConvId(conv.id)}
                  onMouseLeave={() => setHoveredConvId(null)}
                >
                  <div
                    onClick={() => onSelectConversation(conv.id)}
                    style={{
                      padding: '9px 10px',
                      paddingRight: hoveredConvId === conv.id ? '30px' : '10px',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      marginBottom: '2px',
                      background: activeConversationId === conv.id ? '#1e1e2e' : 'transparent',
                      borderLeft: activeConversationId === conv.id ? '2px solid #6366f1' : '2px solid transparent',
                      transition: 'all 0.15s ease',
                    }}
                    onMouseEnter={e => {
                      if (activeConversationId !== conv.id)
                        (e.currentTarget as HTMLElement).style.background = '#161616'
                    }}
                    onMouseLeave={e => {
                      if (activeConversationId !== conv.id)
                        (e.currentTarget as HTMLElement).style.background = 'transparent'
                    }}
                  >
                    <div style={{
                      fontSize: '12.5px', fontWeight: 500, color: '#d1d1d1',
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                      marginBottom: '3px',
                    }}>
                      {conv.title || 'New conversation'}
                    </div>
                    <div style={{ fontSize: '11px', color: '#444' }}>
                      {formatRelativeTime(conv.updatedAt)}
                    </div>
                  </div>
                  
                  {hoveredConvId === conv.id && (
                    <button
                      onClick={async (e) => {
                        e.stopPropagation()
                        if (!confirm('Delete this conversation?')) return
                        try {
                          await onDeleteConversation(conv.id)
                        } catch (err) {
                          console.error('Delete failed:', err)
                        }
                      }}
                      style={{
                        position: 'absolute',
                        right: '6px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        background: 'none',
                        border: 'none',
                        color: '#ef4444',
                        cursor: 'pointer',
                        fontSize: '14px',
                        padding: '4px',
                        borderRadius: '4px',
                        lineHeight: 1,
                      }}
                      title="Delete conversation"
                    >
                      🗑
                    </button>
                  )}
                </div>
              ))}
            </>
          )}
        </div>

        {/* ── User Footer ── */}
        <div style={{
          padding: '12px 14px',
          borderTop: '1px solid #1a1a1a',
          flexShrink: 0,
        }}>
          <ProfileDropdown onOpenSettings={() => onOpenSettings?.()} />
        </div>
        </div>
      </aside>

      <Dialog
        open={Boolean(renameTarget)}
        onOpenChange={(open) => !open && setRenameTarget(null)}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Rename conversation</DialogTitle>
          </DialogHeader>
          <form className="space-y-4" onSubmit={(e) => void handleRenameSubmit(e)}>
            <Input
              autoFocus
              onChange={(e) => setRenameValue(e.target.value)}
              placeholder="Conversation title"
              value={renameValue}
            />
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setRenameTarget(null)}>
                Cancel
              </Button>
              <Button type="submit">Save</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
