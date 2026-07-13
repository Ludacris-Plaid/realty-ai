import Link from "next/link";
import { Bot, Users, Building2, FileText, Calendar, Megaphone, BarChart, Settings } from "lucide-react";

const sections = [
  { title: "AI Agents", icon: Bot, desc: "How the multi-agent system works — supervisor routing, specialist agents, and model selection.", href: "/docs/agents", color: "bg-blue-50 text-blue-600" },
  { title: "Managing Leads", icon: Users, desc: "Track, score, and manage your lead pipeline. AI-powered qualification and follow-up recommendations.", href: "/docs/leads", color: "bg-emerald-50 text-emerald-600" },
  { title: "Properties & Listings", icon: Building2, desc: "Create and manage property listings. Generate AI-powered MLS descriptions.", href: "/docs/listings", color: "bg-amber-50 text-amber-600" },
  { title: "Documents & Contracts", icon: FileText, desc: "Upload, analyze, and extract insights from real estate documents using AI.", href: "/docs/documents", color: "bg-rose-50 text-rose-600" },
  { title: "Calendar & Scheduling", icon: Calendar, desc: "Manage showings, open houses, and client appointments.", href: "/docs/calendar", color: "bg-amber-50 text-amber-600" },
  { title: "Marketing Tools", icon: Megaphone, desc: "AI-generated campaigns, social media posts, and email templates.", href: "/docs/marketing", color: "bg-cyan-50 text-cyan-600" },
  { title: "Analytics & Reports", icon: BarChart, desc: "Business performance metrics, lead pipeline analysis, and AI agent activity stats.", href: "/docs/analytics", color: "bg-indigo-50 text-indigo-600" },
  { title: "Settings & Integrations", icon: Settings, desc: "Configure your profile, brokerage, AI preferences, and connect external services.", href: "/docs/settings", color: "bg-gray-50 text-gray-600" },
];

export default function DocsHome() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">RealtyAI Documentation</h1>
        <p className="mt-2 text-lg text-gray-500">Everything you need to know about your AI-powered real estate platform.</p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        {sections.map((s) => (
          <Link key={s.href} href={s.href} className="group block">
            <div className="rounded-xl border border-gray-200 bg-white p-6 transition-all hover:shadow-lg hover:border-brand-200">
              <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-lg ${s.color}`}>
                <s.icon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 group-hover:text-brand-600">{s.title}</h3>
              <p className="mt-2 text-sm text-gray-500 leading-relaxed">{s.desc}</p>
            </div>
          </Link>
        ))}
      </div>

      <div className="rounded-xl border border-brand-100 bg-brand-50 p-6">
        <h2 className="text-lg font-semibold text-brand-800">Need help?</h2>
        <p className="mt-1 text-sm text-brand-600">Use the AI Assistant in the bottom-right corner of any page to ask questions about using RealtyAI.</p>
      </div>
    </div>
  );
}
