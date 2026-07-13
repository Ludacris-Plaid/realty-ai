"use client";

import { useEffect, useState } from "react";
import { getDashboardSummary, type DashboardSummary } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ActivityFeed } from "@/components/ai/activity-feed";
import { TrendingUp, TrendingDown, Zap, Flame, DollarSign, Building2, Calendar } from "lucide-react";

const greeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
};

function StatCard({ title, value, icon: Icon, trend, loading }: {
  title: string; value: string; icon: React.ElementType; trend?: number; loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-20" />
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-500">{title}</p>
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <Icon className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              {trend !== undefined && (
                <span className={cn("inline-flex items-center gap-0.5 text-sm font-medium", trend >= 0 ? "text-emerald-600" : "text-red-600")}>
                  {trend >= 0 ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
                  {Math.abs(trend)}%
                </span>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

import { cn } from "@/lib/utils";

function RecommendationCard({ item, loading }: { item?: { title: string; description: string; type: string; priority: string }; loading?: boolean }) {
  const priorityColors: Record<string, string> = {
    high: "border-l-red-500 bg-red-50",
    medium: "border-l-amber-500 bg-amber-50",
    low: "border-l-brand-500 bg-brand-50",
  };

  const typeIcons: Record<string, React.ElementType> = {
    lead: Zap,
    listing: Building2,
    deadline: Calendar,
  };

  if (loading) {
    return (
      <div className="flex items-start gap-4 rounded-lg border border-gray-100 p-4">
        <Skeleton className="h-8 w-8 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-full" />
        </div>
      </div>
    );
  }

  if (!item) return null;

  const Icon = typeIcons[item.type] || Zap;
  const borderColor = priorityColors[item.priority] || priorityColors.medium;

  return (
    <div className={cn("flex items-start gap-4 rounded-lg border border-l-4 p-4", borderColor)}>
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-sm">
        <Icon className="h-4 w-4 text-gray-600" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-900">{item.title}</p>
        <p className="mt-0.5 text-xs text-gray-500">{item.description}</p>
      </div>
      <Badge variant={item.priority === "high" ? "danger" : item.priority === "medium" ? "warning" : "default"}>
        {item.priority}
      </Badge>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboardSummary()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {greeting()}, Sarah <span className="ml-1">👋</span>
        </h1>
        <p className="mt-1 text-sm text-gray-500">Here&apos;s your AI-powered business overview</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Hot Leads"
          value={data ? String(data.hot_leads_count) : "—"}
          icon={Flame}
          loading={loading}
        />
        <StatCard
          title="Today's Showings"
          value={data ? String(data.today_showings) : "—"}
          icon={Calendar}
          loading={loading}
        />
        <StatCard
          title="Active Listings"
          value={data ? String(data.active_listings) : "—"}
          icon={Building2}
          loading={loading}
        />
        <StatCard
          title="Pipeline Value"
          value={data ? `$${(data.total_value / 1000).toFixed(0)}k` : "—"}
          icon={DollarSign}
          loading={loading}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-brand-500" />
                AI Recommendations
              </CardTitle>
              <CardDescription>Prioritized actions from your AI agents</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => <RecommendationCard key={i} loading />)}
                </div>
              ) : error ? (
                <p className="text-sm text-red-500">Failed to load: {error}</p>
              ) : (
                <div className="space-y-3">
                  {[
                    { title: "Follow up with Mike Chen", description: "Pre-approved cash buyer ready to close. Response rate: high.", type: "lead", priority: "high" },
                    { title: "Finish 123 Main St MLS description", description: "Listing has been in draft for 3 days. Generate an AI description to publish.", type: "listing", priority: "medium" },
                    { title: "Review contract deadline for Emily Davis", description: "Inspection contingency expires in 2 days.", type: "deadline", priority: "high" },
                  ].map((rec, i) => (
                    <RecommendationCard key={i} item={rec} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-brand-500" />
                AI Agent Activity
              </CardTitle>
              <CardDescription>Recent actions from your team</CardDescription>
            </CardHeader>
            <CardContent>
              <ActivityFeed />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
