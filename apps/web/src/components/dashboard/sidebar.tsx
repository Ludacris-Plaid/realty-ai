"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import {
  LayoutDashboard, Users, Building2, FileText, Calendar, Mail,
  Megaphone, Bot, BarChart3, Settings, ChevronLeft, Brain,
  Sparkles, Database, LogOut, MoreHorizontal,
} from "lucide-react";
import { useState, useEffect } from "react";

const primaryItems = [
  { label: "Athena", href: "/dashboard/athena", icon: Brain, highlight: true },
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Leads", href: "/dashboard/leads", icon: Users },
  { label: "Listings", href: "/dashboard/listings", icon: Building2 },
  { label: "Calendar", href: "/dashboard/calendar", icon: Calendar },
  { label: "Messages", href: "/dashboard/messages", icon: Mail },
  { label: "Documents", href: "/dashboard/documents", icon: FileText },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
];

const moreItems = [
  { label: "Capabilities", href: "/dashboard/ai-agents", icon: Bot },
  { label: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
  { label: "Marketing", href: "/dashboard/marketing", icon: Megaphone },
  { label: "Memory", href: "/dashboard/memory", icon: Database },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [user, setUser] = useState<{ name?: string; email?: string } | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("athena_user");
      if (raw) setUser(JSON.parse(raw));
    } catch { /* ignore */ }
  }, []);

  function handleLogout() {
    localStorage.removeItem("athena_token");
    localStorage.removeItem("athena_user");
    router.push("/");
  }

  const sidebarContent = (
    <div className={cn(
      "flex h-full flex-col text-white transition-all duration-300",
      collapsed ? "w-16" : "w-64",
      "bg-gradient-to-b from-gray-950 via-gray-950 to-gray-900"
    )}>
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4">
        {!collapsed ? (
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.3)]">
              <Brain className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">RealtyAI</span>
          </div>
        ) : (
          <div className="flex w-full justify-center">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.3)]">
              <Brain className="h-5 w-5 text-white" />
            </div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden lg:flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      <Separator className="bg-gray-800" />

      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        {primaryItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          const isAthena = item.highlight;
          const linkClasses = cn(
            "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
            collapsed && "justify-center px-2",
            isActive && isAthena && "bg-amber-600 text-white shadow-[0_0_16px_rgba(245,158,11,0.25)]",
            isActive && !isAthena && "bg-gray-800 text-white",
            !isActive && isAthena && "text-amber-300/70 hover:bg-amber-600/10 hover:text-amber-200",
            !isActive && !isAthena && "text-gray-400 hover:bg-gray-800 hover:text-white",
          );
          return (
            <Link key={item.href} href={item.href} className={linkClasses}>
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && (
                <span className="flex items-center gap-2">
                  {item.label}
                  {isAthena && !isActive && <Sparkles className="h-3 w-3 text-amber-400/50" />}
                </span>
              )}
            </Link>
          );
        })}

        <button
          onClick={() => setMoreOpen(!moreOpen)}
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 w-full",
            collapsed && "justify-center px-2",
            moreOpen ? "text-white bg-gray-800" : "text-gray-500 hover:bg-gray-800 hover:text-gray-300",
          )}
        >
          <MoreHorizontal className="h-5 w-5 shrink-0" />
          {!collapsed && <span>More ({moreItems.length})</span>}
        </button>

        {moreOpen && (
          <div className="space-y-1 pl-3 border-l border-gray-800 ml-2">
            {moreItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                    collapsed && "justify-center px-2",
                    isActive ? "bg-gray-800 text-white" : "text-gray-400 hover:bg-gray-800 hover:text-white",
                  )}
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </div>
        )}

        {/* Logout */}
        <button
          onClick={handleLogout}
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 w-full",
            collapsed && "justify-center px-2",
            "text-gray-500 hover:text-red-400 hover:bg-gray-800",
          )}
        >
          <LogOut className="h-5 w-5 shrink-0" />
          {!collapsed && <span>Log out</span>}
        </button>
      </nav>

      <Separator className="bg-gray-800" />

      {/* User profile — logout moved to nav */}
      <div className={cn("p-4 space-y-2", collapsed && "flex flex-col items-center")}>
        <div className={cn("flex items-center gap-3", collapsed && "flex-col")}>
          <Avatar
            alt={user?.name || "Agent"}
            fallback={(user?.name || "A").charAt(0).toUpperCase()}
            size="sm"
          />
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.name || "Agent"}</p>
              <p className="text-xs text-gray-400 truncate">{user?.email || "Agent"}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed top-4 left-4 z-50 lg:hidden flex h-10 w-10 items-center justify-center rounded-lg bg-gray-950 text-white shadow-lg"
      >
        <ChevronLeft className={cn("h-5 w-5 transition-transform", !mobileOpen && "rotate-180")} />
      </button>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setMobileOpen(false)} />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 lg:relative lg:z-0",
          "transition-transform duration-300 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
