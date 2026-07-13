"use client";

import { useEffect, useState, useCallback } from "react";
import { getActivity, type ActivityItem } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Bot, Sparkles, Search, FileText, MessageSquare, Clock } from "lucide-react";

const agentIcons: Record<string, React.ElementType> = {
  lead: Sparkles,
  listing: Search,
  document: FileText,
  chatbot: MessageSquare,
};

const agentColors: Record<string, string> = {
  lead: "bg-amber-100 text-amber-700",
  listing: "bg-cyan-100 text-cyan-700",
  document: "bg-amber-100 text-amber-700",
  chatbot: "bg-brand-100 text-brand-700",
};

function ActivityItemCard({ item }: { item: ActivityItem }) {
  const agentType = item.agent_name?.toLowerCase().replace(/\s+/g, "_") || "general";
  const Icon = agentIcons[agentType] || Bot;
  const colorClass = agentColors[agentType] || "bg-gray-100 text-gray-700";
  const timeAgo = getTimeAgo(item.created_at);

  return (
    <div className="flex gap-3">
      <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", colorClass)}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-gray-900">{item.agent_name}</p>
          <Badge variant="secondary" className="text-[10px] uppercase tracking-wider px-1.5 py-0">
            {item.agent_name}
          </Badge>
        </div>
        <p className="mt-0.5 text-sm text-gray-600">{item.action}</p>
        <p className="mt-1 flex items-center gap-1 text-xs text-gray-400">
          <Clock className="h-3 w-3" />
          {timeAgo}
        </p>
      </div>
    </div>
  );
}

function getTimeAgo(timestamp: string): string {
  const now = Date.now();
  const then = new Date(timestamp).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function ActivityFeed() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(() => {
    getActivity()
      .then(setActivities)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetch();
    const interval = setInterval(fetch, 30000);
    return () => clearInterval(interval);
  }, [fetch]);

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-500">Failed to load activity: {error}</p>;
  }

  if (!activities.length) {
    return <p className="text-sm text-gray-400">No recent activity.</p>;
  }

  return (
    <div className="space-y-4">
      {activities.map((item) => (
        <ActivityItemCard key={item.id} item={item} />
      ))}
    </div>
  );
}
