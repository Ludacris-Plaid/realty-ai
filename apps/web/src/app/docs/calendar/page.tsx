"use client";

import { Calendar, Clock, Bell, CalendarDays, CalendarRange, List, Home, DoorOpen, Users, Handshake, Wrench } from "lucide-react";

const eventTypes = [
  { name: "Showing", icon: DoorOpen, color: "bg-blue-50 text-blue-600 border-blue-100", desc: "Property showing with a client or buyer agent. Includes arrival instructions and lockbox code." },
  { name: "Open House", icon: Home, color: "bg-emerald-50 text-emerald-600 border-emerald-100", desc: "Public open house event. Can be scheduled with or without registration requirement." },
  { name: "Client Meeting", icon: Users, color: "bg-purple-50 text-purple-600 border-purple-100", desc: "Consultation, strategy session, or check-in with a client. Linked to the lead record." },
  { name: "Closing", icon: Handshake, color: "bg-amber-50 text-amber-600 border-amber-100", desc: "Scheduled closing appointment at title company or attorney&rsquo;s office." },
  { name: "Inspection", icon: Wrench, color: "bg-rose-50 text-rose-600 border-rose-100", desc: "Home inspection, termite inspection, or other property evaluation appointment." },
];

export default function CalendarDocs() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Calendar & Scheduling</h1>
        <p className="mt-2 text-lg text-gray-500">
          Manage showings, open houses, meetings, and closings across a multi-view calendar with automated reminders and Google Calendar sync.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <CalendarDays className="h-5 w-5 text-brand-500" />
          Calendar Views
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            The calendar supports three view modes, switchable from the toolbar. All views share the same event data and filters.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1.5">
                <CalendarDays className="h-4 w-4 text-brand-500" />
                <h3 className="text-sm font-medium text-gray-800">Month</h3>
              </div>
              <p className="text-xs text-gray-500">Full-month overview with event dots on each day. Best for seeing your monthly volume at a glance. Click a day to drill into its events.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1.5">
                <CalendarRange className="h-4 w-4 text-brand-500" />
                <h3 className="text-sm font-medium text-gray-800">Week</h3>
              </div>
              <p className="text-xs text-gray-500">Hourly grid spanning Monday&ndash;Sunday. Each event occupies a time slot with color-coding by type. Drag to reschedule within the grid.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1.5">
                <List className="h-4 w-4 text-brand-500" />
                <h3 className="text-sm font-medium text-gray-800">Day</h3>
              </div>
              <p className="text-xs text-gray-500">Detailed agenda view for a single day. Events are listed chronologically with full details — address, contact, notes, and attachments.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Calendar className="h-5 w-5 text-brand-500" />
          Event Types
        </h2>
        <p className="text-sm text-gray-600 leading-relaxed">Each event type has distinct fields and behaviors. Events are linked to a lead, listing, or both.</p>
        <div className="space-y-2">
          {eventTypes.map((e) => (
            <div key={e.name} className="flex items-start gap-3 rounded-xl border border-gray-200 bg-white p-4">
              <div className={`shrink-0 rounded-lg border p-2 ${e.color}`}>
                <e.icon className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-800">{e.name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{e.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <svg className="h-5 w-5 text-brand-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          Google Calendar Integration
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            RealtyAI can sync bidirectionally with Google Calendar. When enabled via Settings &gt; Integrations, the system maintains a two-way sync every 5 minutes.
          </p>
          <div className="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Sync Behavior</h4>
            <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
              <li>Events created in RealtyAI appear on your Google Calendar within 5 minutes</li>
              <li>Google Calendar events with &ldquo;RealtyAI&rdquo; in the description or matching a known contact are imported</li>
              <li>Deleting an event in either platform deletes it from the other within the same sync window</li>
              <li>Conflicts (event modified in both places simultaneously) resolve to the most recent update timestamp</li>
              <li>Events can optionally be synced to a shared team calendar for brokerage-wide visibility</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Bell className="h-5 w-5 text-brand-500" />
          Automated Reminders
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Every event automatically generates reminders for the participants. Reminder timing depends on the event type:
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { event: "Showing", reminders: "24h before (SMS), 2h before (SMS + email), 30min before (SMS)" },
              { event: "Open House", reminders: "48h before (email blast to saved leads), 2h before (SMS to agent)" },
              { event: "Client Meeting", reminders: "24h before (email), 1h before (SMS)" },
              { event: "Closing", reminders: "7d before (email with checklist), 24h before (email + SMS), 1h before (SMS)" },
            ].map((r) => (
              <div key={r.event} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                <h4 className="text-xs font-semibold text-gray-700 mb-0.5">{r.event}</h4>
                <p className="text-xs text-gray-500">{r.reminders}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500">
            Reminder channels include SMS, email, and in-app notification. Each channel has its own opt-out per lead or per event. You can configure default reminder schedules per event type in Settings.
          </p>
        </div>
      </section>
    </div>
  );
}
