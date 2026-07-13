"use client";

import { Bot, Cpu, GitBranch, Users, FileText, Building2, Calendar, Megaphone, BarChart, Settings, Shield, Zap } from "lucide-react";

const agents = [
  {
    name: "LeadQualifier",
    icon: Users,
    color: "bg-emerald-50 text-emerald-600",
    desc: "Evaluates inbound leads using behavioral signals, property preference analysis, and financial readiness scoring. Assigns a 0–100 quality score and routes high-value leads to the next pipeline stage.",
    model: "Fast (Llama 3.1 8B)",
  },
  {
    name: "ListingOptimizer",
    icon: Building2,
    color: "bg-amber-50 text-amber-600",
    desc: "Generates MLS descriptions, feature highlights, and virtual-staging suggestions. Tailors language to property type — residential, commercial, or luxury — and local market trends.",
    model: "Premium (Claude 3.5 Sonnet)",
  },
  {
    name: "DocAnalyzer",
    icon: FileText,
    color: "bg-rose-50 text-rose-600",
    desc: "Extracts and structures data from PDF contracts, disclosures, and inspection reports. Answers natural-language questions about document contents via RAG pipeline.",
    model: "Premium (Claude 3.5 Sonnet)",
  },
  {
    name: "SchedulerAgent",
    icon: Calendar,
    color: "bg-amber-50 text-amber-600",
    desc: "Coordinates showings, open houses, and inspection appointments across agent and client calendars. Sends confirmation, reminder, and rescheduling notifications.",
    model: "Fast (Llama 3.1 8B)",
  },
  {
    name: "CampaignEngine",
    icon: Megaphone,
    color: "bg-cyan-50 text-cyan-600",
    desc: "Creates multi-channel marketing campaigns — email sequences, social media posts, and print-ready flyers. Suggests audience segments based on lead scores and property type.",
    model: "Premium (Claude 3.5 Sonnet)",
  },
  {
    name: "AnalyticsReporter",
    icon: BarChart,
    color: "bg-indigo-50 text-indigo-600",
    desc: "Compiles pipeline metrics, agent activity reports, and market trend analyses. Produces natural-language summaries of key movements and anomalies.",
    model: "Fast (Llama 3.1 8B)",
  },
  {
    name: "SettingsOrchestrator",
    icon: Settings,
    color: "bg-gray-50 text-gray-600",
    desc: "Manages user preferences, integration tokens, webhook configurations, and notification rules. Ensures all connected services are reachable before workflows execute.",
    model: "Fast (Llama 3.1 8B)",
  },
];

export default function AgentsDocs() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI Agents</h1>
        <p className="mt-2 text-lg text-gray-500">
          RealtyAI uses a multi-agent architecture where a supervisor router delegates tasks to specialist agents based on intent classification.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <GitBranch className="h-5 w-5 text-brand-500" />
          Supervisor Routing
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            Every request enters through the <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-800">SupervisorAgent</span>, which runs a lightweight intent classification step using a fast LLM (Llama 3.1 8B). The classifier assigns the request to one of seven specialist agents based on its semantic category.
          </p>
          <div className="rounded-lg bg-gray-50 p-4 border border-gray-100">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Routing Flow</h4>
            <div className="text-sm text-gray-600 space-y-1.5 font-mono">
              <p className="flex items-center gap-2"><Zap className="h-3.5 w-3.5 text-amber-500" /> Request → SupervisorAgent (intent classifier)</p>
              <p className="pl-5">├─ &ldquo;Lead &gt; 85&rdquo; → <span className="text-emerald-600">LeadQualifier</span></p>
              <p className="pl-5">├─ &ldquo;Write MLS &rdquo; → <span className="text-amber-600">ListingOptimizer</span></p>
              <p className="pl-5">├─ &ldquot;Find in contract&rdquo; → <span className="text-rose-600">DocAnalyzer</span></p>
              <p className="pl-5">├─ &ldquo;Schedule showing&rdquo; → <span className="text-amber-600">SchedulerAgent</span></p>
              <p className="pl-5">├─ &ldquo;Create campaign&rdquo; → <span className="text-cyan-600">CampaignEngine</span></p>
              <p className="pl-5">├─ &ldquo;Monthly report&rdquo; → <span className="text-indigo-600">AnalyticsReporter</span></p>
              <p className="pl-5">└─ &ldquo;Update settings&rdquo; → <span className="text-gray-600">SettingsOrchestrator</span></p>
            </div>
          </div>
          <p className="text-sm text-gray-600 leading-relaxed">
            If the supervisor&rsquo;s confidence is below 0.7, it responds with clarifying options rather than routing to a wrong agent. Each specialist receives only the context relevant to its domain — the supervisor strips unrelated data before forwarding.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Bot className="h-5 w-5 text-brand-500" />
          Specialist Agents
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {agents.map((a) => (
            <div key={a.name} className="rounded-xl border border-gray-200 bg-white p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${a.color}`}>
                  <a.icon className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">{a.name}</h3>
                  <p className="text-xs text-gray-400">{a.model}</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{a.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Cpu className="h-5 w-5 text-brand-500" />
          Model Routing
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            Not every task needs a frontier model. RealtyAI uses a three-tier model routing system to balance quality, cost, and latency.
          </p>
          <div className="space-y-3">
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
              <h4 className="text-sm font-semibold text-amber-800">Fast Tier &mdash; Llama 3.1 8B</h4>
              <p className="text-xs text-amber-700 mt-1">Intent classification, lead scoring, simple Q&amp;A, scheduling commands. Runs locally via Ollama or as a serverless endpoint. Latency &lt; 500ms.</p>
            </div>
            <div className="rounded-lg border border-brand-200 bg-brand-50 p-4">
              <h4 className="text-sm font-semibold text-brand-800">Premium Tier &mdash; Claude 3.5 Sonnet</h4>
              <p className="text-xs text-brand-700 mt-1">MLS description generation, contract analysis, campaign copywriting, complex reasoning. API-based with automatic retry and fallback to GPT-4o on failure. Latency &lt; 3s.</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <h4 className="text-sm font-semibold text-gray-800">Local Tier &mdash; GGUF Models</h4>
              <p className="text-xs text-gray-600 mt-1">Optional local inference using downloaded GGUF files served by llama.cpp. Used for offline-capable operations like document chunking or batch lead scoring. Latency depends on hardware.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Shield className="h-5 w-5 text-brand-500" />
          Human-in-the-Loop
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Certain actions require explicit agent approval before execution. When one of these actions is requested, the agent generates the proposed output but holds it for review instead of executing automatically.
          </p>
          <ul className="text-sm text-gray-600 space-y-2">
            <li className="flex items-start gap-2">
              <span className="mt-0.5 h-4 w-4 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-[10px] font-bold shrink-0">!</span>
              <span><strong>Contract generation</strong> — AI-drafted contract language must be reviewed before sending to any party.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 h-4 w-4 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-[10px] font-bold shrink-0">!</span>
              <span><strong>MLS publication</strong> — Created listings enter <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">draft</span> status and await manual publish.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 h-4 w-4 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-[10px] font-bold shrink-0">!</span>
              <span><strong>Bulk email campaigns</strong> — Campaigns exceeding 50 recipients are queued for review before dispatch.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 h-4 w-4 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-[10px] font-bold shrink-0">!</span>
              <span><strong>Lead status changes</strong> — Moving a lead to <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">closed_won</span> or <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">closed_lost</span> requires confirmation.</span>
            </li>
          </ul>
          <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 mt-2">
            <h4 className="text-sm font-semibold text-gray-700 mb-1">Approval Workflow</h4>
            <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
              <li>Agent drafts the output and flags it as requiring approval.</li>
              <li>A notification appears in the activity feed with &ldquo;Review&rdquo; and &ldquo;Approve&rdquo; actions.</li>
              <li>If approved, the action executes; if rejected, the agent receives feedback and revises.</li>
              <li>All approvals are logged in the audit trail with a timestamp and reviewer identity.</li>
            </ol>
          </div>
        </div>
      </section>
    </div>
  );
}


