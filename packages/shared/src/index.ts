// RealtyAI — shared TypeScript types

export interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  status: string;
  source?: string;
  budget?: number;
  location_interest?: string;
  ai_score?: number;
  ai_score_reason?: string;
  notes?: string;
  created_at: string;
}

export interface Property {
  id: string;
  address_street: string;
  address_city: string;
  address_state: string;
  address_zip: string;
  property_type: string;
  status: string;
  beds?: number;
  baths?: number;
  sqft?: number;
  list_price?: number;
  description?: string;
  features?: string[];
  images?: string[];
}

export interface Client {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  client_type: string;
  status: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title?: string;
  status: string;
  messages: Message[];
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface AgentResponse {
  reply: string;
  email_draft?: Record<string, unknown>;
  lead?: Lead;
  property?: Property;
  actions_taken: string[];
}
