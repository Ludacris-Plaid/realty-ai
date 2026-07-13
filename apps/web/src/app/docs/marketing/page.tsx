"use client";

import { Megaphone, Mail, Newspaper, Image, BarChart, Globe, Instagram, Twitter, Facebook, Users } from "lucide-react";

export default function MarketingDocs() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Marketing Tools</h1>
        <p className="mt-2 text-lg text-gray-500">
          AI-generated campaigns, social media content, email templates, and analytics — all tied to your lead pipeline and property inventory.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Megaphone className="h-5 w-5 text-brand-500" />
          AI-Generated Campaigns
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            The CampaignEngine agent creates multi-channel marketing campaigns from a single brief. You provide a property, a target audience segment, and a goal — the agent generates copy, visuals, schedule, and distribution plan.
          </p>
          <div className="rounded-lg bg-brand-50 border border-brand-100 p-4">
            <h4 className="text-sm font-semibold text-brand-700 mb-2">Campaign Types</h4>
            <ul className="text-sm text-brand-700 space-y-1 list-disc list-inside">
              <li><strong>Listing Launch</strong> — Multi-channel push for a new listing: email to nearby leads, Instagram carousel, Facebook ad, print flyer</li>
              <li><strong>Open House Promotion</strong> — Targeted invitations to leads matching the property profile, social media event page, SMS blasts to saved searches</li>
              <li><strong>Market Report</strong> — Monthly or quarterly neighborhood market updates sent as email newsletters with embedded charts and recent sales</li>
              <li><strong>Just Sold</strong> — Announcement campaign to generate social proof and re-engage past leads</li>
              <li><strong>Sphere of Influence</strong> — Personal outreach series to agent&rsquo;s network with check-in messaging and market insights</li>
            </ul>
          </div>
          <p className="text-sm text-gray-500">
            Campaigns with more than 50 recipients enter a review queue before sending. The AI estimates open rate, click rate, and conversion probability before launch.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Globe className="h-5 w-5 text-brand-500" />
          Social Media Content
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            The CampaignEngine generates platform-optimized social content. Each platform gets appropriate formatting, character limits, hashtag strategy, and image sizing.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1.5">
                <Instagram className="h-4 w-4 text-pink-500" />
                <h3 className="text-sm font-medium text-gray-800">Instagram</h3>
              </div>
              <p className="text-xs text-gray-500">Carousel posts with listing photos, story highlights for open houses, reel scripts for property tours. Hashtag sets auto-generated per market.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1.5">
                <Facebook className="h-4 w-4 text-blue-600" />
                <h3 className="text-sm font-medium text-gray-800">Facebook</h3>
              </div>
              <p className="text-xs text-gray-500">Feed posts with property cards, event pages for open houses, boosted post recommendations. Audience targeting based on lead segments.</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <div className="flex items-center gap-2 mb-1.5">
                <Twitter className="h-4 w-4 text-sky-500" />
                <h3 className="text-sm font-medium text-gray-800">X / Twitter</h3>
              </div>
              <p className="text-xs text-gray-500">Short listing highlights, market stats, and thread-style deep dives. Automated daily market tip posts from curated templates.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Mail className="h-5 w-5 text-brand-500" />
          Email Templates & Newsletters
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            A library of pre-built email templates covers common real estate scenarios. Templates are fully customizable — edit any section, swap images, adjust the call-to-action. The AI can remix any template for a different property or audience.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { name: "New Listing Alert", to: "Prospective buyers matched to property criteria" },
              { name: "Price Reduction", to: "Leads who viewed the property or saved it" },
              { name: "Market Update", to: "Full lead database, segmented by neighborhood" },
              { name: "Just Listed / Just Sold", to: "Sphere of influence and past clients" },
              { name: "Holiday Greeting", to: "Full contact list with personalization" },
              { name: "Open House Invitation", to: "Nearby leads with matching preferences" },
            ].map((t) => (
              <div key={t.name} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                <h3 className="text-sm font-medium text-gray-800">{t.name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{t.to}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500">
            Newsletters support rich media — property image grids, embedded video walkthroughs, charts from the analytics module, and personalized lead recommendations per recipient.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Image className="h-5 w-5 text-brand-500" />
          Content Library
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <p className="text-sm text-gray-600 leading-relaxed">
            The content library stores all marketing assets: saved campaign copy, image variants, video thumbnails, and brand assets. Each item is tagged by property, campaign, and content type. The library is searchable by keyword and filterable by date range, campaign, or asset type. Assets can be reused across campaigns without re-uploading. An approval status tracks whether each asset has been reviewed and approved for publication.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <BarChart className="h-5 w-5 text-brand-500" />
          Campaign Tracking
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Every campaign has a live dashboard showing delivery, engagement, and conversion metrics. Data is updated hourly for email and social campaigns, daily for print.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 text-center">
              <p className="text-xs text-gray-400">Email Open Rate</p>
              <p className="text-xl font-bold text-gray-900">42.3%</p>
              <p className="text-xs text-gray-500">Industry avg: 21.8%</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 text-center">
              <p className="text-xs text-gray-400">Click-Through Rate</p>
              <p className="text-xl font-bold text-gray-900">8.7%</p>
              <p className="text-xs text-gray-500">Industry avg: 3.1%</p>
            </div>
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 text-center">
              <p className="text-xs text-gray-400">Lead Conversions</p>
              <p className="text-xl font-bold text-gray-900">12</p>
              <p className="text-xs text-gray-500">From 3 active campaigns</p>
            </div>
          </div>
          <p className="text-sm text-gray-500">
            Conversion tracking links individual leads back to the campaign and touchpoint that generated them. Attribution is visible on the lead detail page under &ldquo;First Touch&rdquo; and &ldquo;Last Touch.&rdquo;
          </p>
        </div>
      </section>
    </div>
  );
}
