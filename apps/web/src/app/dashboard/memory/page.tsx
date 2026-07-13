"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Brain, Search, Trash2, Loader2, Database, Zap, RefreshCw, AlertCircle, BookOpen } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Memory {
  id: string;
  text: string;
  metadata?: Record<string, any>;
  created_at?: string;
  importance?: number;
  categories?: string[];
}

export default function MemoryDashboard() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [mem0Enabled, setMem0Enabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Search
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Memory[] | null>(null);
  const [searching, setSearching] = useState(false);

  // Delete state
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchMemories = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [listRes, countRes] = await Promise.all([
        fetch(`${API_BASE}/athena/memories?limit=50`),
        fetch(`${API_BASE}/athena/memories/count`),
      ]);
      if (!listRes.ok) throw new Error(`Failed to load memories: ${listRes.status}`);
      if (!countRes.ok) throw new Error(`Failed to load count: ${countRes.status}`);

      const listData = await listRes.json();
      const countData = await countRes.json();

      setMemories(listData.memories || []);
      setTotalCount(countData.count || 0);
      setMem0Enabled(countData.enabled || false);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchMemories(); }, [fetchMemories]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const res = await fetch(`${API_BASE}/athena/memories/search?query=${encodeURIComponent(searchQuery)}&limit=20`);
      if (!res.ok) throw new Error(`Search failed: ${res.status}`);
      const data = await res.json();
      setSearchResults(data.memories || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSearching(false);
    }
  };

  const handleDelete = async (memoryId: string) => {
    if (!confirm("Delete this memory?")) return;
    setDeletingId(memoryId);
    try {
      const res = await fetch(`${API_BASE}/athena/memories/${memoryId}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
      setMemories((prev) => prev.filter((m) => m.id !== memoryId));
      setTotalCount((prev) => Math.max(0, prev - 1));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setDeletingId(null);
    }
  };

  const displayMemories = searchResults !== null ? searchResults : memories;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Memory</h1>
          <p className="mt-1 text-sm text-gray-500">Everything Athena knows about you — facts, preferences, people, deals</p>
        </div>
        <div className="flex items-center gap-3">
          {mem0Enabled && (
            <Badge variant="success" className="gap-1">
              <Zap className="h-3 w-3" /> Mem0 Active
            </Badge>
          )}
          <Button variant="outline" size="sm" onClick={fetchMemories} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Database className="h-8 w-8 text-brand-500" />
              <div>
                <p className="text-2xl font-bold">{loading ? "..." : totalCount}</p>
                <p className="text-xs text-gray-500">Total Memories</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Brain className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{memories.length}</p>
                <p className="text-xs text-gray-500">Loaded</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <BookOpen className="h-8 w-8 text-purple-500" />
              <div>
                <p className={`text-2xl font-bold ${mem0Enabled ? "text-green-600" : "text-gray-400"}`}>
                  {mem0Enabled ? "Active" : "Off"}
                </p>
                <p className="text-xs text-gray-500">Automatic Extraction</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <input
                placeholder={'Search memories semantically - "What do I know about the Windermere listing?"'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
            </div>
            <Button onClick={handleSearch} disabled={searching || !searchQuery.trim()}>
              {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Search
            </Button>
            {searchResults !== null && (
              <Button variant="outline" onClick={() => { setSearchResults(null); setSearchQuery(""); }}>
                Clear
              </Button>
            )}
          </div>
          {searchResults !== null && (
            <p className="mt-2 text-xs text-gray-400">
              {searchResults.length === 0
                ? "No matching memories found."
                : `Found ${searchResults.length} semantically matching memories.`}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Memory list */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-brand-500" />
        </div>
      ) : !mem0Enabled ? (
        <Card>
          <CardContent className="py-8 text-center text-gray-500">
            <Database className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p className="font-medium">Mem0 Not Available</p>
            <p className="text-sm mt-1">Set the <code className="bg-gray-100 px-1 rounded">OPENAI_API_KEY</code> environment variable to enable automatic memory extraction.</p>
          </CardContent>
        </Card>
      ) : displayMemories.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-gray-500">
            <Brain className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p className="font-medium">No memories yet</p>
            <p className="text-sm mt-1">Memories are automatically created as you chat with Athena. She learns from every conversation.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {displayMemories.map((mem) => (
            <Card key={mem.id} className="group hover:shadow-md transition-shadow">
              <CardContent className="py-3 px-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 leading-relaxed">{mem.text}</p>
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                      {mem.categories && mem.categories.slice(0, 3).map((cat) => (
                        <Badge key={cat} variant="secondary" className="text-[10px] px-1.5 py-0">
                          {cat}
                        </Badge>
                      ))}
                      {mem.importance !== undefined && mem.importance !== null && (
                        <span className="text-[10px] text-gray-400">
                          importance: {typeof mem.importance === 'number' ? mem.importance.toFixed(2) : mem.importance}
                        </span>
                      )}
                      {mem.created_at && (
                        <span className="text-[10px] text-gray-400">
                          {new Date(mem.created_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 hover:bg-red-50 shrink-0"
                    onClick={() => handleDelete(mem.id)}
                    disabled={deletingId === mem.id}
                  >
                    {deletingId === mem.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
