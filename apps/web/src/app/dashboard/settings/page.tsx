"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Bot, Bell, Shield, CreditCard, Globe, Palette, Webhook, Key, Save, User, Building2 } from "lucide-react";

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
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
                  <Input defaultValue="Sarah" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Last Name</label>
                  <Input defaultValue="Chen" />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Email</label>
                <Input defaultValue="sarah@eliterealty.com" type="email" />
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
        </div>

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
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
