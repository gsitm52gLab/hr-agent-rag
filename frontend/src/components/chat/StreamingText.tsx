"use client";
import { useCallback, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface StreamingTextProps {
  content: string;
  isStreaming: boolean;
}

function CopyTableButton({ tableRef }: { tableRef: React.RefObject<HTMLTableElement | null> }) {
  const handleCopy = useCallback(() => {
    if (!tableRef.current) return;
    const rows = tableRef.current.querySelectorAll("tr");
    const tsv = Array.from(rows)
      .map((row) =>
        Array.from(row.querySelectorAll("th, td"))
          .map((cell) => cell.textContent?.trim() || "")
          .join("\t")
      )
      .join("\n");

    navigator.clipboard.writeText(tsv).then(() => {
      const btn = tableRef.current?.parentElement?.querySelector(".copy-btn");
      if (btn) {
        btn.textContent = "복사됨!";
        setTimeout(() => { btn.textContent = "표 복사"; }, 1500);
      }
    });
  }, [tableRef]);

  return (
    <button
      onClick={handleCopy}
      className="copy-btn absolute top-1 right-1 px-2 py-0.5 text-xs bg-purple-600/40 hover:bg-purple-600/60 text-purple-200 rounded transition-colors"
    >
      표 복사
    </button>
  );
}

function TableWrapper({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLTableElement>(null);
  return (
    <div className="relative my-3 overflow-x-auto rounded-lg border border-surface-border bg-dark/50">
      <CopyTableButton tableRef={ref} />
      <table ref={ref} className="w-full text-sm">
        {children}
      </table>
    </div>
  );
}

export default function StreamingText({ content, isStreaming }: StreamingTextProps) {
  return (
    <div className="leading-relaxed markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ children }) => <TableWrapper>{children}</TableWrapper>,
          thead: ({ children }) => (
            <thead className="bg-purple-600/15 text-purple-200 text-xs uppercase">
              {children}
            </thead>
          ),
          tbody: ({ children }) => <tbody className="divide-y divide-surface-border/30">{children}</tbody>,
          tr: ({ children }) => (
            <tr className="hover:bg-white/5 transition-colors">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 text-left font-semibold whitespace-nowrap">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-1.5 text-gray-300 whitespace-nowrap">{children}</td>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-semibold text-white mt-4 mb-2">{children}</h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-base font-semibold text-white mt-3 mb-1.5">{children}</h4>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-white">{children}</strong>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-inside space-y-1 my-2 ml-2">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside space-y-1 my-2 ml-2">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-gray-200">{children}</li>
          ),
          p: ({ children }) => (
            <p className="my-1.5">{children}</p>
          ),
          hr: () => <hr className="my-3 border-surface-border/50" />,
        }}
      >
        {content}
      </ReactMarkdown>
      {isStreaming && (
        <span className="inline-block w-2 h-5 bg-purple-400 ml-0.5 animate-pulse rounded-sm" />
      )}
    </div>
  );
}
