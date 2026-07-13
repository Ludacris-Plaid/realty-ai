"use client";

import { useState, useRef, useEffect } from "react";
import { Brain, MessageSquare, X, Sparkles, ChevronDown, Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface AthenaFloatingProps {
  /** Context hint — what page the user is on */
  context?: string;
}

export function AthenaFloating({ context }: AthenaFloatingProps) {
  const [expanded, setExpanded] = useState(false);
  const [input, setInput] = useState("");
  const [showTips, setShowTips] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setExpanded(false);
        setShowTips(false);
      }
    }
    if (expanded) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [expanded]);

  const contextTips: Record<string, { label: string; prompt: string }[]> = {
    leads: [
      { label: "Hot leads", prompt: "Who are my hottest leads right now?" },
      { label: "Pipeline", prompt: "Analyze my lead pipeline" },
      { label: "Follow-up", prompt: "Who needs follow-up today?" },
    ],
    listings: [
      { label: "Active listings", prompt: "Show my active listings" },
      { label: "Describe", prompt: "Generate a listing description" },
      { label: "Market", prompt: "How's the market in Edmonton?" },
    ],
    documents: [
      { label: "Find doc", prompt: "Search my documents for..." },
      { label: "Organize", prompt: "Help me organize my documents" },
    ],
    calendar: [
      { label: "Today", prompt: "What's on my schedule today?" },
      { label: "This week", prompt: "Show my week ahead" },
    ],
    marketing: [
      { label: "Campaigns", prompt: "What marketing campaigns are active?" },
      { label: "Launch", prompt: "Help me launch a campaign" },
    ],
  };

  const tips = context ? contextTips[context] || contextTips.leads : contextTips.leads;

  const handleQuickAction = (prompt: string) => {
    // Navigate to Athena chat with the prompt
    window.location.href = `/dashboard/athena?q=${encodeURIComponent(prompt)}`;
  };

  const handleSubmit = () => {
    if (!input.trim()) return;
    handleQuickAction(input);
  };

  return (
    <div ref={panelRef} className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {/* Expanded panel */}
      {expanded && (
        <div className="mb-2 w-80 animate-in rounded-2xl border border-amber-200/60 bg-white shadow-xl shadow-amber-900/5">
          {/* Header */}
          <div className="flex items-center justify-between rounded-t-2xl bg-gradient-to-r from-amber-500 to-amber-600 px-4 py-3 text-white">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white/20">
                <Brain className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-semibold">Athena</p>
                <p className="text-[10px] text-amber-100">Ask me anything</p>
              </div>
            </div>
            <button
              onClick={() => setExpanded(false)}
              className="flex h-6 w-6 items-center justify-center rounded-full hover:bg-white/20 transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Context-aware tips */}
          <div className="px-4 py-3 border-b border-gray-100">
            <button
              onClick={() => setShowTips(!showTips)}
              className="flex items-center gap-1.5 text-[11px] text-gray-500 hover:text-gray-700"
            >
              <Sparkles className="h-3 w-3 text-amber-500" />
              Quick actions for this page
              <ChevronDown className={cn("h-3 w-3 transition-transform", showTips && "rotate-180")} />
            </button>
            {showTips && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {tips.slice(0, 3).map((tip) => (
                  <button
                    key={tip.label}
                    onClick={() => handleQuickAction(tip.prompt)}
                    className="rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-700 hover:bg-amber-100 transition-colors"
                  >
                    {tip.label}
                  </button>
                ))}
                <button
                  onClick={() => handleQuickAction("")}
                  className="rounded-full bg-gray-50 px-2.5 py-1 text-[11px] font-medium text-gray-500 hover:bg-gray-100 transition-colors"
                >
                  Open full chat →
                </button>
              </div>
            )}
          </div>

          {/* Quick input */}
          <div className="flex items-center gap-2 p-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
              placeholder="Ask Athena..."
              className="flex-1 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400/30"
            />
            <button
              onClick={handleSubmit}
              disabled={!input.trim()}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-40 transition-colors"
            >
              <Send className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="px-4 pb-3 text-center">
            <a
              href="/dashboard/athena"
              className="text-[10px] text-gray-400 hover:text-amber-600 transition-colors"
            >
              Open Athena chat →
            </a>
          </div>
        </div>
      )}

      {/* Floating button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          "group flex h-14 w-14 items-center justify-center rounded-full shadow-lg transition-all duration-300",
          expanded
            ? "bg-gray-800 rotate-45 shadow-gray-900/20"
            : "bg-gradient-to-br from-amber-500 to-amber-600 shadow-amber-500/25 hover:shadow-amber-500/40 hover:scale-105"
        )}
      >
        {expanded ? (
          <X className="h-6 w-6 text-white -rotate-45" />
        ) : (
          <Brain className="h-6 w-6 text-white animate-float" />
        )}
      </button>

      {/* Subtle pulse ring */}
      {!expanded && (
        <div className="absolute bottom-0 right-0 h-14 w-14 animate-ping rounded-full bg-amber-400/20" style={{ animationDuration: "3s" }} />
      )}
    </div>
  );
}
