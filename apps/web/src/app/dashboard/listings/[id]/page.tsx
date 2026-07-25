"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchFromApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowLeft, Bed, Bath, Move, MapPin, Calendar,
  Building2, Ruler, Car, Sparkles, DollarSign,
  Home, Hash
} from "lucide-react";

interface PropertyDetail {
  id: string;
  address_street: string;
  address_city: string;
  address_state: string;
  address_zip: string;
  list_price: number;
  beds: number;
  baths: number;
  sqft: number;
  property_type: string;
  status: string;
  description: string;
  features: string[];
  images: string[];
  year_built: number;
  garage_spaces: number;
  lot_size: number;
  mls_number: string;
  created_at: string;
}

function formatCurrency(n: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

export default function PropertyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [description, setDescription] = useState("");
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    fetchFromApi<PropertyDetail>(`/api/v1/listings/${params.id}`)
      .then(setProperty)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [params.id]);

  const handleGenerateDescription = async () => {
    setGenerating(true);
    try {
      const res = await fetchFromApi<{ description: string }>(
        `/api/v1/listings/${params.id}/generate-description`,
        { method: "POST" }
      );
      setDescription(res.description);
    } catch (e: any) {
      setDescription(`Error: ${e.message}`);
    }
    setGenerating(false);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-48 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400">
        <Building2 className="h-16 w-16" />
        <p className="mt-4 text-lg">Property not found</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push("/dashboard/listings")}>
          <ArrowLeft className="h-4 w-4" /> Back to Listings
        </Button>
      </div>
    );
  }

  const images = Array.isArray(property.images)
    ? property.images.filter(Boolean)
    : typeof property.images === "object" && property.images !== null
      ? (property.images as any).images || []
      : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => router.push("/dashboard/listings")} className="text-gray-600">
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
        <Badge variant={property.status === "ACTIVE" ? "success" : property.status === "PENDING" ? "warning" : "secondary"} className="text-sm px-3 py-1">
          {property.status}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {images.length > 0 ? (
            <>
              <div className="relative h-80 rounded-xl overflow-hidden bg-brand-50">
                <img src={images[selectedImage]} alt={property.address_street} className="h-full w-full object-cover" />
              </div>
              {images.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {images.map((img: string, i: number) => (
                    <button key={i} onClick={() => setSelectedImage(i)}
                      className={`shrink-0 h-16 w-24 rounded-lg overflow-hidden border-2 transition-all ${i === selectedImage ? "border-brand-500 opacity-100" : "border-transparent opacity-60 hover:opacity-80"}`}>
                      <img src={img} alt="" className="h-full w-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="flex h-80 items-center justify-center rounded-xl bg-gradient-to-br from-brand-100 to-brand-50">
              <Building2 className="h-20 w-20 text-brand-300" />
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div>
            <p className="text-3xl font-bold text-gray-900">{formatCurrency(property.list_price)}</p>
            <div className="mt-2 flex items-start gap-1.5 text-sm text-gray-500">
              <MapPin className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{property.address_street}, {property.address_city}, {property.address_state} {property.address_zip}</span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg bg-gray-50 p-3 text-center">
              <Bed className="mx-auto h-5 w-5 text-brand-600" />
              <p className="mt-1 text-lg font-bold text-gray-900">{property.beds}</p>
              <p className="text-xs text-gray-500">Beds</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-3 text-center">
              <Bath className="mx-auto h-5 w-5 text-brand-600" />
              <p className="mt-1 text-lg font-bold text-gray-900">{property.baths}</p>
              <p className="text-xs text-gray-500">Baths</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-3 text-center">
              <Move className="mx-auto h-5 w-5 text-brand-600" />
              <p className="mt-1 text-lg font-bold text-gray-900">{property.sqft.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Sqft</p>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-gray-600">
              <Home className="h-4 w-4" />
              <span className="font-medium">Type:</span> {property.property_type}
            </div>
            {property.year_built > 0 && (
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar className="h-4 w-4" />
                <span className="font-medium">Year Built:</span> {property.year_built}
              </div>
            )}
            {property.garage_spaces > 0 && (
              <div className="flex items-center gap-2 text-gray-600">
                <Car className="h-4 w-4" />
                <span className="font-medium">Garage:</span> {property.garage_spaces} car
              </div>
            )}
            {property.lot_size > 0 && (
              <div className="flex items-center gap-2 text-gray-600">
                <Ruler className="h-4 w-4" />
                <span className="font-medium">Lot Size:</span> {property.lot_size.toLocaleString()} sqft
              </div>
            )}
            {property.mls_number && (
              <div className="flex items-center gap-2 text-gray-600">
                <Hash className="h-4 w-4" />
                <span className="font-medium">MLS#:</span> {property.mls_number}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-gray-100 bg-white p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">About this property</h2>
          <p className="text-sm leading-relaxed text-gray-600">{property.description || "No description available."}</p>
          {property.features && property.features.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">Features</h3>
              <div className="flex flex-wrap gap-2">
                {property.features.map((f: string, i: number) => (
                  <Badge key={i} variant="secondary">{f}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-gray-100 bg-white p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">AI Description</h2>
          <p className="text-sm leading-relaxed text-gray-600 mb-4">
            {description || "Generate an AI-powered MLS listing description for this property."}
          </p>
          <Button onClick={handleGenerateDescription} disabled={generating} className="w-full">
            <Sparkles className="h-4 w-4" />
            {generating ? "Generating..." : "Generate Description"}
          </Button>
        </div>
      </div>

      <div className="flex gap-3">
        <Button onClick={() => router.push(`/dashboard/athena?msg=Schedule a showing for ${property.address_street} ${property.address_city}`)}>
          <Calendar className="h-4 w-4" /> Schedule Showing
        </Button>
        <Button variant="outline" onClick={() => router.push(`/dashboard/athena?msg=Tell me about ${property.address_street} ${property.address_city}`)}>
          Ask Athena about this property
        </Button>
      </div>
    </div>
  );
}
