"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Megaphone, Sparkles, Mail, Share2, FileText, TrendingUp, Send, Plus, Loader2 } from "lucide-react";

const statCards = ["Total Campaigns", "Active", "Avg. Open Rate"];

type Campaign = {
  id: string;
  name: string;
  status: string;
  type: string;
  sent: number;
  opened: number;
  responded: number;
  audience: string;
};

export default function MarketingPage() {
  const [activeTab, setActiveTab] = useState<"campaigns" | "social" | "content">("campaigns");
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://realty-ai-api-production.up.railway.app";
    fetch(`${API_BASE}/api/v1/campaigns`)
      .then((r) => r.json())
      .then((data) => setCampaigns(data.campaigns || []))
      .catch(() => setCampaigns([]))
      .finally(() => setLoading(false));
  }, []);

  const totalCampaigns = campaigns.length;
  const activeCampaigns = campaigns.filter((c) => c.status === "active").length;
  const avgOpenRate = totalCampaigns > 0
    ? Math.round(campaigns.reduce((sum, c) => sum + (c.sent > 0 ? Math.round(c.opened / c.sent * 100) : 0), 0) / totalCampaigns)
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Marketing</h1>
          <p className="mt-1 text-sm text-gray-500">AI-powered campaigns, social media, and content</p>
        </div>
        <Button onClick={() => alert("AI content generation coming soon. Ask Athena to write your campaigns.")}>
          <Sparkles className="h-4 w-4" /> Generate with AI
        </Button>
      </div>

      <div className="flex gap-2 border-b border-gray-200 pb-px">
        {(["campaigns", "social", "content"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab ? "border-brand-600 text-brand-600" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab === "campaigns" ? "Campaigns" : tab === "social" ? "Social Media" : "Content Library"}
          </button>
        ))}
      </div>

      {activeTab === "campaigns" && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-brand-600">{totalCampaigns}</p>
                <p className="text-xs text-gray-500">Total Campaigns</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-green-600">{activeCampaigns}</p>
                <p className="text-xs text-gray-500">Active</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-gray-900">{avgOpenRate}%</p>
                <p className="text-xs text-gray-500">Avg. Open Rate</p>
              </CardContent>
            </Card>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : campaigns.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <Mail className="h-12 w-12" />
              <p className="mt-4 text-sm">No campaigns yet</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={() => alert("Ask Athena to launch a campaign!")}>
                <Sparkles className="h-4 w-4" /> Ask Athena
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {campaigns.map((c) => (
                <Card key={c.id} className="hover:shadow-sm transition-shadow">
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                        c.status === "active" ? "bg-green-100" : c.status === "draft" ? "bg-gray-100" : "bg-amber-100"
                      }`}>
                        {c.type === "email" ? <Mail className="h-5 w-5" /> : c.type === "social" ? <Share2 className="h-5 w-5" /> : <FileText className="h-5 w-5" />}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{c.name}</p>
                        <p className="text-xs text-gray-500">
                          {c.sent > 0 ? `${c.sent} sent · ${c.opened} opened · ${c.responded} responses` : "Not yet sent"}
                        </p>
                      </div>
                    </div>
                    <Badge variant={c.status === "active" ? "success" : c.status === "draft" ? "default" : "warning"}>
                      {c.status}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === "social" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-700">Scheduled Posts</p>
            <Button variant="outline" size="sm" onClick={() => alert("Ask Athena to create social posts for you!")}>
              <Plus className="h-3 w-3" /> New Post
            </Button>
          </div>
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <Share2 className="h-12 w-12" />
            <p className="mt-4 text-sm">Social media integration coming soon</p>
            <p className="text-xs text-gray-400 mt-1">Ask Athena to draft posts in the meantime</p>
          </div>
        </div>
      )}

      {activeTab === "content" && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {["Listing Description Templates", "Email Templates", "Social Media Posts", "Market Reports", "Newsletter Archive", "Brand Assets"].map((item) => (
            <Card key={item} className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => alert(`Ask Athena to generate ${item.toLowerCase()} for you.`)}>
              <CardContent className="p-6 text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-brand-50">
                  <FileText className="h-6 w-6 text-brand-500" />
                </div>
                <p className="text-sm font-semibold text-gray-900">{item}</p>
                <p className="mt-1 text-xs text-gray-400">Ask Athena</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}