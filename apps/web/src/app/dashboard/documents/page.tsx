"use client";

import { useEffect, useState } from "react";
import { getDocuments, type Document } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { FileText, FileSpreadsheet, FileImage, File, Upload, Sparkles, Download, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

const categoryColors: Record<string, string> = {
  contract: "bg-blue-100 text-blue-800",
  disclosure: "bg-amber-100 text-amber-800",
  report: "bg-emerald-100 text-emerald-800",
  marketing: "bg-amber-100 text-violet-800",
  financial: "bg-rose-100 text-rose-800",
  legal: "bg-gray-100 text-gray-800",
};

const fileIcons: Record<string, React.ElementType> = {
  pdf: FileText,
  doc: FileText,
  docx: FileText,
  xls: FileSpreadsheet,
  xlsx: FileSpreadsheet,
  jpg: FileImage,
  jpeg: FileImage,
  png: FileImage,
  default: File,
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function DocumentRow({ doc }: { doc: Document }) {
  const Icon = fileIcons[doc.file_type] || fileIcons.default;
  const colorClass = categoryColors[doc.category] || "bg-gray-100 text-gray-800";

  return (
    <div className="flex items-center gap-4 rounded-lg border border-gray-100 p-4 transition-colors hover:bg-gray-50">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100">
        <Icon className="h-5 w-5 text-gray-600" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-900 truncate">{doc.name}</p>
        <div className="mt-1 flex items-center gap-3 text-xs text-gray-400">
          <span>{formatFileSize(doc.file_size)}</span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {new Date(doc.uploaded_at).toLocaleDateString()}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="secondary" className={cn(colorClass)}>
          {doc.category}
        </Badge>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm">
          <Sparkles className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Download className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDocuments()
      .then(setDocs)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Document Vault</h1>
          <p className="mt-1 text-sm text-gray-500">AI-powered document management</p>
        </div>
        <Button>
          <Upload className="h-4 w-4" /> Upload Document
        </Button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-4 rounded-lg border border-gray-100 p-4">
              <Skeleton className="h-10 w-10 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-32" />
              </div>
              <Skeleton className="h-6 w-20 rounded-full" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16 text-red-400">
          <FileText className="h-12 w-12" />
          <p className="mt-4 text-sm">{error}</p>
        </div>
      ) : docs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400">
          <FileText className="h-12 w-12" />
          <p className="mt-4 text-sm">No documents uploaded yet</p>
          <Button variant="outline" size="sm" className="mt-4">
            <Upload className="h-4 w-4" /> Upload your first document
          </Button>
        </div>
      ) : (
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm divide-y divide-gray-100">
          {docs.map((doc) => (
            <DocumentRow key={doc.id} doc={doc} />
          ))}
        </div>
      )}
    </div>
  );
}
