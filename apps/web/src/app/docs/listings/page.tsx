"use client";

import { Building2, Sparkles, Tag, Image, DollarSign, FileEdit, Clock, CheckCircle2, XCircle, AlertCircle } from "lucide-react";

const propertyStatuses = [
  {
    icon: FileEdit,
    label: "Draft",
    color: "bg-gray-100 text-gray-600 border-gray-200",
    desc: "Listing is being created. Not visible on any public feed. AI-generated content can be edited freely.",
  },
  {
    icon: CheckCircle2,
    label: "Active",
    color: "bg-emerald-100 text-emerald-600 border-emerald-200",
    desc: "Published to MLS and your website. Actively accepting showings and offers.",
  },
  {
    icon: Clock,
    label: "Pending",
    color: "bg-amber-100 text-amber-600 border-amber-200",
    desc: "Offer accepted, contingencies in progress. Listing is marked under contract.",
  },
  {
    icon: XCircle,
    label: "Sold",
    color: "bg-blue-100 text-blue-600 border-blue-200",
    desc: "Deal closed. Listing is archived for historical reference and market analysis.",
  },
  {
    icon: AlertCircle,
    label: "Expired",
    color: "bg-red-100 text-red-600 border-red-200",
    desc: "Listing term ended without sale. Can be renewed or archived.",
  },
];

export default function ListingsDocs() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Properties & Listings</h1>
        <p className="mt-2 text-lg text-gray-500">
          Create, manage, and publish property listings with AI-assisted MLS descriptions, image management, and pricing strategy tools.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Building2 className="h-5 w-5 text-brand-500" />
          Creating & Managing Listings
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Listings are the core entity in RealtyAI. Each listing stores property details, media, pricing history, documents, and associated lead activity. Create a listing by filling out the property form or by importing from an MLS feed.
          </p>
          <p className="text-sm text-gray-600 leading-relaxed">
            Once created, the ListingOptimizer agent immediately generates a draft MLS description, extracts feature tags from the property data, and suggests comparable market prices. Every listing has a timeline showing status changes, price adjustments, and showing activity.
          </p>
          <div className="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Fields</h4>
            <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
              <li>Address, parcel ID, and geolocation coordinates</li>
              <li>Property type, bedrooms, bathrooms, square footage, lot size</li>
              <li>Year built, HOA fees, tax assessment, zoning classification</li>
              <li>Listing agent, co-brokerage, office ID, MLS number</li>
              <li>Custom fields for luxury features, green certifications, or commercial specs</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Sparkles className="h-5 w-5 text-brand-500" />
          MLS Description Generation
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            The ListingOptimizer agent generates MLS descriptions by synthesizing property data, location highlights, nearby amenities, and market trends. Descriptions are tailored to the property type — a downtown condo gets different language than a suburban family home.
          </p>
          <div className="rounded-lg bg-brand-50 border border-brand-100 p-4">
            <h4 className="text-sm font-semibold text-brand-700 mb-1">Generation Pipeline</h4>
            <ol className="text-sm text-brand-700 space-y-1 list-decimal list-inside">
              <li>Extract structured data from property record</li>
              <li>Fetch neighborhood context: schools, transit, walk score, recent sales</li>
              <li>Identify architectural style and standout features</li>
              <li>Generate 3 description variants (standard, luxury, investor-focused)</li>
              <li>Apply market-specific compliance rules (varies by MLS board)</li>
              <li>Present variants for agent review and selection</li>
            </ol>
          </div>
          <p className="text-sm text-gray-500">
            Descriptions enter draft status and are editable before publication. The AI preserves any manual edits you make and incorporates them into future revisions.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Tag className="h-5 w-5 text-brand-500" />
          Property Statuses
        </h2>
        <p className="text-sm text-gray-600 leading-relaxed">Listings move through statuses that control visibility, showing availability, and analytics inclusion.</p>
        <div className="space-y-2">
          {propertyStatuses.map((s) => (
            <div key={s.label} className="flex items-start gap-3 rounded-xl border border-gray-200 bg-white p-4">
              <div className={`shrink-0 rounded-lg p-2 ${s.color}`}>
                <s.icon className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-800">{s.label}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Image className="h-5 w-5 text-brand-500" />
          Feature Tagging & Images
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            The AI auto-tags property features from photos, floor plans, and description text. Tags are organized into categories: interior finishes, exterior features, appliances, smart home tech, community amenities, and nearby points of interest.
          </p>
          <p className="text-sm text-gray-600 leading-relaxed">
            Images support drag-and-drop reordering, auto-orientation, and AI-powered enhancement suggestions. The system generates thumbnail variants for different platforms — MLS, social media, email campaigns — and automatically compresses images to meet MLS file size limits while preserving quality.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <DollarSign className="h-5 w-5 text-brand-500" />
          Pricing Strategies
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            The pricing module provides CMA-based (Comparative Market Analysis) price recommendations. The AI analyzes active listings, pending sales, and sold comparables within a configurable radius — default 1 mile for urban, 3 miles for suburban, 10 miles for rural.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { label: "CMA Range", value: "$425K – $475K", note: "Based on 12 comparable sales in last 90 days" },
              { label: "Suggested Price", value: "$449,900", note: "AI-optimized for days-on-market vs. price balance" },
              { label: "Price per Sq Ft", value: "$312", note: "Per finished square foot vs. market avg of $298" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg border border-gray-100 bg-gray-50 p-4 text-center">
                <p className="text-xs text-gray-400">{stat.label}</p>
                <p className="text-lg font-bold text-gray-900 mt-0.5">{stat.value}</p>
                <p className="text-xs text-gray-500 mt-1">{stat.note}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500">
            Price changes are logged with a reason code (market adjustment, offer feedback, expired listing renewal). The AI can also suggest price reduction strategies based on days-on-market and showing frequency trends.
          </p>
        </div>
      </section>
    </div>
  );
}
