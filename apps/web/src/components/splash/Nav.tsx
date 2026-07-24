"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";

const DARK_SECTION_IDS = ["compliance", "demo"];

export function Nav() {
  const [open, setOpen] = useState(false);
  const [isOverDark, setIsOverDark] = useState(false);
  const reduce = useReducedMotion();

  useEffect(() => {
    const sentinelEls: Element[] = [];
    for (const id of DARK_SECTION_IDS) {
      const el = document.getElementById(id);
      if (el) sentinelEls.push(el);
    }
    if (sentinelEls.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        let overDark = false;
        for (const entry of entries) {
          if (entry.isIntersecting) {
            overDark = true;
            break;
          }
        }
        setIsOverDark(overDark);
      },
      {
        rootMargin: "-64px 0px 0px 0px", // nav height = 64px
        threshold: 0,
      }
    );

    for (const el of sentinelEls) observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <motion.nav
      initial={reduce ? {} : { y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-colors ${
        isOverDark
          ? "bg-gray-900/60 backdrop-blur-sm"
          : "bg-white/80 backdrop-blur-sm"
      }`}
    >
      <div className="mx-auto max-w-[1400px] px-6">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 shadow-sm transition-transform group-hover:scale-105">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
              </svg>
            </div>
            <span className={`text-lg font-semibold tracking-tight transition-colors ${
              isOverDark ? "text-white" : "text-brand-600"
            }`}>
              RealtyAI
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className={`text-sm transition-colors ${
              isOverDark ? "text-amber-200/80 hover:text-white" : "text-gray-500 hover:text-gray-900"
            }`}>
              Features
            </Link>
            <Link href="#demo" className={`text-sm transition-colors ${
              isOverDark ? "text-amber-200/80 hover:text-white" : "text-gray-500 hover:text-gray-900"
            }`}>
              Demo Access
            </Link>
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className={`text-sm font-medium transition-colors px-4 py-2 ${
                  isOverDark ? "text-amber-200/80 hover:text-white" : "text-gray-700 hover:text-gray-900"
                }`}
              >
                Log in
              </Link>
              <Link
                href="/signup"
                className="inline-flex items-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-brand-700 hover:shadow-md active:scale-[0.98]"
              >
                Sign up free
              </Link>
            </div>
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setOpen(!open)}
            className={`md:hidden p-2 transition-colors ${
              isOverDark ? "text-amber-200/80" : "text-gray-600"
            }`}
            aria-label="Toggle menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              {open ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <motion.div
          initial={reduce ? {} : { opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className={`md:hidden border-t transition-colors ${
            isOverDark
              ? "border-white/10 bg-gray-900/95 backdrop-blur-sm"
              : "border-gray-100 bg-white/95 backdrop-blur-sm"
          }`}
        >
          <div className="px-6 py-4 space-y-4">
            <Link href="#features" onClick={() => setOpen(false)} className={`block text-sm transition-colors ${
              isOverDark ? "text-amber-200/80" : "text-gray-600"
            }`}>
              Features
            </Link>
            <Link href="#demo" onClick={() => setOpen(false)} className={`block text-sm transition-colors ${
              isOverDark ? "text-amber-200/80" : "text-gray-600"
            }`}>
              Demo Access
            </Link>
            <div className={`pt-2 border-t flex flex-col gap-3 ${
              isOverDark ? "border-white/10" : "border-gray-100"
            }`}>
              <Link
                href="/login"
                onClick={() => setOpen(false)}
                className={`text-sm font-medium transition-colors ${
                  isOverDark ? "text-amber-200/80" : "text-gray-700"
                }`}
              >
                Log in
              </Link>
              <Link
                href="/signup"
                onClick={() => setOpen(false)}
                className="inline-flex items-center justify-center rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white"
              >
                Sign up free
              </Link>
            </div>
          </div>
        </motion.div>
      )}
    </motion.nav>
  );
}