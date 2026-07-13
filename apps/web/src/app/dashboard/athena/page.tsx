"use client";

import { useEffect, useState, useRef, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { fetchFromApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Send, Bot, Cpu, Activity, Brain, Book, Zap, User, BarChart, Globe,
  MessageSquare, Sparkles, Heart, Copy, Check, Clock, CornerDownLeft,
  ChevronDown, X, RotateCcw, History,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ───────────────────────────────────────────────────────────────

interface SystemOverview {
  business: { total_leads: number; hot_leads: number; total_listings: number; active_listings: number };
  system: { cpu_percent: number; memory_percent: number; memory_gb: number; memory_total_gb: number };
  ai: { model: string; fallback: string; agents: { id: string; name: string }[] };
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  tool_calls?: string;
  timestamp?: string;
}

// ─── Simple markdown renderer ────────────────────────────────────────────

function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let listItems: React.ReactNode[] = [];
  let inList = false;

  const flushList = (key: string) => {
    if (inList && listItems.length > 0) {
      elements.push(
        <ul key={key} className="my-2 space-y-1 pl-4">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  const processInline = (line: string): React.ReactNode => {
    // Bold: **text**
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
      }
      // Italic: *text*
      const italicParts = part.split(/(\*[^*]+\*)/g);
      return italicParts.map((ip, j) => {
        if (ip.startsWith("*") && ip.endsWith("*") && !ip.startsWith("**")) {
          return <em key={`${i}-${j}`}>{ip.slice(1, -1)}</em>;
        }
        return ip;
      });
    });
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    // Empty line
    if (!trimmed) {
      flushList(`list-end-${idx}`);
      return;
    }

    // Headers
    if (trimmed.startsWith("### ")) {
      flushList(`h3-${idx}`);
      elements.push(<h3 key={idx} className="mt-4 mb-1 text-sm font-bold text-gray-900">{trimmed.slice(4)}</h3>);
      return;
    }
    if (trimmed.startsWith("## ")) {
      flushList(`h2-${idx}`);
      elements.push(<h2 key={idx} className="mt-5 mb-1.5 text-base font-bold text-gray-900">{trimmed.slice(3)}</h2>);
      return;
    }
    if (trimmed.startsWith("# ")) {
      flushList(`h1-${idx}`);
      elements.push(<h1 key={idx} className="mt-5 mb-2 text-lg font-bold text-gray-900">{trimmed.slice(2)}</h1>);
      return;
    }

    // Bullet list
    if (trimmed.startsWith("- ") || trimmed.startsWith("• ")) {
      inList = true;
      const content = trimmed.replace(/^[-•]\s*/, "");
      listItems.push(
        <li key={idx} className="text-sm leading-relaxed text-gray-700">
          <span className="mr-2 text-amber-500">•</span>
          {processInline(content)}
        </li>
      );
      return;
    }

    // Numbered list
    if (/^\d+\.\s/.test(trimmed)) {
      inList = true;
      const content = trimmed.replace(/^\d+\.\s*/, "");
      listItems.push(
        <li key={idx} className="text-sm leading-relaxed text-gray-700">
          <span className="mr-2 text-amber-500">{trimmed.match(/^\d+/)?.[0]}.</span>
          {processInline(content)}
        </li>
      );
      return;
    }

    // Separator
    if (trimmed === "---" || trimmed === "***") {
      flushList(`sep-${idx}`);
      elements.push(<Separator key={idx} className="my-3" />);
      return;
    }

    // Regular paragraph
    flushList(`p-${idx}`);
    elements.push(
      <p key={idx} className="text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">
        {processInline(trimmed)}
      </p>
    );
  });

  flushList("list-final");
  return elements;
}

// ─── Copy button component ───────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* fallback */ }
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className={cn(
        "flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium transition-all",
        copied
          ? "bg-emerald-100 text-emerald-700"
          : "bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600 opacity-0 group-hover:opacity-100"
      )}
    >
      {copied ? (
        <><Check className="h-3 w-3" /> Copied</>
      ) : (
        <><Copy className="h-3 w-3" /> Copy</>
      )}
    </button>
  );
}

// ─── Greeting helper ─────────────────────────────────────────────────────

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

// ─── Main Page ───────────────────────────────────────────────────────────

export default function AthenaPage() {
  return (
    <Suspense fallback={
      <div className="flex h-[calc(100vh-6rem)] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-14 w-14 animate-pulse rounded-2xl bg-amber-200 flex items-center justify-center">
            <Brain className="h-7 w-7 text-amber-600" />
          </div>
          <p className="mt-4 text-sm text-gray-400">Waking Athena...</p>
        </div>
      </div>
    }>
      <AthenaPageContent />
    </Suspense>
  );
}

function AthenaPageContent() {
  const searchParams = useSearchParams();
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [athenaState, setAthenaState] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [chatting, setChatting] = useState(false);
  const [activeView, setActiveView] = useState<"chat" | "overview" | "memory">("chat");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [initialGreetingShown, setInitialGreetingShown] = useState(false);
  const chatEnd = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sentFromQuery = useRef(false);

  // Auto-resize textarea
  const resizeTextarea = useCallback(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
    }
  }, []);

  // Load system data AND conversation history on mount
  useEffect(() => {
    Promise.all([
      fetchFromApi<SystemOverview>("/api/v1/athena/system-overview").catch(() => null),
      fetchFromApi<{ agent: any; tools: any[] }>("/api/v1/athena/state").catch(() => null),
      fetchFromApi<{ profile: string; skills: any[] }>("/api/v1/athena/memory").catch(() => null),
      fetchFromApi<{ conversation_id: string; messages: ChatMessage[] }>("/api/v1/athena/conversations/current").catch(() => null),
    ])
      .then(([ov, state, mem, conv]) => {
        if (ov) setOverview(ov);
        if (state && mem) setAthenaState({ ...state.agent, profile: mem.profile, skills: mem.skills });
        
        // Load conversation history
        if (conv && conv.conversation_id) {
          setConversationId(conv.conversation_id);
        }
        if (conv && conv.messages && conv.messages.length > 0) {
          const chatMsgs = conv.messages.filter((m: any) => m.role === "user" || m.role === "assistant");
          if (chatMsgs.length > 0) {
            setMessages(chatMsgs);
            return; // Don't show greeting if we have history
          }
        }
        // No history — show the welcome greeting
        setMessages([{
          role: "assistant",
          content: `${getGreeting()}. I'm Athena, your digital secretary. I know your business, your leads, your listings — and I'm here to make your life easier.\n\nTry asking me anything: *"How are my leads looking?"*, *"Schedule a showing"*, or just tell me about your day. I'm all ears.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }]);
      })
      .catch(() => {
        // On error, show greeting
        setMessages([{
          role: "assistant",
          content: `${getGreeting()}. I'm Athena, your digital secretary. I know your business, your leads, your listings — and I'm here to make your life easier.\n\nTry asking me anything: *"How are my leads looking?"*, *"Schedule a showing"*, or just tell me about your day. I'm all ears.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }]);
      })
      .finally(() => setLoading(false));
  }, []);

  // Auto-scroll
  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus textarea when switching to chat
  useEffect(() => {
    if (activeView === "chat" && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [activeView]);

  // Handle URL query param ?q=...
  useEffect(() => {
    if (!loading && searchParams?.get("q") && !sentFromQuery.current) {
      const q = searchParams.get("q")!;
      sentFromQuery.current = true;
      setInput(q);
      // Auto-send after a brief moment
      setTimeout(() => {
        sendMessage(q);
      }, 300);
    }
  }, [loading, searchParams]);

  const sendMessage = async (overrideMsg?: string) => {
    const msg = (overrideMsg || input).trim();
    if (!msg || chatting) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }]);
    setChatting(true);
    resizeTextarea();

    try {
      const res = await fetchFromApi<{ response: string; tool_calls?: string; model_used?: string }>("/api/v1/athena/chat", {
        method: "POST",
        body: JSON.stringify({ message: msg }),
      });
      setMessages((m) => [...m, {
        role: "assistant",
        content: res.response,
        tool_calls: res.tool_calls,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    } catch (e: any) {
      setMessages((m) => [...m, {
        role: "assistant",
        content: `I ran into a small issue: ${e.message}. Mind trying again?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    }
    setChatting(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    resizeTextarea();
  };

  // ─── New Conversation / Reset ──────────────────────────────────────

  const newConversation = async () => {
    setChatting(true);
    try {
      const res = await fetchFromApi<{ conversation_id: string; message: string }>("/api/v1/athena/conversations/new", {
        method: "POST",
      });
      setConversationId(res.conversation_id);
      setMessages([{
        role: "assistant",
        content: res.message + `\n\n${getGreeting()}. What can I help you with?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    } catch {
      // If API fails, just clear locally
      setMessages([{
        role: "assistant",
        content: `${getGreeting()}. I'm here for you. What do you need?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    }
    setChatting(false);
  };

  // ─── Loading State ────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-6rem)] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-14 w-14 animate-pulse rounded-2xl bg-amber-200 flex items-center justify-center">
            <Brain className="h-7 w-7 text-amber-600" />
          </div>
          <p className="mt-4 text-sm text-gray-400">Waking Athena...</p>
        </div>
      </div>
    );
  }

  // ─── Render ───────────────────────────────────────────────────────────

  return (
    <div className="flex h-[calc(100vh-6rem)] flex-col">
      {/* ── Header ── */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 shadow-md">
            <Brain className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Athena</h1>
            <p className="text-[11px] text-gray-500">Your digital secretary — always learning, always here</p>
          </div>
        </div>
        <div className="flex gap-1">
          <button onClick={() => setActiveView("chat")}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-lg transition-all",
              activeView === "chat" ? "bg-amber-100 text-amber-700 shadow-sm" : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            )}>
            <MessageSquare className="h-4 w-4 inline mr-1.5" />Chat
          </button>
          <button onClick={() => setActiveView("overview")}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-lg transition-all",
              activeView === "overview" ? "bg-amber-100 text-amber-700 shadow-sm" : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            )}>
            <BarChart className="h-4 w-4 inline mr-1.5" />Overview
          </button>
          <button onClick={() => setActiveView("memory")}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-lg transition-all",
              activeView === "memory" ? "bg-amber-100 text-amber-700 shadow-sm" : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            )}>
            <Book className="h-4 w-4 inline mr-1.5" />Memory
          </button>
          <div className="w-px bg-gray-200 mx-1" />
          <button onClick={newConversation} disabled={chatting}
            className="px-3 py-2 text-sm font-medium rounded-lg text-gray-500 hover:text-amber-700 hover:bg-amber-50 transition-all"
            title="Start a new conversation">
            <RotateCcw className="h-4 w-4 inline mr-1" />New
          </button>
        </div>
      </div>

      {/* ── CHAT VIEW ── */}
      {activeView === "chat" && (
        <div className="flex flex-1 flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
            {messages.map((msg, i) => (
              <div key={i} className={cn("flex gap-3 msg-enter", msg.role === "user" && "justify-end")}>
                {msg.role === "assistant" && (
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-100 to-amber-200 shadow-sm mt-1">
                    <Brain className="h-5 w-5 text-amber-600" />
                  </div>
                )}

                <div className={cn(
                  "max-w-[80%] rounded-2xl px-5 py-3.5 relative",
                  msg.role === "user"
                    ? "bg-amber-600 text-white rounded-br-md shadow-sm"
                    : "bg-gray-50 text-gray-800 rounded-bl-md border border-gray-100 group"
                )}>
                  {/* Message content with formatting */}
                  {msg.role === "assistant" ? (
                    <div className="space-y-1 text-sm leading-relaxed">
                      {renderMarkdown(msg.content)}
                    </div>
                  ) : (
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  )}

                  {/* Copy button (assistant messages only) */}
                  {msg.role === "assistant" && (
                    <div className="flex items-center justify-end mt-2 -mb-1">
                      <CopyButton text={msg.content} />
                    </div>
                  )}

                  {/* Footer: tool calls + timestamp */}
                  <div className={cn(
                    "flex items-center gap-2 mt-1.5",
                    msg.role === "user" ? "justify-end" : "justify-start"
                  )}>
                    {msg.tool_calls && msg.tool_calls !== "[]" && msg.tool_calls !== "" && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-200/80 text-gray-500">
                        📎 {msg.tool_calls.slice(0, 30)}
                      </span>
                    )}
                    {msg.timestamp && (
                      <span className={cn("text-[10px] flex items-center gap-1", msg.role === "user" ? "text-amber-200" : "text-gray-400")}>
                        <Clock className="h-3 w-3" />
                        {msg.timestamp}
                      </span>
                    )}
                  </div>
                </div>

                {msg.role === "user" && (
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gray-800 shadow-sm mt-1">
                    <User className="h-5 w-5 text-white" />
                  </div>
                )}
              </div>
            ))}

            {/* Typing indicator */}
            {chatting && (
              <div className="flex gap-3 msg-enter">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-100 to-amber-200 shadow-sm">
                  <Brain className="h-5 w-5 text-amber-600" />
                </div>
                <div className="rounded-2xl rounded-bl-md bg-gray-50 border border-gray-100 px-5 py-3.5 shadow-sm">
                  <div className="flex gap-1.5">
                    <div className="h-2.5 w-2.5 rounded-full bg-amber-400 animate-bounce" />
                    <div className="h-2.5 w-2.5 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: "0.15s" }} />
                    <div className="h-2.5 w-2.5 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: "0.3s" }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEnd} />
          </div>

          {/* ── Input Area ── */}
          <div className="border-t border-gray-200 bg-white px-6 py-4">
            <div className="flex items-end gap-2">
              <div className="relative flex-1">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Tell me what you need..."
                  disabled={chatting}
                  rows={1}
                  className="w-full resize-none rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 pr-16 text-sm outline-none transition-all placeholder:text-gray-400 focus:border-amber-400 focus:bg-white focus:ring-2 focus:ring-amber-400/20 disabled:opacity-50"
                  style={{ minHeight: "48px", maxHeight: "160px" }}
                />
                <div className="absolute bottom-2.5 right-3 flex items-center gap-1 pointer-events-none">
                  <kbd className="hidden sm:inline-flex rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] text-gray-400 font-medium">
                    ↵
                  </kbd>
                </div>
              </div>
              <Button
                onClick={() => sendMessage()}
                disabled={chatting || !input.trim()}
                className="h-12 w-12 shrink-0 rounded-xl bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-40"
              >
                <Send className="h-5 w-5" />
              </Button>
            </div>
            <div className="mt-2 flex items-center justify-center gap-4 text-[11px] text-gray-400">
              <span>Enter to send</span>
              <span className="text-gray-300">·</span>
              <span>Shift+Enter for new line</span>
              <span className="text-gray-300">·</span>
              <span>Ask me about leads, listings, your day</span>
            </div>
          </div>
        </div>
      )}

      {/* ── OVERVIEW VIEW ── */}
      {activeView === "overview" && (
        <div className="overflow-y-auto space-y-6">
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
                <div><div className="flex justify-between text-sm"><span>CPU</span><span>{overview?.system.cpu_percent}%</span></div><div className="h-2 rounded-full bg-gray-100"><div className="h-2 rounded-full bg-amber-500" style={{width: `${overview?.system.cpu_percent || 0}%`}} /></div></div>
                <div><div className="flex justify-between text-sm"><span>RAM</span><span>{overview?.system.memory_percent}% ({overview?.system.memory_gb}/{overview?.system.memory_total_gb} GB)</span></div><div className="h-2 rounded-full bg-gray-100"><div className="h-2 rounded-full bg-amber-500" style={{width: `${overview?.system.memory_percent || 0}%`}} /></div></div>
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
              <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Brain className="h-4 w-4" /> Athena Status</CardTitle></CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-lg bg-amber-50 p-3 text-center">
                    <p className="text-2xl font-bold text-amber-600">{athenaState?.conversations || 0}</p>
                    <p className="text-xs text-gray-500">Conversations</p>
                  </div>
                  <div className="rounded-lg bg-amber-50 p-3 text-center">
                    <p className="text-2xl font-bold text-amber-600">{athenaState?.tools_available || 0}</p>
                    <p className="text-xs text-gray-500">System Tools</p>
                  </div>
                  <div className="rounded-lg bg-amber-50 p-3 text-center">
                    <p className="text-2xl font-bold text-amber-600">{athenaState?.skills_count || 0}</p>
                    <p className="text-xs text-gray-500">Skills Created</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* ── MEMORY VIEW ── */}
      {activeView === "memory" && (
        <div className="overflow-y-auto grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><User className="h-4 w-4" /> What I Know About You</CardTitle></CardHeader>
            <CardContent>
              {athenaState?.profile && athenaState.profile !== "I'm still getting to know you." ? (
                <div>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">{athenaState.profile}</p>
                  <Button variant="outline" size="sm" className="mt-3 text-xs border-amber-200 text-amber-700" onClick={() => setActiveView("chat")}>
                    <Heart className="h-3 w-3 mr-1" /> Tell me more about you
                  </Button>
                </div>
              ) : (
                <div className="flex flex-col items-center py-8 text-gray-400">
                  <Book className="h-8 w-8 mb-2" />
                  <p className="text-sm">Still getting to know you</p>
                  <p className="text-xs mt-1 text-center max-w-xs">The more we talk, the better I'll know your style, preferences, and business</p>
                  <Button variant="outline" size="sm" className="mt-4 border-amber-200 text-amber-700" onClick={() => setActiveView("chat")}>
                    <MessageSquare className="h-3 w-3 mr-1" /> Start chatting
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2 text-sm"><Sparkles className="h-4 w-4" /> Skills</CardTitle></CardHeader>
            <CardContent>
              {athenaState?.skills && athenaState.skills.length > 0 ? (
                <div className="space-y-3">
                  {athenaState.skills.map((s: any) => (
                    <div key={s.name} className="rounded-lg border p-3 hover:border-amber-200 transition-colors">
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
                  <p className="text-xs mt-1 text-center max-w-xs">I create skills as we work together — routines, workflows, your way of doing things</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
