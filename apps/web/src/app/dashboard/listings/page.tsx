"use client";

import { useEffect, useState } from "react";
import { getListings, fetchFromApi, type Property } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Building2, Bed, Bath, Move, Search, Sparkles, MapPin, Download, Loader2, X } from "lucide-react";
import Link from "next/link";

function formatCurrency(n: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

const statusBadge: Record<string, "success" | "warning" | "default" | "secondary"> = {
  active: "success",
  pending: "warning",
  sold: "secondary",
  expired: "default",
};

function ListingCard({ property }: { property: Property }) {
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await fetchFromApi<{ description: string }>(
        `/api/v1/listings/${property.id}/generate-description`,
        { method: "POST" }
      );
      alert(`AI-generated description:\n\n${res.description?.slice(0, 500) || "Description generated!"}`);
    } catch (e: any) {
      alert(`Could not generate description: ${e.message}`);
    }
    setGenerating(false);
  };

  return (
    <Card className="overflow-hidden transition-all hover:shadow-lg group">
      <Link href={`/dashboard/listings/${property.id}`}>
        <div className="relative h-48 bg-gradient-to-br from-brand-100 to-brand-50">
          {property.image_url ? (
            <img src={property.image_url} alt={property.address} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center">
              <Building2 className="h-12 w-12 text-brand-300" />
            </div>
          )}
          <div className="absolute top-3 right-3">
            <Badge variant={statusBadge[property.status] || "default"}>
              {property.status.charAt(0).toUpperCase() + property.status.slice(1)}
            </Badge>
          </div>
        </div>
        <CardContent className="p-4 space-y-3">
          <div>
            <p className="text-lg font-bold text-gray-900">{formatCurrency(property.price)}</p>
            <div className="mt-1 flex items-start gap-1.5 text-sm text-gray-500">
              <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span className="line-clamp-1">{property.address}</span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span className="flex items-center gap-1"><Bed className="h-3.5 w-3.5" /> {property.beds} beds</span>
            <span className="flex items-center gap-1"><Bath className="h-3.5 w-3.5" /> {property.baths} baths</span>
            <span className="flex items-center gap-1"><Move className="h-3.5 w-3.5" /> {property.sqft.toLocaleString()} sqft</span>
          </div>
          <p className="line-clamp-2 text-xs text-gray-400">{property.description}</p>
          <Button variant="outline" size="sm" className="w-full" onClick={(e) => { e.preventDefault(); handleGenerate(); }} disabled={generating}>
            <Sparkles className="h-3.5 w-3.5" /> {generating ? "Generating..." : "Generate MLS Description"}
          </Button>
        </CardContent>
      </Link>
    </Card>
  );
}

function ScrapeModal({ open, onClose, onSuccess }: { open: boolean; onClose: () => void; onSuccess: () => void }) {
  const [location, setLocation] = useState("Edmonton, AB");
  const [count, setCount] = useState(10);
  const [scraping, setScraping] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  if (!open) return null;

  const handleScrape = async () => {
    setScraping(true);
    setResult(null);
    try {
      const res = await fetchFromApi<{ status: string; properties_inserted: number; scraped: number }>("/api/v1/scrape", {
        method: "POST",
        body: JSON.stringify({ location, count }),
      });
      const msg = `${res.properties_inserted} properties imported from ${location}`;
      setResult(msg);
      setTimeout(() => { onSuccess(); onClose(); }, 2000);
    } catch (e: any) {
      setResult(`Error: ${e.message}`);
    }
    setScraping(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Scrape New Listings</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="h-5 w-5" /></button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">Location</label>
            <Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Edmonton, AB" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Max results</label>
            <Input type="number" value={count} onChange={(e) => setCount(Number(e.target.value))} min={1} max={50} />
          </div>
          <Button className="w-full" onClick={handleScrape} disabled={scraping}>
            {scraping ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {scraping ? "Scraping..." : "Scrape & Import"}
          </Button>
          {result && (
            <p className={`text-sm text-center ${result.startsWith("Error") ? "text-red-500" : "text-green-600"}`}>{result}</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ListingsPage() {
  const [listings, setListings] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showScrape, setShowScrape] = useState(false);

  const loadListings = () => {
    setLoading(true);
    getListings()
      .then(setListings)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadListings(); }, []);

  const filtered = listings.filter((p) =>
    p.address.toLowerCase().includes(search.toLowerCase()) ||
    p.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <ScrapeModal open={showScrape} onClose={() => setShowScrape(false)} onSuccess={loadListings} />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Property Listings</h1>
          <p className="mt-1 text-sm text-gray-500">Manage and market your properties</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowScrape(true)}>
            <Download className="h-4 w-4" /> Scrape New Listings
          </Button>
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search listings..."
          className="pl-9"
        />
      </div>

      {loading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="overflow-hidden">
              <Skeleton className="h-48 w-full rounded-none" />
              <CardContent className="p-4 space-y-3">
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-full" />
                <div className="flex gap-4">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-20" />
                </div>
                <Skeleton className="h-8 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400">
          <Building2 className="h-12 w-12" />
          <p className="mt-4 text-sm">No listings found. Click "Scrape New Listings" to populate your dashboard.</p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((property) => (
            <ListingCard key={property.id} property={property} />
          ))}
        </div>
      )}
    </div>
  );
}
