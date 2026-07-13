"use client";

import { useEffect, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { getLead, type Lead } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { X, Phone, Mail, Calendar, Star, Target, TrendingUp, User } from "lucide-react";
import { cn } from "@/lib/utils";

const statusColors: Record<string, "default" | "secondary" | "success" | "warning" | "danger"> = {
  new: "default",
  qualifying: "warning",
  qualified: "success",
  contacted: "default",
  "appointment_set": "warning",
  "closed_won": "success",
  "closed_lost": "danger",
};

function formatStatus(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatCurrency(n: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

function ScoreRing({ score }: { score: number }) {
  const color = score >= 70 ? "stroke-emerald-500" : score >= 50 ? "stroke-amber-500" : "stroke-red-500";
  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;

  return (
    <div className="flex flex-col items-center">
      <svg width="96" height="96" className="-rotate-90">
        <circle cx="48" cy="48" r={r} fill="none" stroke="#e5e7eb" strokeWidth="6" />
        <circle cx="48" cy="48" r={r} fill="none" className={color} strokeWidth="6" strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-2xl font-bold text-gray-900">{score}</span>
        <span className="text-xs text-gray-500">Score</span>
      </div>
    </div>
  );
}

export function LeadDetailDialog({ leadId, open, onOpenChange }: { leadId: string; open: boolean; onOpenChange: (open: boolean) => void }) {
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    getLead(leadId)
      .then(setLead)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [leadId, open]);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out" />
        <Dialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-2xl translate-x-[-50%] translate-y-[-50%] rounded-xl bg-white shadow-2xl data-[state=open]:animate-in data-[state=closed]:animate-out max-h-[85vh] overflow-y-auto">
          <Dialog.Close className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600">
            <X className="h-4 w-4" />
          </Dialog.Close>

          {loading ? (
            <div className="p-6 space-y-6">
              <div className="flex items-center gap-4">
                <Skeleton className="h-16 w-16 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-6 w-48" />
                  <Skeleton className="h-4 w-32" />
                </div>
              </div>
              <Skeleton className="h-32 w-full" />
            </div>
          ) : lead ? (
            <div>
              <div className="bg-gradient-to-r from-brand-600 to-brand-800 px-6 py-8 text-white">
                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/20">
                    <User className="h-8 w-8" />
                  </div>
                  <div>
                    <Dialog.Title className="text-xl font-bold">{lead.name}</Dialog.Title>
                    <div className="mt-1 flex items-center gap-2">
                      <Badge variant={statusColors[lead.status] || "secondary"}>
                        {formatStatus(lead.status)}
                      </Badge>
                      <span className="text-sm text-white/70">{lead.source}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-6 space-y-6">
                <div className="flex items-center justify-center">
                  <div className="relative">
                    <ScoreRing score={lead.score} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg bg-gray-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Budget</p>
                    <p className="mt-1 text-lg font-semibold text-gray-900">{formatCurrency(lead.budget)}</p>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Email</p>
                    <p className="mt-1 text-sm font-medium text-gray-900">{lead.email}</p>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Phone</p>
                    <p className="mt-1 text-sm font-medium text-gray-900">{lead.phone}</p>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Created</p>
                    <p className="mt-1 text-sm font-medium text-gray-900">{new Date(lead.created_at).toLocaleDateString()}</p>
                  </div>
                </div>

                {lead.notes && (
                  <div>
                    <p className="mb-2 text-sm font-medium text-gray-700">AI Notes</p>
                    <p className="text-sm text-gray-600">{lead.notes}</p>
                  </div>
                )}

                <Separator />

                <div className="flex gap-3">
                  <Button variant="default" size="md" className="flex-1">
                    <Phone className="h-4 w-4" /> Call
                  </Button>
                  <Button variant="outline" size="md" className="flex-1">
                    <Mail className="h-4 w-4" /> Email
                  </Button>
                  <Button variant="outline" size="md" className="flex-1">
                    <Calendar className="h-4 w-4" /> Schedule
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 text-center text-gray-500">Lead not found.</div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
