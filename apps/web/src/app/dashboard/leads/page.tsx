"use client";

import { useEffect, useState } from "react";
import { getLeads, type Lead } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { LeadDetailDialog } from "@/components/leads/lead-detail";
import { cn } from "@/lib/utils";
import { DollarSign, User, ArrowUpRight } from "lucide-react";

const columns = [
  { key: "new", label: "New", color: "bg-gray-100 border-t-gray-400" },
  { key: "qualifying", label: "Qualifying", color: "bg-amber-50 border-t-amber-400" },
  { key: "qualified", label: "Qualified", color: "bg-emerald-50 border-t-emerald-400" },
  { key: "appointment_set", label: "Appt. Set", color: "bg-amber-50 border-t-violet-400" },
  { key: "contacted", label: "Contacted", color: "bg-blue-50 border-t-blue-400" },
  { key: "closed_won", label: "Closed Won", color: "bg-emerald-100 border-t-emerald-500" },
  { key: "closed_lost", label: "Closed Lost", color: "bg-red-50 border-t-red-400" },
];

function formatCurrency(n: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

function LeadCard({ lead, onClick }: { lead: Lead; onClick: () => void }) {
  const scoreColor = lead.score >= 70 ? "bg-emerald-100 text-emerald-800" : lead.score >= 50 ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800";

  return (
    <Card
      className="cursor-pointer transition-all hover:shadow-md hover:border-brand-200"
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100">
                <User className="h-4 w-4 text-brand-600" />
              </div>
              <p className="text-sm font-semibold text-gray-900 truncate">{lead.name}</p>
            </div>
            <div className="mt-3 space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <DollarSign className="h-3 w-3" />
                <span>{formatCurrency(lead.budget)}</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <ArrowUpRight className="h-3 w-3" />
                <span>{lead.source}</span>
              </div>
            </div>
          </div>
          <div className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-bold", scoreColor)}>
            {lead.score}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    getLeads()
      .then(setLeads)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleLeadClick = (id: string) => {
    setSelectedLeadId(id);
    setDialogOpen(true);
  };

  const groupedLeads = columns.reduce<Record<string, Lead[]>>((acc, col) => {
    acc[col.key] = leads.filter((l) => l.status === col.key);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Leads Pipeline</h1>
        <p className="mt-1 text-sm text-gray-500">Drag and drop or click to manage your leads</p>
      </div>

      {loading ? (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {columns.map((col) => (
            <div key={col.key} className="min-w-[280px] flex-shrink-0 space-y-3">
              <Skeleton className="h-8 w-24" />
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-28 w-full" />)}
            </div>
          ))}
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {columns.map((col) => {
            const columnLeads = groupedLeads[col.key] || [];
            return (
              <div key={col.key} className={cn("min-w-[280px] flex-shrink-0 rounded-xl border-t-4 border bg-white shadow-sm", col.color)}>
                <div className="flex items-center justify-between px-4 py-3">
                  <h3 className="text-sm font-semibold text-gray-700">{col.label}</h3>
                  <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-gray-200 px-1.5 text-xs font-medium text-gray-600">
                    {columnLeads.length}
                  </span>
                </div>
                <div className="space-y-3 px-3 pb-3 max-h-[calc(100vh-280px)] overflow-y-auto">
                  {columnLeads.map((lead) => (
                    <LeadCard key={lead.id} lead={lead} onClick={() => handleLeadClick(lead.id)} />
                  ))}
                  {columnLeads.length === 0 && (
                    <p className="py-6 text-center text-xs text-gray-400">No leads</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedLeadId && (
        <LeadDetailDialog
          leadId={selectedLeadId}
          open={dialogOpen}
          onOpenChange={setDialogOpen}
        />
      )}
    </div>
  );
}
