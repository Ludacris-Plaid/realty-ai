"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { gmailApi, type EmailMessage, type GmailStatus, type SyncResult } from "@/lib/api";
import {
  Inbox, Send, FileEdit, RefreshCw, Reply, ExternalLink,
  Mail, MailOpen, Sparkles, CheckCircle, Loader2, AlertCircle,
} from "lucide-react";

const classificationLabels: Record<string, { label: string; color: string; icon: string }> = {
  buyer_lead: { label: "Buyer Lead", color: "bg-emerald-100 text-emerald-800", icon: "💰" },
  seller_lead: { label: "Seller Lead", color: "bg-blue-100 text-blue-800", icon: "🏠" },
  follow_up: { label: "Follow Up", color: "bg-amber-100 text-amber-800", icon: "📋" },
  pre_approval: { label: "Pre-Approval", color: "bg-purple-100 text-purple-800", icon: "✅" },
  general: { label: "General", color: "bg-gray-100 text-gray-800", icon: "📧" },
};

function classifyLabel(cls: string | null) {
  return classificationLabels[cls || ""] || classificationLabels.general;
}

function EmailListItem({ email, active, onClick }: {
  email: EmailMessage;
  active: boolean;
  onClick: () => void;
}) {
  const cls = classifyLabel(email.ai_classification);
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 border-b border-gray-100 transition-colors hover:bg-gray-50 ${
        active ? "bg-brand-50 border-l-2 border-l-brand-500" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            {email.is_unread ? (
              <Mail className="h-4 w-4 text-brand-500 shrink-0" />
            ) : (
              <MailOpen className="h-4 w-4 text-gray-300 shrink-0" />
            )}
            <span className={`text-sm truncate ${email.is_unread ? "font-semibold text-gray-900" : "text-gray-700"}`}>
              {email.sender_name || email.sender}
            </span>
          </div>
          <p className={`text-sm mt-1 truncate ${email.is_unread ? "font-medium text-gray-900" : "text-gray-600"}`}>
            {email.subject}
          </p>
          <p className="text-xs text-gray-400 mt-0.5 truncate">{email.snippet}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 mt-2">
        {email.ai_classification && (
          <span className={`text-xs px-2 py-0.5 rounded-full ${cls.color}`}>
            {cls.label}
          </span>
        )}
        <span className="text-xs text-gray-400">
          {email.received_at ? new Date(email.received_at).toLocaleDateString() : ""}
        </span>
      </div>
    </button>
  );
}

function EmailDetail({ email, onReply }: { email: EmailMessage; onReply: (body: string) => void }) {
  const cls = classifyLabel(email.ai_classification);
  return (
    <div className="p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">{email.subject}</h2>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-sm font-medium text-gray-700">{email.sender_name || email.sender}</span>
          <span className="text-xs text-gray-400">
            {email.received_at ? new Date(email.received_at).toLocaleString() : ""}
          </span>
        </div>
        <span className="text-xs text-gray-500">{email.sender}</span>
      </div>

      <div className="flex items-center gap-2 mb-4">
        {email.ai_classification && (
          <Badge className={cls.color}>{cls.label}</Badge>
        )}
        {email.ai_suggested_action && (
          <Badge variant="outline">{email.ai_suggested_action.replace(/_/g, " ")}</Badge>
        )}
      </div>

      {email.ai_draft_reply && (
        <Card className="mb-4 border-brand-200 bg-brand-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-brand-700 mb-2">
              <Sparkles className="h-4 w-4" /> AI Suggested Reply
            </div>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{email.ai_draft_reply}</p>
            <div className="flex gap-2 mt-3">
              <Button size="sm" onClick={() => onReply(email.ai_draft_reply!)}>
                <Reply className="h-3.5 w-3.5" /> Use Draft
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Separator className="my-4" />

      <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
        {email.body || email.snippet || "(No content)"}
      </div>
    </div>
  );
}

export default function EmailPage() {
  const [emails, setEmails] = useState<EmailMessage[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [gmailStatus, setGmailStatus] = useState<GmailStatus | null>(null);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const selected = emails.find((e) => e.id === selectedId) || null;

  const loadEmails = useCallback(async () => {
    try {
      const data = await gmailApi.list(50, filter === "unread");
      setEmails(data.emails);
      if (!data.emails.find((e) => e.id === selectedId)) {
        setSelectedId(data.emails[0]?.id || null);
      }
    } catch (e) {
      console.error("Failed to load emails:", e);
    } finally {
      setLoading(false);
    }
  }, [filter, selectedId]);

  useEffect(() => {
    loadEmails();
    gmailApi.status().then(setGmailStatus).catch(() => {});
  }, [loadEmails]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const result = await gmailApi.sync();
      setSyncResult(result);
      await loadEmails();
    } catch (e) {
      console.error("Sync failed:", e);
    } finally {
      setSyncing(false);
    }
  };

  const handleConnectGmail = async () => {
    try {
      const { auth_url } = await gmailApi.authUrl();
      window.open(auth_url, "_blank", "width=600,height=700");
    } catch (e) {
      console.error("Auth URL failed:", e);
    }
  };

  const handleReply = async (replyBody: string) => {
    if (!selected) return;
    try {
      await gmailApi.createDraft(selected.id, replyBody);
      await loadEmails();
    } catch (e) {
      console.error("Draft creation failed:", e);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Email</h1>
          <p className="text-sm text-gray-500 mt-1">
            {gmailStatus?.connected
              ? `Connected as ${gmailStatus.email}`
              : "Connect Gmail to sync your inbox"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {gmailStatus?.connected ? (
            <Badge variant="success" className="flex items-center gap-1">
              <CheckCircle className="h-3 w-3" /> Gmail Connected
            </Badge>
          ) : (
            <Button variant="outline" size="sm" onClick={handleConnectGmail}>
              <ExternalLink className="h-4 w-4" /> Connect Gmail
            </Button>
          )}
          <Button size="sm" onClick={handleSync} disabled={syncing}>
            {syncing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {syncing ? "Syncing..." : "Sync"}
          </Button>
        </div>
      </div>

      {syncResult && (
        <Card className="border-brand-200 bg-brand-50">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle className="h-4 w-4 text-brand-600" />
              <span className="text-brand-800">{syncResult.message}</span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setSyncResult(null)}>Dismiss</Button>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-2 mb-2">
        <Button
          variant={filter === "all" ? "default" : "ghost"}
          size="sm"
          onClick={() => setFilter("all")}
        >
          <Inbox className="h-4 w-4" /> All
        </Button>
        <Button
          variant={filter === "unread" ? "default" : "ghost"}
          size="sm"
          onClick={() => setFilter("unread")}
        >
          <Mail className="h-4 w-4" /> Unread
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Inbox className="h-4 w-4 text-brand-500" />
              Inbox
              {emails.filter((e) => e.is_unread).length > 0 && (
                <Badge>{emails.filter((e) => e.is_unread).length} unread</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-4 space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                ))}
              </div>
            ) : emails.length === 0 ? (
              <div className="p-8 text-center">
                <Inbox className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No emails yet</p>
                <p className="text-xs text-gray-400 mt-1">Click Sync to fetch your inbox</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
                {emails.map((email) => (
                  <EmailListItem
                    key={email.id}
                    email={email}
                    active={selected?.id === email.id}
                    onClick={() => setSelectedId(email.id)}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <MailOpen className="h-4 w-4 text-brand-500" />
              {selected ? selected.subject : "Message"}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-4">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-32 w-full" />
              </div>
            ) : selected ? (
              <EmailDetail email={selected} onReply={handleReply} />
            ) : (
              <div className="p-8 text-center">
                <MailOpen className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">Select an email to read</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
