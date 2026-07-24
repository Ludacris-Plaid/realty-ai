"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Bot, Bell, Shield, CreditCard, Globe, Palette, Webhook, Key, Save, User, Building2, Eye, EyeOff, CheckCircle, XCircle, RefreshCw, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface BotStatus {
  telegram: { configured: boolean; env_token_set: boolean; db_configured: boolean; db_config: Record<string, any> };
  slack: { configured: boolean; env_bot_token_set: boolean; env_signing_secret_set: boolean; db_configured: boolean; db_config: Record<string, any> };
}

interface BotConfig {
  platform: string;
  config: Record<string, string>;
  enabled: boolean;
}

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");

  // Load user from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem("athena_user");
      if (raw) {
        const u = JSON.parse(raw);
        setFirstName(u.name || "");
        setLastName(u.last_name || "");
        setEmail(u.email || "");
      }
    } catch { /* ignore */ }
  }, []);

  // ─── Bot integration state ─────────────────────────────────────────────────
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusError, setStatusError] = useState("");

  // Telegram form
  const [tgToken, setTgToken] = useState("");
  const [tgEnabled, setTgEnabled] = useState(false);
  const [tgShowToken, setTgShowToken] = useState(false);
  const [tgSaving, setTgSaving] = useState(false);
  const [tgMsg, setTgMsg] = useState<{ ok: boolean; text: string } | null>(null);

  // Slack form
  const [slackToken, setSlackToken] = useState("");
  const [slackSecret, setSlackSecret] = useState("");
  const [slackEnabled, setSlackEnabled] = useState(false);
  const [slackShowToken, setSlackShowToken] = useState(false);
  const [slackSaving, setSlackSaving] = useState(false);
  const [slackMsg, setSlackMsg] = useState<{ ok: boolean; text: string } | null>(null);

  // Load initial status
  const fetchStatus = async () => {
    setStatusLoading(true);
    setStatusError("");
    try {
      const res = await fetch(`${API_BASE}/athena/bots/status`);
      if (!res.ok) throw new Error(`Status fetch failed: ${res.status}`);
      const data: BotStatus = await res.json();
      setBotStatus(data);

      // Populate form fields from DB (or env)
      const tgCfg = data.telegram.db_config?.config || {};
      setTgToken(tgCfg.bot_token || "");
      setTgEnabled(data.telegram.db_configured || data.telegram.env_token_set);

      const slackCfg = data.slack.db_config?.config || {};
      setSlackToken(slackCfg.bot_token || "");
      setSlackSecret(slackCfg.signing_secret || "");
      setSlackEnabled(data.slack.db_configured || (data.slack.env_bot_token_set && data.slack.env_signing_secret_set));
    } catch (e: any) {
      setStatusError(e.message);
    } finally {
      setStatusLoading(false);
    }
  };

  useEffect(() => { fetchStatus(); }, []);

  // ─── Save bot config ──────────────────────────────────────────────────────
  const saveBotConfig = async (platform: string, config: Record<string, string>, enabled: boolean) => {
    const setMsg = platform === "telegram"
      ? (m: typeof tgMsg) => setTgMsg(m)
      : (m: typeof slackMsg) => setSlackMsg(m);
    const setSaving = platform === "telegram" ? setTgSaving : setSlackSaving;

    setSaving(true);
    setMsg(null);
    try {
      const res = await fetch(`${API_BASE}/athena/bots/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform, config, enabled }),
      });
      if (!res.ok) throw new Error(`Save failed: ${res.status}`);
      setMsg({ ok: true, text: "Saved successfully." });
      await fetchStatus(); // Refresh status
    } catch (e: any) {
      setMsg({ ok: false, text: e.message });
    } finally {
      setSaving(false);
    }
  };

  // ─── Delete bot config ────────────────────────────────────────────────────
  const deleteBotConfig = async (platform: string) => {
    const setMsg = platform === "telegram" ? setTgMsg : setSlackMsg;

    if (!confirm(`Remove ${platform} configuration?`)) return;
    try {
      const res = await fetch(`${API_BASE}/athena/bots/config/${platform}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
      // Reset form
      if (platform === "telegram") {
        setTgToken("");
        setTgEnabled(false);
        setTgMsg({ ok: true, text: "Configuration removed." });
      } else {
        setSlackToken("");
        setSlackSecret("");
        setSlackEnabled(false);
        setSlackMsg({ ok: true, text: "Configuration removed." });
      }
      await fetchStatus();
    } catch (e: any) {
      setMsg({ ok: false, text: e.message });
    }
  };

  // ─── Set Telegram webhook ─────────────────────────────────────────────────
  const setTelegramWebhook = async () => {
    setTgMsg(null);
    try {
      const res = await fetch(`${API_BASE}/athena/telegram/set-webhook`, { method: "POST" });
      const data = await res.json();
      if (data.ok) {
        setTgMsg({ ok: true, text: "Webhook registered!" });
      } else {
        setTgMsg({ ok: false, text: data.error || "Webhook registration failed" });
      }
    } catch (e: any) {
      setTgMsg({ ok: false, text: e.message });
    }
  };

  const handleSave = async () => {
    setSaved(true);
    const token = localStorage.getItem("athena_token");
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://realty-ai-api-production.up.railway.app";
    try {
      await fetch(`${API_BASE}/api/v1/auth/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          name: `${firstName} ${lastName}`.trim(),
          email,
        }),
      });
    } catch { /* silent — localStorage save as fallback */ }
    // Update localStorage too
    try {
      const raw = localStorage.getItem("athena_user");
      if (raw) {
        const u = JSON.parse(raw);
        u.name = `${firstName} ${lastName}`.trim();
        u.email = email;
        localStorage.setItem("athena_user", JSON.stringify(u));
      }
    } catch { /* ignore */ }
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">Manage your account and application preferences</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {/* ── Profile ── */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-brand-500" /> Profile
              </CardTitle>
              <CardDescription>Your personal and brokerage information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">First Name</label>
                  <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Last Name</label>
                  <Input value={lastName} onChange={(e) => setLastName(e.target.value)} />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Email</label>
                <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Phone</label>
                <Input defaultValue="(555) 123-4567" />
              </div>
              <Button onClick={handleSave}>
                <Save className="h-4 w-4" /> {saved ? "Saved!" : "Save Changes"}
              </Button>
            </CardContent>
          </Card>

          {/* ── Brokerage ── */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-brand-500" /> Brokerage
              </CardTitle>
              <CardDescription>Your real estate brokerage details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Brokerage Name</label>
                <Input defaultValue="Edmonton Elite Realty" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">License Number</label>
                <Input defaultValue="RE12345" />
              </div>
              <Button variant="outline" onClick={handleSave}>Save</Button>
            </CardContent>
          </Card>

          {/* ── AI Preferences ── */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-brand-500" /> AI Preferences
              </CardTitle>
              <CardDescription>Configure how AI agents work for you</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-gray-900">Auto-follow up on leads</p>
                  <p className="text-xs text-gray-500">AI automatically sends follow-up emails to new leads</p>
                </div>
                <div className="h-6 w-11 rounded-full bg-brand-600 cursor-pointer relative">
                  <div className="h-5 w-5 rounded-full bg-white absolute right-0.5 top-0.5 shadow" />
                </div>
              </div>
              <Separator />
              <div className="flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-gray-900">Daily briefing</p>
                  <p className="text-xs text-gray-500">Receive a daily AI-generated business summary</p>
                </div>
                <div className="h-6 w-11 rounded-full bg-gray-200 cursor-pointer relative">
                  <div className="h-5 w-5 rounded-full bg-white absolute left-0.5 top-0.5 shadow" />
                </div>
              </div>
              <Separator />
              <div>
                <label className="text-sm font-medium text-gray-700">AI Voice Tone</label>
                <select className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                  <option>Professional</option>
                  <option>Friendly</option>
                  <option>Casual</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* ── Bot Integrations (Telegram / Slack) ── */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Webhook className="h-5 w-5 text-brand-500" /> Bot Integrations
              </CardTitle>
              <CardDescription>
                Connect your own Telegram and Slack bots to Athena. Tokens are stored encrypted in your database.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">

              {/* Telegram */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-blue-500" />
                    <h3 className="text-base font-semibold text-gray-900">Telegram</h3>
                    {statusLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                    ) : (
                      <Badge variant={botStatus?.telegram.configured ? "success" : "default"} className="text-[10px] px-1.5 py-0">
                        {botStatus?.telegram.configured ? "Connected" : "Not configured"}
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="relative">
                    <Input
                      label="Bot Token"
                      placeholder="1234567890:ABCdefGHIjklmNOPqrstUVwxyz"
                      value={tgToken}
                      onChange={(e) => setTgToken(e.target.value)}
                      type={tgShowToken ? "text" : "password"}
                    />
                    <button
                      type="button"
                      onClick={() => setTgShowToken(!tgShowToken)}
                      className="absolute right-2 bottom-2.5 text-gray-400 hover:text-gray-600"
                    >
                      {tgShowToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className={`h-5 w-9 rounded-full cursor-pointer relative transition-colors ${tgEnabled ? "bg-blue-600" : "bg-gray-300"}`}
                      onClick={() => setTgEnabled(!tgEnabled)}
                    >
                      <div className={`h-4 w-4 rounded-full bg-white absolute top-0.5 shadow transition-transform ${tgEnabled ? "right-0.5" : "left-0.5"}`} />
                    </div>
                    <span className="text-xs text-gray-500">Enable Telegram bot</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      onClick={() => saveBotConfig("telegram", { bot_token: tgToken }, tgEnabled)}
                      disabled={tgSaving || !tgToken}
                    >
                      {tgSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                      Save Token
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={setTelegramWebhook}
                      disabled={!tgEnabled}
                    >
                      <Webhook className="h-4 w-4" /> Set Webhook
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-500 border-red-200 hover:bg-red-50"
                      onClick={() => deleteBotConfig("telegram")}
                    >
                      Remove
                    </Button>
                  </div>
                  {tgMsg && (
                    <p className={`text-xs flex items-center gap-1 ${tgMsg.ok ? "text-green-600" : "text-red-600"}`}>
                      {tgMsg.ok ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                      {tgMsg.text}
                    </p>
                  )}
                  <details className="text-xs text-gray-400">
                    <summary className="cursor-pointer hover:text-gray-600">How to get a Telegram Bot Token</summary>
                    <ol className="mt-2 ml-4 list-decimal space-y-1 text-gray-500">
                      <li>Open Telegram and search for <strong>@BotFather</strong></li>
                      <li>Send <code className="bg-gray-100 px-1 rounded">/newbot</code> and follow the prompts</li>
                      <li>BotFather will give you an API token — paste it above</li>
                      <li>Click <strong>Save Token</strong>, then <strong>Set Webhook</strong></li>
                    </ol>
                  </details>
                </div>
              </div>

              <Separator />

              {/* Slack */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-purple-500" />
                    <h3 className="text-base font-semibold text-gray-900">Slack</h3>
                    {statusLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                    ) : (
                      <Badge variant={botStatus?.slack.configured ? "success" : "default"} className="text-[10px] px-1.5 py-0">
                        {botStatus?.slack.configured ? "Connected" : "Not configured"}
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="relative">
                    <Input
                      label="Bot Token"
                      placeholder="xoxb-1234567890-abc123def456"
                      value={slackToken}
                      onChange={(e) => setSlackToken(e.target.value)}
                      type={slackShowToken ? "text" : "password"}
                    />
                    <button
                      type="button"
                      onClick={() => setSlackShowToken(!slackShowToken)}
                      className="absolute right-2 bottom-2.5 text-gray-400 hover:text-gray-600"
                    >
                      {slackShowToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  <Input
                    label="Signing Secret"
                    placeholder="abc123def456..."
                    value={slackSecret}
                    onChange={(e) => setSlackSecret(e.target.value)}
                    type="password"
                  />
                  <div className="flex items-center gap-2">
                    <div
                      className={`h-5 w-9 rounded-full cursor-pointer relative transition-colors ${slackEnabled ? "bg-purple-600" : "bg-gray-300"}`}
                      onClick={() => setSlackEnabled(!slackEnabled)}
                    >
                      <div className={`h-4 w-4 rounded-full bg-white absolute top-0.5 shadow transition-transform ${slackEnabled ? "right-0.5" : "left-0.5"}`} />
                    </div>
                    <span className="text-xs text-gray-500">Enable Slack bot</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      onClick={() => saveBotConfig("slack", { bot_token: slackToken, signing_secret: slackSecret }, slackEnabled)}
                      disabled={slackSaving || !slackToken || !slackSecret}
                    >
                      {slackSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                      Save Credentials
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-500 border-red-200 hover:bg-red-50"
                      onClick={() => deleteBotConfig("slack")}
                    >
                      Remove
                    </Button>
                  </div>
                  {slackMsg && (
                    <p className={`text-xs flex items-center gap-1 ${slackMsg.ok ? "text-green-600" : "text-red-600"}`}>
                      {slackMsg.ok ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                      {slackMsg.text}
                    </p>
                  )}
                  <details className="text-xs text-gray-400">
                    <summary className="cursor-pointer hover:text-gray-600">How to set up a Slack bot</summary>
                    <ol className="mt-2 ml-4 list-decimal space-y-1 text-gray-500">
                      <li>Go to <strong>api.slack.com/apps</strong> and create a new app</li>
                      <li>Under <strong>OAuth &amp; Permissions</strong>, add scopes: <code className="bg-gray-100 px-1 rounded">chat:write</code>, <code className="bg-gray-100 px-1 rounded">channels:history</code>, <code className="bg-gray-100 px-1 rounded">app_mentions:read</code></li>
                      <li>Install the app to your workspace and copy the <strong>Bot Token</strong> (xoxb-...)</li>
                      <li>Under <strong>Basic Information</strong>, copy the <strong>Signing Secret</strong></li>
                      <li>Enable <strong>Event Subscriptions</strong> with URL: <code className="bg-gray-100 px-1 rounded">{process.env.NEXT_PUBLIC_API_URL || "..."}/athena/slack/events</code></li>
                      <li>Subscribe to <code className="bg-gray-100 px-1 rounded">message.channels</code> and <code className="bg-gray-100 px-1 rounded">app_mention</code></li>
                    </ol>
                  </details>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Right sidebar ── */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-brand-500" /> Notifications
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {["New lead alerts", "Showing reminders", "Contract deadlines", "Weekly summary"].map((n) => (
                <div key={n} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{n}</span>
                  <div className="h-5 w-9 rounded-full bg-brand-600 cursor-pointer relative">
                    <div className="h-4 w-4 rounded-full bg-white absolute right-0.5 top-0.5 shadow" />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-brand-500" /> Integrations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { name: "Google Calendar", connected: false },
                { name: "Gmail", connected: false },
                { name: "Twilio SMS", connected: false },
                { name: "MLS Sync", connected: false },
              ].map((int) => (
                <div key={int.name} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{int.name}</span>
                  <Badge variant={int.connected ? "success" : "default"}>
                    {int.connected ? "Connected" : "Connect"}
                  </Badge>
                </div>
              ))}
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700 flex items-center gap-1">
                  <Bot className="h-3.5 w-3.5 text-blue-500" /> Telegram Bot
                </span>
                <Badge variant={botStatus?.telegram.configured ? "success" : "default"}>
                  {botStatus?.telegram.configured ? "Connected" : "Connect"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700 flex items-center gap-1">
                  <Bot className="h-3.5 w-3.5 text-purple-500" /> Slack Bot
                </span>
                <Badge variant={botStatus?.slack.configured ? "success" : "default"}>
                  {botStatus?.slack.configured ? "Connected" : "Connect"}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
