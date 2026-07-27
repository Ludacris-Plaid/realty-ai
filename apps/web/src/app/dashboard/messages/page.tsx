"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Mail, Phone, MessageSquare, Send, Search, Plus, RefreshCw,
  Check, X, FileText, ArrowLeft, Clock, ChevronRight,
  User, Bot, Inbox, Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";

type UnifiedThread = {
  id: string; title: string; platform: string; participants: string[];
  last_message: string; last_message_at: string; message_count: number;
  source: string; sender_name?: string; is_read?: boolean;
};

type ThreadMessage = {
  id: string; role: string; content: string; direction: string;
  platform: string; sender: string; subject: string; created_at: string;
};

const PLATFORM_CFG: Record<string, { icon: any; color: string; label: string }> = {
  email: { icon: Mail, color: "text-blue-400", label: "Email" },
  sms: { icon: Phone, color: "text-amber-400", label: "SMS" },
  chat: { icon: MessageSquare, color: "text-emerald-400", label: "Chat" },
};

function pc(platform: string) {
  return PLATFORM_CFG[platform] || { icon: MessageSquare, color: "text-gray-400", label: platform };
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

const COLORS = [
  "bg-blue-600", "bg-amber-600", "bg-emerald-600", "bg-purple-600",
  "bg-rose-600", "bg-teal-600", "bg-cyan-600", "bg-pink-600",
];

function nameColor(n: string): string {
  let h = 0;
  for (let i = 0; i < n.length; i++) h = n.charCodeAt(i) + ((h << 5) - h);
  return COLORS[Math.abs(h) % COLORS.length];
}

function fmt(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  const n = new Date();
  return d.toDateString() === n.toDateString()
    ? d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : d.toLocaleDateString([], { month: "short", day: "numeric" });
}

function extractName(sender: string, participants: string[]): string {
  if (sender) return sender.split("@")[0].replace(/[._]/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  if (participants.length) return participants[0].split("@")[0];
  return "Unknown";
}

export default function MessagesPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [replyText, setReplyText] = useState("");
  const [replyPlat, setReplyPlat] = useState<"email" | "sms">("email");
  const [showCompose, setShowCompose] = useState(false);
  const [composeTo, setComposeTo] = useState("");
  const [composeSubj, setComposeSubj] = useState("");
  const [composeBody, setComposeBody] = useState("");
  const [sending, setSending] = useState(false);
  const [threads, setThreads] = useState<UnifiedThread[]>([]);
  const [msgs, setMsgs] = useState<ThreadMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem("athena_token") : null;
  const api = (path: string, opts?: RequestInit) =>
    fetch(`/api/v1${path}`, {
      ...opts,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...opts?.headers },
    });

  async function loadThreads() {
    try {
      setLoading(true);
      const res = await api("/messages/unified");
      if (res.ok) setThreads(await res.json());
    } catch {}
    setLoading(false);
  }

  async function loadMsgs(id: string) {
    try {
      const res = await api(`/messages/unified/${id}`);
      if (res.ok) setMsgs(await res.json());
    } catch {}
  }

  useEffect(() => { loadThreads(); const iv = setInterval(loadThreads, 15000); return () => clearInterval(iv); }, []);
  useEffect(() => { if (selectedId) loadMsgs(selectedId); else setMsgs([]); }, [selectedId]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs.length]);

  const filtered = threads.filter((t) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return t.title?.toLowerCase().includes(q) || t.participants?.some((p) => p.toLowerCase().includes(q));
  });

  const sel = filtered.find((t) => t.id === selectedId);

  async function handleReply() {
    if (!replyText.trim() || !selectedId || sending) return;
    setSending(true);
    if (replyPlat === "email") {
      await api("/gmail/send", {
        method: "POST",
        body: JSON.stringify({ to: sel?.participants?.[0] || "", subject: `Re: ${sel?.title || ""}`, body: replyText }),
      });
    } else {
      await api("/messages/webhook", {
        method: "POST",
        body: JSON.stringify({ content: replyText, platform: "sms", sender: "agent" }),
      });
    }
    setReplyText("");
    setSending(false);
    loadMsgs(selectedId);
    loadThreads();
  }

  async function handleSend() {
    if (!composeTo.trim() || !composeSubj.trim() || sending) return;
    setSending(true);
    await api("/gmail/send", {
      method: "POST",
      body: JSON.stringify({ to: composeTo, subject: composeSubj, body: composeBody }),
    });
    setSending(false);
    setShowCompose(false);
    setComposeTo("");
    setComposeSubj("");
    setComposeBody("");
    loadThreads();
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-0 -m-6">
      {/* LEFT PANEL */}
      <div className={cn("w-72 lg:w-80 flex-shrink-0 border-r border-gray-800 bg-gray-950 flex flex-col", selectedId ? "hidden md:flex" : "flex")}>
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-bold text-white">Messages</h1>
            <div className="flex gap-1">
              <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-white" onClick={() => setShowCompose(true)}>
                <Plus className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-white" onClick={loadThreads}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
            <Input value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Search messages..." className="pl-8 h-9 text-sm bg-gray-900 border-gray-700 text-gray-200 placeholder:text-gray-500" />
          </div>
        </div>

        <ScrollArea className="flex-1">
          {loading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center gap-3 animate-pulse">
                  <div className="h-9 w-9 rounded-full bg-gray-800 shrink-0" />
                  <div className="flex-1 space-y-1.5"><div className="h-3 w-24 rounded bg-gray-800" /><div className="h-2 w-40 rounded bg-gray-800/50" /></div>
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center px-4">
              <Inbox className="h-12 w-12 text-gray-600 mb-3" />
              <p className="text-sm text-gray-400">No messages yet</p>
            </div>
          ) : (
            <div className="py-1">
              {filtered.map((t) => {
                const name = extractName(t.sender_name || "", t.participants);
                const PlatIcon = pc(t.platform).icon;
                return (
                  <button key={t.id} onClick={() => { setSelectedId(t.id); setShowCompose(false); }}
                    className={cn("w-full flex items-start gap-3 px-4 py-3 text-left transition-colors border-l-2", selectedId === t.id ? "bg-gray-800 border-l-2 border-amber-500" : "border-l-2 border-transparent hover:bg-gray-800/50")}>
                    <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white", nameColor(name))}>{initials(name)}</div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-gray-200 truncate">{name}</span>
                        <span className="text-[10px] text-gray-500 shrink-0">{fmt(t.last_message_at)}</span>
                      </div>
                      <div className="flex items-center gap-1 mt-0.5">
                        <PlatIcon className={cn("h-3 w-3", pc(t.platform).color)} />
                        <span className="text-xs text-gray-400 truncate">{t.title}</span>
                      </div>
                      <p className="text-[11px] text-gray-500 truncate mt-0.5">{t.last_message}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* RIGHT PANEL */}
      <div className={cn("flex-1 flex flex-col bg-gray-900", showCompose || selectedId ? "flex" : "hidden md:flex")}>
        {showCompose ? (
          <div className="flex flex-col flex-1">
            <div className="border-b border-gray-800 p-4 flex items-center justify-between">
              <h2 className="text-base font-semibold text-white">New Message</h2>
              <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400" onClick={() => setShowCompose(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <div className="max-w-2xl space-y-4">
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">To</label>
                  <Input value={composeTo} onChange={(e) => setComposeTo(e.target.value)} placeholder="recipient@example.com" className="bg-gray-800 border-gray-700 text-gray-200" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">Subject</label>
                  <Input value={composeSubj} onChange={(e) => setComposeSubj(e.target.value)} placeholder="Subject" className="bg-gray-800 border-gray-700 text-gray-200" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">Message</label>
                  <textarea value={composeBody} onChange={(e) => setComposeBody(e.target.value)} rows={12} placeholder="Write your message..."
                    className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder:text-gray-500 focus:border-amber-500 focus:outline-none resize-none font-mono" />
                </div>
                <Button onClick={handleSend} disabled={sending || !composeTo.trim() || !composeSubj.trim()}
                  className="bg-amber-600 hover:bg-amber-700 text-white">
                  <Send className="h-4 w-4 mr-2" /> {sending ? "Sending..." : "Send"}
                </Button>
              </div>
            </div>
          </div>
        ) : !selectedId ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="mx-auto h-12 w-12 text-gray-600" />
              <p className="mt-3 text-sm text-gray-400">Select a conversation</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col flex-1">
            <div className="border-b border-gray-800 p-4 shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 md:hidden" onClick={() => setSelectedId(null)}>
                    <ArrowLeft className="h-4 w-4" />
                  </Button>
                  <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white", nameColor(extractName(sel?.sender_name || "", sel?.participants || [])))}>
                    {initials(extractName(sel?.sender_name || "", sel?.participants || []))}
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-sm font-semibold text-white">{extractName(sel?.sender_name || "", sel?.participants || [])}</h2>
                    <p className="text-xs text-gray-400">{sel?.title} · {msgs.length} messages</p>
                  </div>
                </div>
              </div>
            </div>

            <ScrollArea className="flex-1 px-5 py-4">
              <div className="space-y-4 max-w-3xl mx-auto">
                {msgs.length === 0 ? (
                  <p className="text-xs text-gray-500 text-center py-8">Loading...</p>
                ) : (
                  msgs.map((m) => {
                    const inbound = m.direction === "inbound";
                    const name = extractName(m.sender, []);
                    const PlatIcon = pc(m.platform).icon;
                    return (
                      <div key={m.id} className={cn("flex gap-3 max-w-[85%]", inbound ? "" : "ml-auto flex-row-reverse")}>
                        <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white", inbound ? nameColor(name) : "bg-amber-600")}>
                          {inbound ? initials(name) : "A"}
                        </div>
                        <div className={cn("min-w-0", inbound ? "" : "text-right")}>
                          <div className={cn("flex items-center gap-1.5 mb-1", inbound ? "" : "flex-row-reverse")}>
                            <span className="text-xs font-medium text-gray-400">{inbound ? name : "You"}</span>
                            <PlatIcon className={cn("h-3 w-3", pc(m.platform).color)} />
                          </div>
                          <div className={cn("rounded-2xl px-4 py-2.5 text-sm leading-relaxed", inbound ? "bg-gray-800 text-gray-200 rounded-bl-sm" : "bg-amber-600 text-white rounded-br-sm")}>
                            <p className="whitespace-pre-wrap break-words">{m.content}</p>
                          </div>
                          <p className={cn("text-[10px] text-gray-500 mt-1", inbound ? "" : "text-right")}>{fmt(m.created_at)}</p>
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={bottomRef} />
              </div>
            </ScrollArea>

            <div className="border-t border-gray-800 p-4 shrink-0">
              <div className="flex items-end gap-2 max-w-3xl mx-auto">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1.5">
                    <button onClick={() => setReplyPlat("email")}
                      className={cn("flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium transition-colors", replyPlat === "email" ? "bg-blue-600/20 text-blue-400" : "text-gray-500 hover:text-gray-300")}>
                      <Mail className="h-3 w-3" /> Email
                    </button>
                    <button onClick={() => setReplyPlat("sms")}
                      className={cn("flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium transition-colors", replyPlat === "sms" ? "bg-amber-600/20 text-amber-400" : "text-gray-500 hover:text-gray-300")}>
                      <Phone className="h-3 w-3" /> SMS
                    </button>
                    <span className="text-[10px] text-gray-600 ml-auto">via {replyPlat === "email" ? "Gmail" : "Twilio"}</span>
                  </div>
                  <textarea value={replyText} onChange={(e) => setReplyText(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleReply(); } }}
                    rows={2} placeholder={"Reply via " + replyPlat + "..."}
                    className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-500 focus:border-amber-500 focus:outline-none resize-none" />
                </div>
                <Button onClick={handleReply} disabled={!replyText.trim() || sending} className="bg-amber-600 hover:bg-amber-700 text-white shrink-0 h-[60px]">
                  {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
