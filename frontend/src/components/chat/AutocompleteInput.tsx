"use client";
import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { useAutocomplete } from "@/hooks/useAutocomplete";

interface AutocompleteInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function AutocompleteInput({ onSend, disabled }: AutocompleteInputProps) {
  const [input, setInput] = useState("");
  const { results, isOpen, search, close } = useAutocomplete();
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  useEffect(() => {
    search(input);
    setSelectedIndex(-1);
  }, [input, search]);

  const handleSubmit = () => {
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput("");
    close();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (isOpen && results.length > 0) {
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev <= 0 ? results.length - 1 : prev - 1));
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev >= results.length - 1 ? 0 : prev + 1));
        return;
      }
      if (e.key === "Enter" && selectedIndex >= 0) {
        e.preventDefault();
        const selected = results[selectedIndex];
        if (selected.type === "recent" || selected.type === "example") {
          setInput(selected.text);
        } else {
          // Replace last word with the glossary term
          const words = input.split(/\s+/);
          words[words.length - 1] = selected.text;
          setInput(words.join(" "));
        }
        close();
        return;
      }
      if (e.key === "Escape") {
        close();
        return;
      }
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSelect = (index: number) => {
    const selected = results[index];
    if (selected.type === "recent" || selected.type === "example") {
      setInput(selected.text);
    } else {
      const words = input.split(/\s+/);
      words[words.length - 1] = selected.text;
      setInput(words.join(" "));
    }
    close();
    inputRef.current?.focus();
  };

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      {/* Autocomplete dropdown (opens upward) */}
      {isOpen && results.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-dark-light border border-surface-border rounded-xl shadow-2xl overflow-y-auto z-10 max-h-80">
          {results.map((item, i) => (
            <button
              key={i}
              className={`w-full px-4 py-3 text-left flex items-center gap-3 transition-colors ${
                i === selectedIndex
                  ? "bg-purple-600/20"
                  : "hover:bg-white/5"
              }`}
              onMouseDown={(e) => {
                e.preventDefault();
                handleSelect(i);
              }}
            >
              {item.type === "recent" ? (
                <>
                  <svg className="w-4 h-4 text-gray-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-gray-300 text-sm truncate">{item.text}</span>
                </>
              ) : item.type === "example" ? (
                <>
                  <svg className="w-4 h-4 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-gray-300 text-sm truncate">{item.text}</span>
                  {item.label && (
                    <span className="px-1.5 py-0.5 rounded-full bg-blue-600/20 text-blue-300 text-xs flex-shrink-0">
                      {item.label}
                    </span>
                  )}
                </>
              ) : (
                <>
                  <span className="px-2 py-0.5 rounded-full bg-purple-600/30 text-purple-300 text-xs font-medium flex-shrink-0">
                    {item.label || "용어"}
                  </span>
                  <div className="min-w-0">
                    <span className="text-white text-sm font-medium">{item.text}</span>
                    {item.definition && (
                      <span className="text-gray-500 text-xs ml-2 truncate">
                        {item.definition}
                      </span>
                    )}
                  </div>
                </>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="flex items-end gap-2 bg-surface border border-surface-border rounded-2xl p-2 focus-within:border-purple-500/50 transition-colors">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => setTimeout(close, 200)}
          placeholder="인사규정에 대해 질문하세요..."
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-gray-200 placeholder-gray-500 resize-none px-3 py-2 focus:outline-none text-sm max-h-32"
          style={{ minHeight: "40px" }}
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || disabled}
          className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 text-white flex items-center justify-center hover:from-purple-500 hover:to-blue-500 disabled:opacity-30 transition-all"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}
