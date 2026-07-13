"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/dashboard/sidebar";
import { AthenaFloating } from "@/components/ai/athena-floating";

/** Map pathname to context hints for the floating Athena */
function getPageContext(pathname: string): string | undefined {
  if (pathname.includes("/leads")) return "leads";
  if (pathname.includes("/listings")) return "listings";
  if (pathname.includes("/documents")) return "documents";
  if (pathname.includes("/calendar")) return "calendar";
  if (pathname.includes("/marketing")) return "marketing";
  if (pathname.includes("/analytics")) return "analytics";
  if (pathname.includes("/ai-agents")) return "agents";
  if (pathname.includes("/settings")) return "settings";
  return undefined;
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const pageContext = getPageContext(pathname);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
        {children}
      </main>
      {/* Athena floats on every page */}
      <AthenaFloating context={pageContext} />
    </div>
  );
}
