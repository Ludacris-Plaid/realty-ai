"use client";

import { Settings, User, Building2, Bot, Bell, Link, Key, Webhook, Sliders, Mail, Phone, Calendar } from "lucide-react";

export default function SettingsDocs() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings & Integrations</h1>
        <p className="mt-2 text-lg text-gray-500">
          Configure your profile, brokerage, AI preferences, notifications, and external service connections.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <User className="h-5 w-5 text-brand-500" />
          Profile Management
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Your profile stores personal information, license details, and contact preferences. Fields include full name, email, phone, license number, state of licensure, headshot photo, and a short bio that appears on listing pages and email signatures.
          </p>
          <p className="text-sm text-gray-600 leading-relaxed">
            Profile visibility controls let you decide which fields are public-facing and which are internal-only. Timezone and working hours affect scheduling availability windows and reminder timing.
          </p>
          <div className="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-1">Profile Fields</h4>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
              <span>Full name & title</span>
              <span>Email & phone numbers</span>
              <span>License number & state</span>
              <span>Brokerage affiliation</span>
              <span>Headshot & bio</span>
              <span>Timezone & working hours</span>
              <span>Office address</span>
              <span>Personal website URL</span>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Building2 className="h-5 w-5 text-brand-500" />
          Brokerage Configuration
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Brokerage-level settings control branding, team structure, and compliance rules. Admin users can manage these settings for the entire brokerage; agents only see their own profile and preferences.
          </p>
          <ul className="text-sm text-gray-600 space-y-1.5 list-disc list-inside">
            <li><strong>Branding</strong> — Brokerage name, logo, primary colors, and MLS disclaimers applied to all listings and campaigns</li>
            <li><strong>Team management</strong> — Add/remove agents, assign roles (admin, agent, assistant), set commission splits</li>
            <li><strong>Compliance</strong> — Required disclosures per state, mandatory approval workflows, retention policies</li>
            <li><strong>MLS configuration</strong> — Board ID, feed credentials, syndication targets, and update frequency</li>
          </ul>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Bot className="h-5 w-5 text-brand-500" />
          AI Preferences
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Fine-tune how the AI agents behave across four dimensions. These settings apply globally but can be overridden per lead or per listing.
          </p>
          <div className="space-y-2">
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1">
                <Sliders className="h-4 w-4 text-brand-500" />
                <h4 className="text-sm font-semibold text-gray-700">Auto Follow-Ups</h4>
              </div>
              <p className="text-xs text-gray-500">Enable or disable automatic follow-up sequences. Set the delay between touches, maximum touches per sequence, and whether SMS is allowed. Default: enabled, 24h delay, 4-touch max.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1">
                <Bell className="h-4 w-4 text-brand-500" />
                <h4 className="text-sm font-semibold text-gray-700">Daily Briefing</h4>
              </div>
              <p className="text-xs text-gray-500">Toggle the morning briefing email. Choose briefing content: today&rsquo;s scheduled events, new leads, recent listing views, task reminders. Delivery time is configurable per day.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1">
                <Mail className="h-4 w-4 text-brand-500" />
                <h4 className="text-sm font-semibold text-gray-700">Communication Tone</h4>
              </div>
              <p className="text-xs text-gray-500">Set the default voice for AI-generated client-facing copy: professional, warm, luxury, or direct. Tone affects MLS descriptions, emails, and SMS. Can be overridden per document.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1">
                <Bot className="h-4 w-4 text-brand-500" />
                <h4 className="text-sm font-semibold text-gray-700">Model Selection</h4>
              </div>
              <p className="text-xs text-gray-500">Choose which models power each agent tier. Fast tier defaults to Llama 3.1 8B (local or API). Premium tier defaults to Claude 3.5 Sonnet. Fallback model if primary is unavailable.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Bell className="h-5 w-5 text-brand-500" />
          Notification Settings
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <p className="text-sm text-gray-600 leading-relaxed">
            Configure which events trigger notifications and which channels they use — in-app, email, or SMS. Each notification type has independent toggles and delivery preferences.
          </p>
          <div className="mt-3 grid gap-2 text-sm text-gray-600">
            {[
              { event: "New lead assigned", channels: "In-app + email" },
              { event: "Lead status changes", channels: "In-app" },
              { event: "Showing requested", channels: "In-app + SMS" },
              { event: "Document uploaded to transaction", channels: "In-app + email" },
              { event: "Campaign approval needed", channels: "In-app + email" },
              { event: "AI agent error", channels: "In-app (admin only)" },
              { event: "Daily briefing", channels: "Email" },
              { event: "Monthly report ready", channels: "In-app + email" },
            ].map((n) => (
              <div key={n.event} className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-4 py-2">
                <span className="font-medium">{n.event}</span>
                <span className="text-xs text-gray-400">{n.channels}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Link className="h-5 w-5 text-brand-500" />
          Integration Setup
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            RealtyAI connects with external services via OAuth and API key integrations. Each integration has its own configuration panel showing connection status, last sync time, and any error logs.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-brand-100 bg-brand-50 p-4">
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="h-4 w-4 text-brand-600" />
                <h4 className="text-sm font-semibold text-brand-700">Google Calendar</h4>
              </div>
              <p className="text-xs text-brand-600">OAuth 2.0 connection. Bi-directional sync every 5 minutes. Select which calendars to sync. Requires calendar.readonly and calendar.events scope.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1">
                <Mail className="h-4 w-4 text-gray-600" />
                <h4 className="text-sm font-semibold text-gray-700">Gmail</h4>
              </div>
              <p className="text-xs text-gray-500">OAuth 2.0 for sending AI-generated emails on your behalf. Used for follow-up sequences and campaign dispatch. Optional, falls back to SMTP if not connected.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1">
                <Phone className="h-4 w-4 text-gray-600" />
                <h4 className="text-sm font-semibold text-gray-700">Twilio (SMS)</h4>
              </div>
              <p className="text-xs text-gray-500">API key + phone number configuration. Powers SMS reminders, showing confirmations, and follow-up sequences. Supports US and Canadian numbers.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1">
                <Building2 className="h-4 w-4 text-gray-600" />
                <h4 className="text-sm font-semibold text-gray-700">MLS Feed</h4>
              </div>
              <p className="text-xs text-gray-500">RETS/API feed credentials from your local MLS board. Configurable sync schedule (default: every 6 hours). Supports IDX and VOW data formats.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Key className="h-5 w-5 text-brand-500" />
          API Keys & Webhooks
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Developers and tech-savvy brokerages can access the RealtyAI REST API. API keys are generated per user with scoped permissions — read-only, leads, listings, documents, or full access.
          </p>
          <div className="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Webhook Events</h4>
            <div className="grid gap-1.5 text-xs text-gray-600">
              {[
                "lead.created — A new lead enters the system",
                "lead.status_changed — Lead moved to a different pipeline stage",
                "lead.scored — Lead score recalculated",
                "listing.created — New property listing created",
                "listing.status_changed — Listing status updated",
                "listing.published — Listing published to MLS",
                "document.processed — Document extraction completed",
                "campaign.sent — Marketing campaign dispatched",
                "agent.error — AI agent encountered a failure",
              ].map((ev) => (
                <div key={ev} className="rounded border border-gray-200 bg-white px-3 py-1.5 font-mono text-xs">
                  {ev}
                </div>
              ))}
            </div>
          </div>
          <p className="text-sm text-gray-500">
            Webhooks are delivered via POST to your configured endpoint with a JSON payload and HMAC signature header for verification. Retry up to 3 times with exponential backoff on failure.
          </p>
        </div>
      </section>
    </div>
  );
}
