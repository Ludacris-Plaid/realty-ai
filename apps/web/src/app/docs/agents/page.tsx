"use client";

import { Bot, Cpu, Zap, Brain } from "lucide-react";

export default function AgentsDocs() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Athena AI</h1>
        <p className="mt-2 text-lg text-gray-500">
          Athena is your single AI secretary for the entire RealtyAI platform. 23 built-in tools, persistent memory, and natural language control.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Bot className="h-5 w-5 text-brand-500" />
          How It Works
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            Every request goes directly to <strong>Athena</strong>, a LangChain tool-calling agent powered by DeepSeek v4 Flash. She has 23 tools covering every aspect of real estate: leads, listings, documents, marketing, scheduling, market research, and web browsing. No routing, no supervisor — just one agent who can do it all.
          </p>
          <p className="text-sm text-gray-600 leading-relaxed">
            Athena remembers everything from persistent memory (PostgreSQL + Mem0). She learns your preferences, client details, and deal nuances across conversations. Start where you left off.
          </p>
        </div>
      </section>

      <section className="space-y-4">
          <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Zap className="h-5 w-5 text-brand-500" />
          Tool Categories (23 tools)
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            { name: "Leads", cat: "6 tools", desc: "List, score, update, analyze pipeline, recommend follow-ups" },
            { name: "Listings", cat: "6 tools", desc: "List, price analysis, scrape Zillow, import, generate descriptions" },
            { name: "Market", cat: "3 tools", desc: "Market snapshot, neighborhood comparison, trend reports" },
            { name: "Documents", cat: "2 tools", desc: "Contract summary, deadline extraction" },
            { name: "Marketing", cat: "1 tool", desc: "Launch and manage campaigns" },
            { name: "Scheduling", cat: "1 tool", desc: "Schedule showings" },
            { name: "Web", cat: "2 tools", desc: "Browse pages, search web" },
            { name: "Memory", cat: "3 tools", desc: "Save facts, recall, notes" },
            { name: "System", cat: "3 tools", desc: "Dashboard summary, stats, overview" },
          ].map((cat) => (
            <div key={cat.name} className="rounded-xl border border-gray-200 bg-white p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-100 text-brand-600">
                  <Zap className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">{cat.name}</h3>
                  <p className="text-xs text-gray-400">{cat.cat}</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{cat.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Cpu className="h-5 w-5 text-brand-500" />
          Memory & Learning
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            Athena uses a dual-memory system. <strong>PostgreSQL</strong> stores structured facts, conversation history, and notes with full-text search. <strong>Mem0</strong> provides semantic vector search via Qdrant — so Athena finds relevant memories by meaning, not just keywords.
          </p>
          <p className="text-sm text-gray-600 leading-relaxed">
            Every chat interaction is automatically embedded and stored. You can browse, search, and delete memories from the Memory page.
          </p>
        </div>
      </section>
    </div>
  );
}


