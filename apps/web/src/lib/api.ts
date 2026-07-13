const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export async function fetchFromApi<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API error: ${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  return res.json();
}

export interface DashboardSummary {
  total_leads: number;
  hot_leads_count: number;
  leads_by_status: Record<string, number>;
  total_listings: number;
  active_listings: number;
  total_value: number;
  recent_activities: ActivityItem[];
  pending_approvals: number;
  today_showings: number;
}

export interface Recommendation {
  type: string;
  title: string;
  description: string;
  priority: string;
}

export interface Lead {
  id: string;
  name: string;
  email: string;
  phone: string;
  budget: number;
  score: number;
  status: string;
  source: string;
  notes: string;
  location_interest: string;
  property_type_interest: string;
  timeline: string;
  pre_approved: boolean;
  ai_score_reason: string;
  last_contacted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Property {
  id: string;
  address: string;
  address_street: string;
  address_city: string;
  address_state: string;
  address_zip: string;
  price: number;
  list_price: number;
  beds: number;
  baths: number;
  sqft: number;
  status: string;
  property_type: string;
  description: string;
  features: string[];
  images: string[];
  mls_number: string;
  year_built: number;
  garage_spaces: number;
  lot_size: number;
  created_at: string;
  image_url: string;
}

export interface Document {
  id: string;
  name: string;
  filename: string;
  file_type: string;
  content_type: string;
  file_size: number;
  file_size_bytes: number;
  category: string;
  title: string;
  description: string;
  uploaded_at: string;
  created_at: string;
}

export interface ActivityItem {
  id: string;
  agent_name: string;
  action: string;
  intent: string;
  model_used: string;
  status: string;
  created_at: string;
}

export interface AgentChatRequest {
  message: string;
}

export interface AgentChatResponse {
  response: string;
  conversation_id?: string;
}

function normalizeLead(raw: any): Lead {
  const statusMap: Record<string, string> = {
    NEW: "new", QUALIFYING: "qualifying", QUALIFIED: "qualified",
    CONTACTED: "contacted", APPOINTMENT_SET: "appointment_set",
    CLOSED_WON: "closed_won", CLOSED_LOST: "closed_lost", DORMANT: "dormant",
  };
  const sourceMap: Record<string, string> = {
    ZILLOW: "zillow", REALTOR_COM: "realtor_com", REDFIN: "redfin",
    WEBSITE: "website", REFERRAL: "referral", SOCIAL_MEDIA: "social_media",
    OPEN_HOUSE: "open_house", CALL_IN: "call_in", EMAIL: "email", OTHER: "other",
  };
  return {
    id: raw.id,
    name: `${raw.first_name || ""} ${raw.last_name || ""}`.trim(),
    email: raw.email || "",
    phone: raw.phone || "",
    budget: raw.budget || 0,
    score: raw.ai_score || 0,
    status: statusMap[raw.status] || (raw.status || "").toLowerCase(),
    source: sourceMap[raw.source] || (raw.source || "").toLowerCase().replace(/_/g, " "),
    notes: raw.notes || "",
    location_interest: raw.location_interest || "",
    property_type_interest: raw.property_type_interest || "",
    timeline: raw.timeline || "",
    pre_approved: raw.pre_approved || false,
    ai_score_reason: raw.ai_score_reason || "",
    last_contacted_at: raw.last_contacted_at || null,
    created_at: raw.created_at,
    updated_at: raw.updated_at,
  };
}

function normalizeProperty(raw: any): Property {
  const images = raw.images || [];
  return {
    id: raw.id,
    address: `${raw.address_street || ""}, ${raw.address_city || ""}, ${raw.address_state || ""}`.trim().replace(/^,\s*|,\s*$/g, "") || "",
    address_street: raw.address_street || "",
    address_city: raw.address_city || "",
    address_state: raw.address_state || "",
    address_zip: raw.address_zip || "",
    price: raw.list_price ? Number(raw.list_price) : 0,
    list_price: raw.list_price ? Number(raw.list_price) : 0,
    beds: raw.beds || 0,
    baths: raw.baths || 0,
    sqft: raw.sqft || 0,
    status: (raw.status || "").toLowerCase(),
    property_type: (raw.property_type || "").toLowerCase(),
    description: raw.description || "",
    features: raw.features || [],
    images,
    mls_number: raw.mls_number || "",
    year_built: raw.year_built || 0,
    garage_spaces: raw.garage_spaces || 0,
    lot_size: raw.lot_size || 0,
    created_at: raw.created_at,
    image_url: (Array.isArray(images) && images.length > 0) ? images[0] : "",
  };
}

export async function getLeads(params?: Record<string, string>): Promise<Lead[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  const res = await fetchFromApi<{ leads: any[] }>("/api/v1/leads" + qs);
  return (res.leads || []).map(normalizeLead);
}

export async function getLead(id: string): Promise<Lead> {
  const res = await fetchFromApi<any>(`/api/v1/leads/${id}`);
  return normalizeLead(res);
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const data = await fetchFromApi<DashboardSummary>("/api/v1/dashboard/summary");
  return {
    ...data,
    today_showings: data.today_showings || 0,
  };
}

export async function getListings(params?: Record<string, string>): Promise<Property[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  const res = await fetchFromApi<{ listings: any[] }>("/api/v1/listings" + qs);
  return (res.listings || []).map(normalizeProperty);
}

export async function getDocuments(): Promise<Document[]> {
  const res = await fetchFromApi<{ documents: any[] }>("/api/v1/documents");
  return (res.documents || []).map((d: any) => ({
    id: d.id,
    name: d.filename || d.title || "",
    filename: d.filename || "",
    file_type: d.content_type || "",
    content_type: d.content_type || "",
    file_size: d.file_size_bytes || 0,
    file_size_bytes: d.file_size_bytes || 0,
    category: d.category || "",
    title: d.title || "",
    description: d.description || "",
    uploaded_at: d.created_at || "",
    created_at: d.created_at || "",
  }));
}

export async function getActivity(): Promise<ActivityItem[]> {
  const res = await fetchFromApi<{ activities: any[] }>("/activity");
  return (res.activities || []).map((a: any) => ({
    id: a.id,
    agent_name: a.agent_name || a.agent_type || "",
    action: a.action || a.description || "",
    intent: a.intent || "",
    model_used: a.model_used || "",
    status: a.status || "success",
    created_at: a.created_at || a.timestamp || "",
  }));
}

export async function sendChatMessage(req: AgentChatRequest): Promise<AgentChatResponse> {
  const data = await fetchFromApi<any>("/api/v1/agent/chat", {
    method: "POST",
    body: JSON.stringify(req),
  });
  return { response: data.reply || data.response || "" };
}
