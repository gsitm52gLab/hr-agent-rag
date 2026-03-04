"use client";
import { useRef, useEffect } from "react";
import { useChat } from "@/hooks/useChat";
import MessageBubble from "./MessageBubble";
import AutocompleteInput from "./AutocompleteInput";
import type { ChatMessage } from "@/lib/types";

interface ChatInterfaceProps {
  onConversationCreated?: () => void;
  initialMessages?: ChatMessage[];
  initialConversationId?: string;
}

export default function ChatInterface({
  onConversationCreated,
  initialMessages,
  initialConversationId,
}: ChatInterfaceProps) {
  const { messages, isStreaming, sendMessage, stopStreaming, loadConversation } = useChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialMessages && initialConversationId) {
      loadConversation(initialConversationId, initialMessages);
    }
  }, [initialConversationId, initialMessages, loadConversation]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text: string) => {
    await sendMessage(text);
    onConversationCreated?.();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center mb-6">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-white mb-2">HR Agent</h2>
            <p className="text-gray-400 max-w-md">
              인사규정에 대해 궁금한 점을 질문해주세요.
              <br />
              채용, 근무, 휴가, 급여 등 다양한 규정을 안내해드립니다.
            </p>
            <div className="flex flex-wrap gap-2 mt-6 justify-center">
              {["연차휴가 규정이 궁금해요", "야근수당은 어떻게 계산하나요?", "승진 기준을 알려주세요"].map(
                (q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-gray-300 text-sm hover:bg-white/10 transition-colors"
                  >
                    {q}
                  </button>
                )
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto">
            {messages.map((msg, i) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                isStreaming={isStreaming}
                isLast={i === messages.length - 1}
              />
            ))}
            <div ref={scrollRef} />
          </div>
        )}
      </div>

      {/* Input area - fixed height border container + floating content */}
      <div className="flex-shrink-0 relative h-[69px]">
        <div className="absolute bottom-0 left-0 right-0 z-10 bg-dark/80 backdrop-blur-xl px-4 py-4">
          {isStreaming && (
            <div className="flex justify-center mb-2">
              <button
                onClick={stopStreaming}
                className="px-4 py-1.5 rounded-full bg-white/10 text-gray-300 text-xs hover:bg-white/20 transition-colors"
              >
                응답 중지
              </button>
            </div>
          )}
          <AutocompleteInput onSend={handleSend} disabled={isStreaming} />
        </div>
      </div>
    </div>
  );
}
