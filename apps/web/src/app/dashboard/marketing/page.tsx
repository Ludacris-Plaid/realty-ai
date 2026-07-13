"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Megaphone, Sparkles, Mail, Share2, FileText, TrendingUp, Send, Plus } from "lucide-react";

const campaigns = [
  { id: 1, name: "Summer Open House Blitz", status: "active", type: "email", sent: 124, opened: 89, responded: 12 },
  { id: 2, name: "New Listing Alert - Windermere", status: "active", type: "social", sent: 450, opened: 210, responded: 8 },
  { id: 3, name: "Referral Request - July", status: "draft", type: "email", sent: 0, opened: 0, responded: 0 },
  { id: 4, name: "Market Report Q3", status: "scheduled", type: "newsletter", sent: 0, opened: 0, responded: 0 },
];

const posts = [
  { id: 1, content: "Just listed! Charming 4-bed family home in Windermere. Open house this Sunday 2-4PM. #EdmontonRealEstate", platform: "Instagram", scheduled: "2026-07-14", status: "scheduled" },
  { id: 2, content: "📊 July Market Update: Edmonton housing inventory up 15%. Sellers market cooling slightly. Contact me for a free home valuation!", platform: "Facebook", scheduled: "2026-07-15", status: "draft" },
];

export default function MarketingPage() {
  const [activeTab, setActiveTab] = useState<"campaigns" | "social" | "content">("campaigns");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Marketing</h1>
          <p className="mt-1 text-sm text-gray-500">AI-powered campaigns, social media, and content</p>
        </div>
        <Button onClick={() => alert("AI content generation coming soon in Phase 2. Athena will write your campaigns.")}>
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
                <p className="text-2xl font-bold text-brand-600">4</p>
                <p className="text-xs text-gray-500">Total Campaigns</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-green-600">2</p>
                <p className="text-xs text-gray-500">Active</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-gray-900">32%</p>
                <p className="text-xs text-gray-500">Avg. Open Rate</p>
              </CardContent>
            </Card>
          </div>

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
        </>
      )}

      {activeTab === "social" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-700">Scheduled Posts</p>
            <Button variant="outline" size="sm"><Plus className="h-3 w-3" /> New Post</Button>
          </div>
          {posts.map((p) => (
            <Card key={p.id}>
              <CardContent className="p-4 space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <p className="text-sm text-gray-800">{p.content}</p>
                  <Badge variant={p.status === "scheduled" ? "warning" : "default"} className="shrink-0">
                    {p.status}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{p.platform} · {p.scheduled}</span>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm">Edit</Button>
                    <Button variant="ghost" size="sm" className="text-red-500">Delete</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === "content" && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {["Listing Description Templates", "Email Templates", "Social Media Posts", "Market Reports", "Newsletter Archive", "Brand Assets"].map((item) => (
            <Card key={item} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="p-6 text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-brand-50">
                  <FileText className="h-6 w-6 text-brand-500" />
                </div>
                <p className="text-sm font-semibold text-gray-900">{item}</p>
                <p className="mt-1 text-xs text-gray-400">View library</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
