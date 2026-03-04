"use client";
import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
import { getConversation } from "@/lib/api";
import Sidebar from "@/components/sidebar/Sidebar";
import ChatInterface from "@/components/chat/ChatInterface";
import type { ChatMessage } from "@/lib/types";

export default function Home() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>();
  const [loadedMessages, setLoadedMessages] = useState<ChatMessage[] | undefined>();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [key, setKey] = useState(0);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.push("/login");
    }
  }, [router]);

  const handleSelectConversation = useCallback(async (id: string) => {
    try {
      const detail = await getConversation(id);
      setActiveConversationId(id);
      setLoadedMessages(detail.messages);
      setKey((k) => k + 1);
    } catch { /* ignore */ }
  }, []);

  const handleNewConversation = useCallback(() => {
    setActiveConversationId(undefined);
    setLoadedMessages(undefined);
    setKey((k) => k + 1);
  }, []);

  const handleConversationCreated = useCallback(() => {
    setRefreshTrigger((t) => t + 1);
  }, []);

  return (
    <div className="flex h-screen bg-dark">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        refreshTrigger={refreshTrigger}
      />

      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-surface-border bg-dark/80 backdrop-blur-xl">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="text-sm text-gray-400">
            {activeConversationId ? "대화 계속" : "새 대화"}
          </span>
        </header>

        <div className="flex-1 min-h-0">
          <ChatInterface
            key={key}
            onConversationCreated={handleConversationCreated}
            initialMessages={loadedMessages}
            initialConversationId={activeConversationId}
          />
        </div>
      </main>
    </div>
  );
}
