"use client";
import { useState, useCallback, useRef, useEffect } from "react";
import { searchGlossary, getRecentSearches, getExampleQuestions } from "@/lib/api";
import type { GlossaryItem, RecentSearch, ExampleQuestion } from "@/lib/types";

interface AutocompleteResult {
  type: "recent" | "glossary" | "example";
  text: string;
  label?: string;
  definition?: string;
}

export function useAutocomplete() {
  const [results, setResults] = useState<AutocompleteResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const search = useCallback((input: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!input.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      try {
        const trimmed = input.trim();
        const words = trimmed.split(/\s+/);
        const lastWord = words[words.length - 1];

        // Get recent searches, glossary, and example questions in parallel
        const [recent, glossary, examples] = await Promise.all([
          trimmed.length <= 1
            ? getRecentSearches(trimmed)
            : Promise.resolve([] as RecentSearch[]),
          lastWord.length >= 1
            ? searchGlossary(lastWord)
            : Promise.resolve([] as GlossaryItem[]),
          trimmed.length >= 1
            ? getExampleQuestions(trimmed)
            : Promise.resolve([] as ExampleQuestion[]),
        ]);

        const items: AutocompleteResult[] = [];

        // Recent searches (only for first character input)
        if (trimmed.length <= 1 && recent.length > 0) {
          recent.forEach((r) => {
            items.push({ type: "recent", text: r.query });
          });
        }

        // Example questions (matching user input)
        examples.forEach((eq) => {
          items.push({
            type: "example",
            text: eq.question,
            label: eq.category || undefined,
          });
        });

        // Glossary matches
        glossary.forEach((g) => {
          items.push({
            type: "glossary",
            text: g.term,
            label: g.category || undefined,
            definition: g.definition,
          });
        });

        setResults(items);
        setIsOpen(items.length > 0);
      } catch {
        setResults([]);
        setIsOpen(false);
      }
    }, 200);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
  }, []);

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return { results, isOpen, search, close };
}
