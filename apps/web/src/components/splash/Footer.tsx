"use client";

import Link from "next/link";

const IM_LOGO_BG = "#030806";
const IM_GREEN = "#00ff66";

export function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-white">
      <div className="mx-auto max-w-[1400px] px-6 py-10 md:py-12">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          {/* Left: RealtyAI brand */}
          <Link href="/" className="flex items-center gap-2.5 group shrink-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 transition-transform group-hover:scale-105">
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-brand-600">RealtyAI</span>
          </Link>

          {/* Right: Indications Media */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400 hidden sm:inline">Designed &amp; powered by</span>
            <Link
              href="https://indicationsmedia.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 group"
            >
              <svg
                width={28}
                height={28}
                viewBox="0 0 100 100"
                className="transition-transform duration-300 group-hover:scale-110 shrink-0"
              >
                <rect width={100} height={100} rx={12} fill={IM_LOGO_BG} />
                <text
                  x={50}
                  y={65}
                  fontFamily="Arial, sans-serif"
                  fontSize={52}
                  fontWeight="bold"
                  fill={IM_GREEN}
                  textAnchor="middle"
                  className="select-none"
                >
                  iM
                </text>
              </svg>
              <span className="text-xs font-semibold text-gray-700 transition-colors group-hover:text-[#00ff66]">
                Indications Media
              </span>
            </Link>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-8 pt-5 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-[11px] text-gray-400">
            &copy; {new Date().getFullYear()} RealtyAI. All rights reserved.
          </p>
          <p className="text-[11px] text-gray-400">
            Web development, cybersecurity &amp; AI by{" "}
            <Link
              href="https://indicationsmedia.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-[#00ff66] transition-colors"
            >
              Indications Media
            </Link>
          </p>
        </div>
      </div>
    </footer>
  );
}