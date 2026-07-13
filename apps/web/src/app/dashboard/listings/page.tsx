"use client";

import { useEffect, useState } from "react";
import { getListings, fetchFromApi, type Property } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Building2, Bed, Bath, Move, Search, Sparkles, MapPin } from "lucide-react";

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
    <Card className="overflow-hidden transition-all hover:shadow-lg">
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
        <Button variant="outline" size="sm" className="w-full" onClick={handleGenerate} disabled={generating}>
          <Sparkles className="h-3.5 w-3.5" /> {generating ? "Generating..." : "Generate MLS Description"}
        </Button>
      </CardContent>
    </Card>
  );
}

export default function ListingsPage() {
  const [listings, setListings] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    getListings()
      .then(setListings)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = listings.filter((p) =>
    p.address.toLowerCase().includes(search.toLowerCase()) ||
    p.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Property Listings</h1>
          <p className="mt-1 text-sm text-gray-500">Manage and market your properties</p>
        </div>
        <Button onClick={() => alert("Listing creation form coming soon. Use Athena to add listings by voice or chat.")}>
          <Building2 className="h-4 w-4" /> Add Listing
        </Button>
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
          <p className="mt-4 text-sm">No listings found</p>
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
