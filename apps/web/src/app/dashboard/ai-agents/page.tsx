"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Bot, UserCheck, FileText, BarChart, Megaphone, Search, Shield, Zap, Activity } from "lucide-react";
import { fetchFromApi } from "@/lib/api";

const agentMeta: Record<string, { name: string; description: string; icon: React.ElementType; color: string }> = {
  lead: { name: "Lead Agent", description: "Qualifies leads, scores pipeline, recommends follow-ups", icon: UserCheck, color: "bg-blue-500" },
  listing: { name: "Listing Agent", description: "Generates MLS descriptions, compares properties", icon: FileText, color: "bg-emerald-500" },
  marketing: { name: "Marketing Agent", description: "Creates campaigns, social posts, content", icon: Megaphone, color: "bg-purple-500" },
  transaction: { name: "Transaction Agent", description: "Tracks deadlines, manages contract dates", icon: Shield, color: "bg-amber-500" },
  document: { name: "Document Agent", description: "Analyzes contracts, extracts key terms", icon: Search, color: "bg-rose-500" },
  research: { name: "Research Agent", description: "Market trends, neighborhood insights", icon: BarChart, color: "bg-cyan-500" },
  general: { name: "General Assistant", description: "Handles general questions and requests", icon: Bot, color: "bg-gray-500" },
};

interface AgentInfo {
  id: string;
  name: string;
  description: string;
  tool_count: number;
}

export default function AIAgentsPage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFromApi<{ agents: AgentInfo[] }>("/supervisor/agents")
      .then((d) => setAgents(d.agents || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Agents</h1>
        <p className="mt-1 text-sm text-gray-500">Specialist AI agents working for your business</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="bg-gradient-to-br from-brand-600 to-brand-800 text-white">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <Zap className="h-8 w-8" />
              <div>
                <p className="text-lg font-bold">Multi-Agent System</p>
                <p className="text-sm text-white/70">Active · {agents.length} agents deployed</p>
              </div>
            </div>
            <Separator className="my-4 bg-white/20" />
            <p className="text-sm text-white/80">Intelligent routing: your request is analyzed and sent to the best specialist agent for the job.</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-brand-500" />
              <div>
                <p className="text-lg font-bold text-gray-900">Agent Activity</p>
                <p className="text-sm text-gray-500">Real-time actions and decisions</p>
              </div>
            </div>
            <Separator className="my-4" />
            <p className="text-sm text-gray-500">View the <span className="text-brand-600 font-medium">Activity Feed</span> on the dashboard for a complete log of all agent actions, approvals needed, and completed tasks.</p>
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Specialist Agents</h2>
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i}><CardContent className="p-6"><div className="h-24 animate-pulse bg-gray-100 rounded" /></CardContent></Card>
            ))}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map((agent) => {
              const meta = agentMeta[agent.id] || { name: agent.name, description: agent.description, icon: Bot, color: "bg-gray-500" };
              const Icon = meta.icon;
              return (
                <Card key={agent.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-3">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${meta.color}`}>
                        <Icon className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{meta.name}</p>
                        <Badge variant="secondary" className="text-[10px]">{agent.tool_count} tools</Badge>
                      </div>
                    </div>
                    <p className="mt-3 text-xs text-gray-500 leading-relaxed">{meta.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Agent Configuration</CardTitle>
          <CardDescription>Control which agents are active and how they behave</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {["Intent Classification", "Model Routing", "Human Approval", "Activity Logging"].map((setting) => (
              <div key={setting} className="flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-gray-900">{setting}</p>
                  <p className="text-xs text-gray-500">Configure how {setting.toLowerCase()} works</p>
                </div>
                <Button variant="outline" size="sm">Configure</Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
