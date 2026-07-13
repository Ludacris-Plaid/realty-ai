"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Book, Bot, Users, Building2, FileText, Calendar, Megaphone, Settings, BarChart, ChevronRight } from "lucide-react";

const docsNav = [
  { label: "Getting Started", href: "/docs", icon: Book },
  { label: "AI Agents", href: "/docs/agents", icon: Bot },
  { label: "Managing Leads", href: "/docs/leads", icon: Users },
  { label: "Properties & Listings", href: "/docs/listings", icon: Building2 },
  { label: "Documents & Contracts", href: "/docs/documents", icon: FileText },
  { label: "Calendar & Scheduling", href: "/docs/calendar", icon: Calendar },
  { label: "Marketing Tools", href: "/docs/marketing", icon: Megaphone },
  { label: "Analytics & Reports", href: "/docs/analytics", icon: BarChart },
  { label: "Settings & Integrations", href: "/docs/settings", icon: Settings },
];

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="w-64 shrink-0 border-r border-gray-200 bg-white hidden lg:block">
        <div className="flex h-16 items-center gap-2.5 px-6 border-b border-gray-100">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500">
            <Book className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight">RealtyAI Docs</span>
        </div>
        <nav className="p-4 space-y-1">
          {docsNav.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )}
              >
                <item.icon className="h-4 w-4" />
                <span>{item.label}</span>
                {isActive && <ChevronRight className="h-4 w-4 ml-auto text-brand-500" />}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-8 py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
