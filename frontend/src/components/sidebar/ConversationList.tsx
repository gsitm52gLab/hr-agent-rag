"use client";
import type { Conversation } from "@/lib/types";
import { deleteConversation } from "@/lib/api";
import { useState } from "react";

interface ConversationListProps {
  conversations: Conversation[];
  activeId?: string;
  onSelect: (id: string) => void;
  onRefresh: () => void;
}

export default function ConversationList({
  conversations,
  activeId,
  onSelect,
  onRefresh,
}: ConversationListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setDeletingId(id);
    try {
      await deleteConversation(id);
      onRefresh();
    } finally {
      setDeletingId(null);
    }
  };

  if (conversations.length === 0) {
    return (
      <div className="px-4 py-8 text-center text-gray-500 text-sm">
        대화 기록이 없습니다
      </div>
    );
  }

  return (
    <div className="space-y-1 px-2">
      {conversations.map((conv) => (
        <div
          key={conv.id}
          role="button"
          tabIndex={0}
          onClick={() => onSelect(conv.id)}
          onKeyDown={(e) => e.key === "Enter" && onSelect(conv.id)}
          className={`w-full text-left px-3 py-2.5 rounded-xl group flex items-center justify-between transition-colors cursor-pointer ${
            activeId === conv.id
              ? "bg-purple-600/20 text-white"
              : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
          }`}
        >
          <span className="truncate text-sm flex-1">{conv.title}</span>
          <button
            onClick={(e) => handleDelete(e, conv.id)}
            disabled={deletingId === conv.id}
            className="opacity-0 group-hover:opacity-100 ml-2 text-gray-500 hover:text-red-400 transition-all flex-shrink-0"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}
