export interface Source {
  document: string;
  section: string;
  content: string;
  score: number;
}

export interface Contact {
  name: string;
  position: string;
  role: string;
  email: string;
  phone: string;
  department: string;
}

export interface PromotionStat {
  year: number;
  position_from: string;
  position_to: string;
  eligible: number;
  promoted: number;
  rate: number;
  avg_score: number;
  min_score: number;
  my_score?: number | null;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[] | null;
  contacts?: Contact[] | null;
  promotion_stats?: PromotionStat[] | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: ChatMessage[];
}

export interface GlossaryItem {
  id: number;
  term: string;
  definition: string;
  category?: string;
  aliases?: string;
  created_at?: string;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  title: string;
  content: string;
  created_at?: string;
}

export interface SearchStats {
  total_queries: number;
  avg_response_time_ms: number;
  top_queries: { query: string; count: number }[];
  daily_stats: { date: string; count: number }[];
}

export interface RecentSearch {
  id: number;
  query: string;
  created_at: string;
}

export interface ExampleQuestion {
  id: number;
  question: string;
  category?: string;
  keywords?: string;
}

export interface Department {
  id: number;
  name: string;
  description?: string;
  parent_id?: number | null;
  sort_order?: number;
}

export interface Employee {
  id: number;
  name: string;
  department_id: number;
  position?: string;
  role?: string;
  email?: string;
  phone?: string;
  is_department_head?: boolean;
}

export interface OrgChart {
  departments: Department[];
  employees: Employee[];
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
