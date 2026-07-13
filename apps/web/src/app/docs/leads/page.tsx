"use client";

import { Users, TrendingUp, Radio, Bell, Columns3, Star, Phone, Mail, MessageSquare } from "lucide-react";

const statuses = [
  { label: "New", color: "bg-blue-100 text-blue-700 border-blue-200", desc: "Lead entered the system from any source. No action taken yet." },
  { label: "Qualifying", color: "bg-indigo-100 text-indigo-700 border-indigo-200", desc: "Agent or AI has initiated contact. Gathering needs, budget, and timeline." },
  { label: "Qualified", color: "bg-emerald-100 text-emerald-700 border-emerald-200", desc: "Lead confirmed as a serious prospect with clear requirements and financing." },
  { label: "Contacted", color: "bg-amber-100 text-amber-700 border-amber-200", desc: "Showing or property recommendations have been shared. Awaiting response." },
  { label: "Appointment Set", color: "bg-purple-100 text-purple-700 border-purple-200", desc: "Showing, open house, or consultation scheduled on the calendar." },
  { label: "Closed Won", color: "bg-emerald-100 text-emerald-700 border-emerald-200", desc: "Deal closed. Lead converted to client." },
  { label: "Closed Lost", color: "bg-red-100 text-red-700 border-red-200", desc: "Lead disqualified or deal fell through. Reason recorded for analysis." },
];

const scoreFactors = [
  { label: "Property type match", icon: Star, detail: "Lead's desired property type matches active inventory. +20 points for exact match, +10 for partial." },
  { label: "Budget coherence", icon: TrendingUp, detail: "Requested price range vs. market reality. +15 for realistic range, -10 for severe mismatch." },
  { label: "Timeline urgency", icon: CalendarIcon, detail: "Moving timeline within 90 days. +15 for immediate, +10 for 1-3 months, +5 for 6+ months." },
  { label: "Engagement level", icon: Bell, detail: "Email opens, link clicks, site visits. +2 per interaction in the last 7 days, capped at +25." },
  { label: "Source quality", icon: Radio, detail: "Referral and repeat client sources score +20. Zillow/Realtor.com +10. Cold inquiries +5." },
  { label: "Pre-approval status", icon: Star, detail: "Verified pre-approval letter uploaded. +25 flat bonus." },
];

export default function LeadsDocs() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Managing Leads</h1>
        <p className="mt-2 text-lg text-gray-500">
          Track prospects through a structured pipeline, let AI score and qualify them, and automate follow-ups so no lead slips through.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Columns3 className="h-5 w-5 text-brand-500" />
          Pipeline Statuses
        </h2>
        <p className="text-sm text-gray-600 leading-relaxed">Each lead moves through a defined set of statuses. Transitions can be manual or triggered by AI-detected events.</p>
        <div className="space-y-2">
          {statuses.map((s) => (
            <div key={s.label} className="flex items-start gap-3 rounded-xl border border-gray-200 bg-white p-4">
              <span className={`shrink-0 rounded-md border px-2.5 py-1 text-xs font-semibold ${s.color}`}>{s.label}</span>
              <p className="text-sm text-gray-600">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Star className="h-5 w-5 text-brand-500" />
          AI Scoring System
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            Every lead receives a dynamic 0&ndash;100 score recalculated whenever new data arrives. Scores determine routing priority, follow-up cadence, and campaign inclusion. Leads above 80 are flagged for immediate contact.
          </p>
          <h3 className="text-sm font-semibold text-gray-800">Scoring Factors</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {scoreFactors.map((f) => (
              <div key={f.label} className="rounded-lg border border-gray-100 bg-gray-50 p-4">
                <div className="flex items-center gap-2 mb-1.5">
                  <f.icon className="h-4 w-4 text-brand-500" />
                  <h4 className="text-sm font-medium text-gray-800">{f.label}</h4>
                </div>
                <p className="text-xs text-gray-500">{f.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Radio className="h-5 w-5 text-brand-500" />
          Lead Sources
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            Each lead records its origin automatically. Sources are tagged on ingestion and visible in both the lead detail view and pipeline analytics.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { name: "Zillow", type: "Portal" },
              { name: "Realtor.com", type: "Portal" },
              { name: "Website Chat", type: "Inbound" },
              { name: "Phone Call", type: "Inbound" },
              { name: "Referral", type: "Network" },
              { name: "Open House", type: "Event" },
              { name: "Social Media", type: "Campaign" },
              { name: "Manual Entry", type: "Internal" },
            ].map((src) => (
              <div key={src.name} className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-center">
                <p className="text-sm font-medium text-gray-800">{src.name}</p>
                <p className="text-xs text-gray-400">{src.type}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Bell className="h-5 w-5 text-brand-500" />
          Auto Follow-Up
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            When a lead reaches a status without agent action within a configurable window, the system triggers an automated follow-up sequence. Each sequence is a chain of touches spaced by delays.
          </p>
          <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Example: New Lead Sequence</h4>
            <div className="text-sm text-gray-600 space-y-1.5">
              <p className="flex items-center gap-2"><Mail className="h-3.5 w-3.5 text-brand-500" /> T+0h &mdash; Send introductory email with market summary</p>
              <p className="flex items-center gap-2"><MessageSquare className="h-3.5 w-3.5 text-brand-500" /> T+24h &mdash; SMS check-in: &ldquo;Did you get a chance to review?&rdquo;</p>
              <p className="flex items-center gap-2"><Phone className="h-3.5 w-3.5 text-brand-500" /> T+72h &mdash; Flag for phone call if no response</p>
              <p className="flex items-center gap-2"><Bell className="h-3.5 w-3.5 text-amber-500" /> T+7d &mdash; Re-engagement email with new listings</p>
            </div>
          </div>
          <p className="text-sm text-gray-500">All automated touches are logged on the lead timeline and visible in the activity feed. Agents can pause or override sequences per lead.</p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Users className="h-5 w-5 text-brand-500" />
          Kanban Board
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <p className="text-sm text-gray-600 leading-relaxed">
            The pipeline is displayed as a drag-and-drop Kanban board with one column per status. Leads appear as cards showing name, source, score badge, days in status, and next action. Dragging a card to a new column immediately updates the lead status and triggers any applicable workflows — scoring recalculation, follow-up sequence start/stop, or notification to assigned agent. Column-level summary bars show total value and count at the top of each column. Filters at the board level allow slicing by source, score range, agent, or date range.
          </p>
        </div>
      </section>
    </div>
  );
}

function CalendarIcon(props: React.ComponentProps<typeof Star>) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}
