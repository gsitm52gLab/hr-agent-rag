"use client";
import dynamic from "next/dynamic";
import type { ChatMessage } from "@/lib/types";
import StreamingText from "./StreamingText";
import SourceCard from "./SourceCard";

const PromotionChart = dynamic(() => import("./PromotionChart"), { ssr: false });

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming: boolean;
  isLast: boolean;
}

export default function MessageBubble({ message, isStreaming, isLast }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-5 py-3 ${
          isUser
            ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white"
            : "bg-surface border border-surface-border text-gray-200"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <>
            <StreamingText
              content={message.content}
              isStreaming={isStreaming && isLast}
            />
            {message.sources && <SourceCard sources={message.sources} />}
            {message.promotion_stats && message.promotion_stats.length > 0 && (
              <PromotionChart data={message.promotion_stats} />
            )}
            {message.contacts && message.contacts.length > 0 && (
              <div className="mt-3 pt-3 border-t border-surface-border">
                <p className="text-xs text-gray-400 mb-2 flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  담당자 안내
                </p>
                <div className="flex flex-wrap gap-2">
                  {message.contacts.map((c, i) => (
                    <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-dark/50 border border-surface-border text-xs">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                        {c.name[0]}
                      </div>
                      <div>
                        <div className="text-white font-medium">{c.name} <span className="text-gray-400 font-normal">{c.position}</span></div>
                        <div className="text-gray-500">{c.department} | {c.role}</div>
                        <div className="text-blue-400">{c.phone} · {c.email}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
