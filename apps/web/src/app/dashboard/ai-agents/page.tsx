"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, Users, Building2, FileText, BarChart, Megaphone, Calendar, Search, Globe, Database, Cpu, Sparkles, UserCheck, Wallet, TrendingUp } from "lucide-react";

interface ToolDef {
  name: string;
  description: string;
  parameters: Record<string, any>;
}

const toolGroups: Record<string, { icon: React.ElementType; color: string; tools: string[] }> = {
  "Leads": { icon: Users, color: "bg-amber-500", tools: ["list_leads", "get_lead_detail", "update_lead_status", "score_lead", "analyze_pipeline", "recommend_follow_up"] },
  "Listings": { icon: Building2, color: "bg-emerald-500", tools: ["list_listings", "generate_listing_description", "property_price_analysis", "scrape_properties_advanced", "scrape_and_import_properties", "check_scraper_sources"] },
  "Market": { icon: TrendingUp, color: "bg-cyan-500", tools: ["market_snapshot", "compare_neighborhoods", "market_trend_report"] },
  "Documents": { icon: FileText, color: "bg-rose-500", tools: ["summarize_contract", "extract_deadlines"] },
  "Marketing": { icon: Megaphone, color: "bg-purple-500", tools: ["launch_campaign"] },
  "Scheduling": { icon: Calendar, color: "bg-blue-500", tools: ["schedule_showing"] },
  "Web": { icon: Globe, color: "bg-indigo-500", tools: ["browse_web_page", "search_web"] },
  "Memory": { icon: Database, color: "bg-teal-500", tools: ["remember_fact", "recall_memory", "save_note"] },
  "System": { icon: Cpu, color: "bg-gray-500", tools: ["get_dashboard_summary", "get_agent_stats", "system_overview"] },
};

export default function CapabilitiesPage() {
  const [tools, setTools] = useState<ToolDef[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedGroup, setExpandedGroup] = useState<string | null>("Leads");

  useEffect(() => {
    fetch("/api/v1/athena/state")
      .then((r) => r.json())
      .then((d) => setTools(d.tools || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const toolMap = new Map(tools.map((t) => [t.name, t]));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Athena Capabilities</h1>
          <p className="mt-1 text-sm text-gray-500">{tools.length} tools across 9 categories</p>
        </div>
        <div className="flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-1.5">
          <Sparkles className="h-4 w-4 text-amber-600" />
          <span className="text-sm font-medium text-amber-700">All powered by Athena</span>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}><CardContent className="p-6"><div className="h-20 animate-pulse bg-gray-100 rounded" /></CardContent></Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Object.entries(toolGroups).map(([group, meta]) => {
            const Icon = meta.icon;
            const groupTools = meta.tools.filter((t) => toolMap.has(t));
            const isExpanded = expandedGroup === group;
            return (
              <Card key={group}
                className={`transition-all cursor-pointer hover:shadow-md ${isExpanded ? "ring-2 ring-brand-200" : ""}`}
                onClick={() => setExpandedGroup(isExpanded ? null : group)}
              >
                <CardContent className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${meta.color}`}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{group}</p>
                      <Badge variant="secondary" className="text-[10px]">{groupTools.length} tools</Badge>
                    </div>
                  </div>
                  {isExpanded && (
                    <div className="mt-3 space-y-2 border-t border-gray-100 pt-3">
                      {groupTools.map((toolName) => {
                        const td = toolMap.get(toolName);
                        return (
                          <div key={toolName} className="rounded-lg bg-gray-50 p-2.5">
                            <p className="text-xs font-medium text-gray-900">{toolName}</p>
                            <p className="mt-0.5 text-[11px] text-gray-500 leading-relaxed">{td?.description || ""}</p>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
