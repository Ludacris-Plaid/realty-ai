"use client";

import { useEffect, useState, useRef } from "react";
import { fetchFromApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Send, Bot, Cpu, Activity, Database, Brain, Book, Zap, User, BarChart, Globe, MessageSquare, Sparkles } from "lucide-react";

interface SystemOverview {
  business: { total_leads: number; hot_leads: number; total_listings: number; active_listings: number };
  system: { cpu_percent: number; memory_percent: number; memory_gb: number; memory_total_gb: number };
  ai: { model: string; fallback: string; agents: { id: string; name: string }[] };
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  tool_calls?: string;
}

export default function HermesPage() {
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [hermesState, setHermesState] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hey, I'm Hermes. I'm your persistent AI assistant for RealtyAI. I can control the entire system — ask me anything about your leads, listings, pipeline, or tell me what you'd like me to do." }
  ]);
  const [input, setInput] = useState("");
  const [chatting, setChatting] = useState(false);
  const [activeView, setActiveView] = useState<"overview" | "chat" | "memory">("overview");
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([
      fetchFromApi<SystemOverview>("/api/v1/hermes/system-overview"),
      fetchFromApi<{ agent: any; tools: any[] }>("/api/v1/hermes/state"),
      fetchFromApi<{ profile: string; skills: any[] }>("/api/v1/hermes/memory"),
    ])
      .then(([ov, state, mem]) => {
        setOverview(ov);
        setHermesState({ ...state.agent, profile: mem.profile, skills: mem.skills });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || chatting) return;
    const msg = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setChatting(true);

    try {
      const res = await fetchFromApi<{ response: string; tool_calls?: string; model_used?: string }>("/api/v1/hermes/chat", {
        method: "POST",
        body: JSON.stringify({ message: msg }),
      });
      setMessages((m) => [...m, { role: "assistant", content: res.response, tool_calls: res.tool_calls }]);
    } catch (e: any) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${e.message}` }]);
    }
    setChatting(false);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Hermes Agent</h1>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1,2,3,4].map(i => <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-100" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-600">
            <Bot className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Hermes Agent</h1>
            <p className="text-sm text-gray-500">Persistent AI — controls the entire system, learns from you, grows over time</p>
          </div>
        </div>
      </div>

      <div className="flex gap-2 border-b border-gray-200 pb-px">
        {(["overview", "chat", "memory"] as const).map((tab) => (
          <button key={tab} onClick={() => setActiveView(tab)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeView === tab ? "border-violet-600 text-violet-600" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}>
            {tab === "overview" ? "System Overview" : tab === "chat" ? "Chat" : "Memory & Skills"}
          </button>
        ))}
      </div>

      {activeView === "overview" && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card><CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-gray-500">Total Leads</p>
                <Activity className="h-4 w-4 text-blue-500" />
              </div>
              <p className="mt-1 text-2xl font-bold">{overview?.business.total_leads || 0}</p>
            </CardContent></Card>
            <Card><CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-gray-500">Hot Leads</p>
                <Zap className="h-4 w-4 text-red-500" />
              </div>
              <p className="mt-1 text-2xl font-bold">{overview?.business.hot_leads || 0}</p>
            </CardContent></Card>
            <Card><CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-gray-500">Total Listings</p>
                <BarChart className="h-4 w-4 text-emerald-500" />
              </div>
              <p className="mt-1 text-2xl font-bold">{overview?.business.total_listings || 0}</p>
            </CardContent></Card>
            <Card><CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-gray-500">Active Listings</p>
                <Globe className="h-4 w-4 text-amber-500" />
              </div>
              <p className="mt-1 text-2xl font-bold">{overview?.business.active_listings || 0}</p>
            </CardContent></Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Cpu className="h-4 w-4" /> System Health</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div><div className="flex justify-between text-sm"><span>CPU</span><span>{overview?.system.cpu_percent}%</span></div><div className="h-2 rounded-full bg-gray-100"><div className="h-2 rounded-full bg-violet-500" style={{width: `${overview?.system.cpu_percent || 0}%`}} /></div></div>
                <div><div className="flex justify-between text-sm"><span>RAM</span><span>{overview?.system.memory_percent}% ({overview?.system.memory_gb}/{overview?.system.memory_total_gb} GB)</span></div><div className="h-2 rounded-full bg-gray-100"><div className="h-2 rounded-full bg-violet-500" style={{width: `${overview?.system.memory_percent || 0}%`}} /></div></div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Brain className="h-4 w-4" /> AI Configuration</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Primary Model</span><span className="font-medium">{overview?.ai.model || "N/A"}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Fallback</span><span className="font-medium">{overview?.ai.fallback || "N/A"}</span></div>
                <Separator />
                <p className="text-xs text-gray-400">Specialist Agents ({overview?.ai.agents.length || 0}):</p>
                <div className="flex flex-wrap gap-1">
                  {overview?.ai.agents.map((a) => <Badge key={a.id} variant="secondary" className="text-[10px]">{a.name}</Badge>)}
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Bot className="h-4 w-4" /> Hermes Agent Status</CardTitle></CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-lg bg-violet-50 p-3 text-center">
                    <p className="text-2xl font-bold text-violet-600">{hermesState?.conversations || 0}</p>
                    <p className="text-xs text-gray-500">Conversations</p>
                  </div>
                  <div className="rounded-lg bg-violet-50 p-3 text-center">
                    <p className="text-2xl font-bold text-violet-600">{hermesState?.tools_available || 0}</p>
                    <p className="text-xs text-gray-500">System Tools</p>
                  </div>
                  <div className="rounded-lg bg-violet-50 p-3 text-center">
                    <p className="text-2xl font-bold text-violet-600">{hermesState?.skills_count || 0}</p>
                    <p className="text-xs text-gray-500">Skills Created</p>
                  </div>
                </div>
                {hermesState?.profile && (
                  <div className="mt-4 rounded-lg bg-gray-50 p-3">
                    <p className="text-xs font-medium text-gray-500 mb-1">What Hermes Knows</p>
                    <p className="text-xs text-gray-600 whitespace-pre-wrap">{hermesState.profile}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {activeView === "chat" && (
        <Card className="flex flex-col h-[600px]">
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                {msg.role === "assistant" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-violet-100">
                    <Bot className="h-4 w-4 text-violet-600" />
                  </div>
                )}
                <div className={`max-w-[80%] rounded-lg px-4 py-2.5 ${
                  msg.role === "user" ? "bg-violet-600 text-white" : "bg-gray-100 text-gray-800"
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  {msg.tool_calls && msg.tool_calls !== "[]" && msg.tool_calls !== "" && (
                    <p className="mt-1 text-[10px] opacity-60">Tools used: {msg.tool_calls}</p>
                  )}
                </div>
                {msg.role === "user" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-800">
                    <User className="h-4 w-4 text-white" />
                  </div>
                )}
              </div>
            ))}
            {chatting && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-100">
                  <Bot className="h-4 w-4 text-violet-600" />
                </div>
                <div className="rounded-lg bg-gray-100 px-4 py-2.5">
                  <div className="flex gap-1">
                    <div className="h-2 w-2 rounded-full bg-violet-400 animate-bounce" />
                    <div className="h-2 w-2 rounded-full bg-violet-400 animate-bounce delay-100" />
                    <div className="h-2 w-2 rounded-full bg-violet-400 animate-bounce delay-200" />
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEnd} />
          </CardContent>
          <div className="border-t p-4">
            <form onSubmit={(e) => { e.preventDefault(); sendMessage(); }} className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Hermes to do anything — manage leads, analyze pipeline, run crews..."
                disabled={chatting}
                className="flex-1"
              />
              <Button type="submit" disabled={chatting || !input.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </form>
            <p className="mt-1 text-[10px] text-gray-400">Hermes can control the full system via natural language. Try: "Show my hot leads" or "Analyze my pipeline"</p>
          </div>
        </Card>
      )}

      {activeView === "memory" && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><User className="h-4 w-4" /> User Profile</CardTitle></CardHeader>
            <CardContent>
              {hermesState?.profile && hermesState.profile !== "I'm still getting to know you." ? (
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{hermesState.profile}</p>
              ) : (
                <div className="flex flex-col items-center py-8 text-gray-400">
                  <Book className="h-8 w-8 mb-2" />
                  <p className="text-sm">Still getting to know you</p>
                  <p className="text-xs mt-1">Chat with Hermes for it to build your profile</p>
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Sparkles className="h-4 w-4" /> Skills</CardTitle></CardHeader>
            <CardContent>
              {hermesState?.skills && hermesState.skills.length > 0 ? (
                <div className="space-y-3">
                  {hermesState.skills.map((s: any) => (
                    <div key={s.name} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-semibold">{s.name}</p>
                        <Badge variant="secondary" className="text-[10px]">{s.uses} uses</Badge>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">{s.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center py-8 text-gray-400">
                  <Sparkles className="h-8 w-8 mb-2" />
                  <p className="text-sm">No skills yet</p>
                  <p className="text-xs mt-1">Hermes creates skills automatically as you work together</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
