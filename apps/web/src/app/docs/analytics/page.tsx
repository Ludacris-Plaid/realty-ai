"use client";

import { BarChart, TrendingUp, TrendingDown, Activity, Download, Bot, Users, DollarSign, Clock, PieChart, LineChart } from "lucide-react";

export default function AnalyticsDocs() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics & Reports</h1>
        <p className="mt-2 text-lg text-gray-500">
          Business performance dashboards, pipeline analysis, AI agent activity logs, and exportable reports to keep your finger on the pulse.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Activity className="h-5 w-5 text-brand-500" />
          Dashboard Overview
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            The analytics dashboard displays a snapshot of your business metrics for the selected period — defaulting to the current month with comparison to the previous period.
          </p>
          <div className="grid gap-3 sm:grid-cols-4">
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <p className="text-xs text-gray-400">Active Leads</p>
              <p className="text-xl font-bold text-gray-900">47</p>
              <p className="text-xs text-emerald-600 flex items-center gap-1"><TrendingUp className="h-3 w-3" /> +12 vs last month</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <p className="text-xs text-gray-400">Active Listings</p>
              <p className="text-xl font-bold text-gray-900">23</p>
              <p className="text-xs text-red-600 flex items-center gap-1"><TrendingDown className="h-3 w-3" /> -3 vs last month</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <p className="text-xs text-gray-400">Closed Volume</p>
              <p className="text-xl font-bold text-gray-900">$8.2M</p>
              <p className="text-xs text-emerald-600 flex items-center gap-1"><TrendingUp className="h-3 w-3" /> +18% vs last month</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <p className="text-xs text-gray-400">Commission</p>
              <p className="text-xl font-bold text-gray-900">$246K</p>
              <p className="text-xs text-emerald-600 flex items-center gap-1"><TrendingUp className="h-3 w-3" /> +14% vs last month</p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Users className="h-5 w-5 text-brand-500" />
          Lead Pipeline Analytics
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Pipeline analytics break down lead movement by stage. Each section shows lead count, total pipeline value, average days in stage, and conversion rate to the next stage.
          </p>
          <div className="space-y-2">
            {[
              { stage: "New → Qualifying", rate: "72%", avgDays: "2.3", value: "$1.2M" },
              { stage: "Qualifying → Qualified", rate: "58%", avgDays: "4.1", value: "$890K" },
              { stage: "Qualified → Contacted", rate: "81%", avgDays: "1.5", value: "$2.1M" },
              { stage: "Contacted → Appointment Set", rate: "43%", avgDays: "6.8", value: "$1.6M" },
              { stage: "Appointment Set → Closed Won", rate: "37%", avgDays: "14.2", value: "$980K" },
            ].map((row) => (
              <div key={row.stage} className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-4 py-3 text-sm">
                <span className="font-medium text-gray-700">{row.stage}</span>
                <div className="flex items-center gap-6">
                  <span className="text-gray-500"><span className="text-gray-400 text-xs">Rate: </span>{row.rate}</span>
                  <span className="text-gray-500"><span className="text-gray-400 text-xs">Avg: </span>{row.avgDays}d</span>
                  <span className="font-semibold text-gray-800">{row.value}</span>
                </div>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500">
            The pipeline view also highlights bottlenecks — stages where leads stall past the average duration — and suggests re-engagement actions.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Bot className="h-5 w-5 text-brand-500" />
          AI Agent Activity
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Each AI agent reports its activity statistics. Monitor throughput, error rates, approval ratios, and response times to understand how the system is performing.
          </p>
          <div className="grid gap-2 text-sm">
            <div className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-4 py-2.5">
              <span className="font-medium text-gray-700">LeadQualifier</span>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>342 leads scored</span>
                <span className="text-emerald-600">98.2% success</span>
                <span>0.4s avg latency</span>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-4 py-2.5">
              <span className="font-medium text-gray-700">ListingOptimizer</span>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>89 descriptions generated</span>
                <span className="text-emerald-600">99.1% success</span>
                <span>2.8s avg latency</span>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-4 py-2.5">
              <span className="font-medium text-gray-700">DocAnalyzer</span>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>156 documents processed</span>
                <span className="text-emerald-600">97.4% success</span>
                <span>4.2s avg latency</span>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-4 py-2.5">
              <span className="font-medium text-gray-700">CampaignEngine</span>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>24 campaigns created</span>
                <span className="text-amber-600">92.6% success</span>
                <span>6.1s avg latency</span>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-4 py-2.5">
              <span className="font-medium text-gray-700">SchedulerAgent</span>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>187 events scheduled</span>
                <span className="text-emerald-600">99.5% success</span>
                <span>0.6s avg latency</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <PieChart className="h-5 w-5 text-brand-500" />
          Performance Trends
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <p className="text-sm text-gray-600 leading-relaxed">
            Trend charts display key metrics plotted over time — daily, weekly, monthly, or custom range. Available trend views include lead acquisition rate, pipeline velocity, average days to close, listing-to-lead conversion rate, and monthly commission trajectory. Each chart supports interactive date-range zooming and series toggling. Hovering over a data point shows the exact value and any annotation. Trend data can be used to spot seasonal patterns, evaluate the impact of marketing campaigns, and forecast future volume.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Download className="h-5 w-5 text-brand-500" />
          Exporting Reports
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Any dashboard view or analytics page can be exported as PDF or CSV. Reports include a timestamp, date range, and branding (brokerage name and logo from settings).
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <h4 className="text-sm font-medium text-gray-800 mb-1">Standard Reports</h4>
              <ul className="text-xs text-gray-500 space-y-0.5 list-disc list-inside">
                <li>Monthly business review (dashboard summary)</li>
                <li>Pipeline health report (stage-by-stage breakdown)</li>
                <li>Agent activity report (per-agent metrics)</li>
                <li>Listing performance report (days on market, views, showings)</li>
              </ul>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <h4 className="text-sm font-medium text-gray-800 mb-1">Scheduled Reports</h4>
              <ul className="text-xs text-gray-500 space-y-0.5 list-disc list-inside">
                <li>Weekly pipeline summary (emailed every Monday 8 AM)</li>
                <li>Monthly board-ready PDF (emailed 1st of month)</li>
                <li>Custom schedules — any report, any frequency, any recipient list</li>
                <li>AI-generated narrative summary alongside chart exports</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
