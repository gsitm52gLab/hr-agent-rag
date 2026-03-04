"use client";
import { useState } from "react";
import type { Source } from "@/lib/types";

interface SourceCardProps {
  sources: Source[];
}

export default function SourceCard({ sources }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-purple-400 hover:text-purple-300 transition-colors"
      >
        <svg
          className={`w-4 h-4 transition-transform ${expanded ? "rotate-90" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        참조 규정 ({sources.length}개)
      </button>
      {expanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source, i) => (
            <div
              key={i}
              className="rounded-lg bg-white/5 border border-white/10 p-3 text-sm"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2 py-0.5 rounded-full bg-purple-600/30 text-purple-300 text-xs font-medium">
                  {source.document}
                </span>
                <span className="text-gray-400 text-xs">{source.section}</span>
              </div>
              <p className="text-gray-300 text-xs leading-relaxed line-clamp-3">
                {source.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
