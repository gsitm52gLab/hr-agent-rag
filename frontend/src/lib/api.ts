import { getToken } from "./auth";
import type {
  LoginResponse,
  Conversation,
  ConversationDetail,
  GlossaryItem,
  DocumentInfo,
  SearchStats,
  RecentSearch,
  ExampleQuestion,
  OrgChart,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function fetchAPI<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API Error ${res.status}: ${body}`);
  }
  return res.json();
}

// Auth
export async function login(username: string, password: string): Promise<LoginResponse> {
  return fetchAPI("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

// Chat - streaming
export function chatStream(
  message: string,
  conversationId?: string
): { reader: ReadableStreamDefaultReader<Uint8Array>; abort: () => void } {
  const token = getToken();
  const controller = new AbortController();
  const body = JSON.stringify({
    message,
    conversation_id: conversationId || null,
  });

  const fetchPromise = fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body,
    signal: controller.signal,
  });

  const readerPromise = fetchPromise.then((res) => {
    if (!res.ok) throw new Error(`Chat API Error ${res.status}`);
    return res.body!.getReader();
  });

  // Return a proxy reader that awaits the promise
  let resolvedReader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  const proxyReader: ReadableStreamDefaultReader<Uint8Array> = {
    read: async () => {
      if (!resolvedReader) resolvedReader = await readerPromise;
      return resolvedReader.read();
    },
    releaseLock: () => resolvedReader?.releaseLock(),
    cancel: async (reason?: unknown) => {
      if (resolvedReader) return resolvedReader.cancel(reason);
    },
    closed: readerPromise.then((r) => r.closed),
  };

  return { reader: proxyReader, abort: () => controller.abort() };
}

// Conversations
export async function getConversations(): Promise<Conversation[]> {
  return fetchAPI("/api/chat/history");
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  return fetchAPI(`/api/chat/history/${id}`);
}

export async function deleteConversation(id: string): Promise<void> {
  await fetchAPI(`/api/chat/history/${id}`, { method: "DELETE" });
}

// Glossary
export async function searchGlossary(q: string): Promise<GlossaryItem[]> {
  return fetchAPI(`/api/glossary/search?q=${encodeURIComponent(q)}`);
}

export async function getGlossary(): Promise<GlossaryItem[]> {
  return fetchAPI("/api/glossary");
}

export async function createGlossary(data: { term: string; definition: string; category?: string; aliases?: string }): Promise<GlossaryItem> {
  return fetchAPI("/api/glossary", { method: "POST", body: JSON.stringify(data) });
}

export async function updateGlossary(id: number, data: { term?: string; definition?: string; category?: string; aliases?: string }): Promise<GlossaryItem> {
  return fetchAPI(`/api/glossary/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export async function deleteGlossary(id: number): Promise<void> {
  await fetchAPI(`/api/glossary/${id}`, { method: "DELETE" });
}

// History
export async function getRecentSearches(q?: string): Promise<RecentSearch[]> {
  const params = q ? `?q=${encodeURIComponent(q)}` : "";
  return fetchAPI(`/api/history/recent${params}`);
}

// Example questions
export async function getExampleQuestions(q: string): Promise<ExampleQuestion[]> {
  return fetchAPI(`/api/history/examples?q=${encodeURIComponent(q)}`);
}

// Admin
export async function getDocuments(): Promise<DocumentInfo[]> {
  return fetchAPI("/api/admin/documents");
}

export async function createDocument(data: { filename: string; title: string; content: string }): Promise<DocumentInfo> {
  return fetchAPI("/api/admin/documents", { method: "POST", body: JSON.stringify(data) });
}

export async function updateDocument(id: string, data: { title?: string; content?: string }): Promise<DocumentInfo> {
  return fetchAPI(`/api/admin/documents/${id}`, { method: "PUT", body: JSON.stringify(data) });
}

export async function deleteDocument(id: string): Promise<void> {
  await fetchAPI(`/api/admin/documents/${id}`, { method: "DELETE" });
}

export async function reindex(): Promise<void> {
  await fetchAPI("/api/admin/reindex", { method: "POST" });
}

export async function getStats(): Promise<SearchStats> {
  return fetchAPI("/api/admin/stats");
}

// Org Chart
export async function getOrgChart(): Promise<OrgChart> {
  return fetchAPI("/api/org");
}
