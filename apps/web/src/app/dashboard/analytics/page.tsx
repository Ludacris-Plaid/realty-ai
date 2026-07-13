"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchFromApi, getDashboardSummary, type DashboardSummary } from "@/lib/api";
import { TrendingUp, Users, Building2, DollarSign, Activity, Target, ArrowUp, ArrowDown } from "lucide-react";

interface ActivityStat {
  total_activities: number;
  by_intent: Record<string, number>;
  by_status: Record<string, number>;
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [activityStats, setActivityStats] = useState<ActivityStat | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getDashboardSummary(),
      fetchFromApi<ActivityStat>("/activity/stats").catch(() => null),
    ])
      .then(([s, a]) => {
        setSummary(s);
        setActivityStats(a);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const totalPipeline = summary?.total_value || 0;
  const totalLeads = summary?.total_leads || 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-1 text-sm text-gray-500">Business performance and AI agent metrics</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-gray-500">Total Leads</p>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50">
                <Users className="h-4 w-4 text-blue-500" />
              </div>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">{totalLeads}</p>
            <div className="mt-1 flex items-center gap-1 text-xs text-green-600">
              <ArrowUp className="h-3 w-3" /> 12% vs last month
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-gray-500">Active Listings</p>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50">
                <Building2 className="h-4 w-4 text-emerald-500" />
              </div>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">{summary?.active_listings || 0}</p>
            <div className="mt-1 flex items-center gap-1 text-xs text-green-600">
              <ArrowUp className="h-3 w-3" /> 2 new this week
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-gray-500">Pipeline Value</p>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50">
                <DollarSign className="h-4 w-4 text-amber-500" />
              </div>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">${(totalPipeline / 1000000).toFixed(1)}M</p>
            <div className="mt-1 flex items-center gap-1 text-xs text-green-600">
              <ArrowUp className="h-3 w-3" /> Across {summary?.total_listings || 0} properties
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-gray-500">Hot Leads</p>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50">
                <Target className="h-4 w-4 text-red-500" />
              </div>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">{summary?.hot_leads_count || 0}</p>
            <div className="mt-1 flex items-center gap-1 text-xs text-red-600">
              <ArrowUp className="h-3 w-3" /> Needs attention
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Lead Pipeline Status</CardTitle>
            <CardDescription>Distribution by stage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {summary?.leads_by_status && Object.entries(summary.leads_by_status).length > 0 ? (
                Object.entries(summary.leads_by_status).map(([status, count]) => {
                  const pct = totalLeads > 0 ? ((count as number) / totalLeads) * 100 : 0;
                  const colors: Record<string, string> = {
                    NEW: "bg-gray-400", QUALIFYING: "bg-amber-400", QUALIFIED: "bg-emerald-400",
                    CONTACTED: "bg-blue-400", APPOINTMENT_SET: "bg-violet-400", CLOSED_WON: "bg-green-500",
                    CLOSED_LOST: "bg-red-400", DORMANT: "bg-gray-300",
                  };
                  return (
                    <div key={status} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-700 font-medium">{status.replace(/_/g, " ")}</span>
                        <span className="text-gray-500">{count} ({(pct).toFixed(0)}%)</span>
                      </div>
                      <div className="h-2 rounded-full bg-gray-100">
                        <div className={`h-2 rounded-full ${colors[status] || "bg-brand-400"}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-sm text-gray-400">No lead data available</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AI Agent Activity</CardTitle>
            <CardDescription>Actions by agent type</CardDescription>
          </CardHeader>
          <CardContent>
            {activityStats?.by_intent && Object.keys(activityStats.by_intent).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(activityStats.by_intent).map(([intent, count]) => {
                  const total = Object.values(activityStats.by_intent).reduce((a, b) => a + b, 0);
                  const pct = total > 0 ? ((count as number) / total) * 100 : 0;
                  return (
                    <div key={intent} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-700 capitalize">{intent}</span>
                        <span className="text-gray-500">{String(count)}</span>
                      </div>
                      <div className="h-2 rounded-full bg-gray-100">
                        <div className="h-2 rounded-full bg-brand-400" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-gray-400">
                <Activity className="h-8 w-8 mb-2" />
                <p className="text-sm">No AI activity recorded yet</p>
                <p className="text-xs mt-1">Activity is logged when you interact with the AI agents</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
