"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { AnimatedAthenaSVG } from "./AnimatedAthenaSVG";

export function Hero() {
  const reduce = useReducedMotion();

  return (
    <section className="relative min-h-[100dvh] flex items-center overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-amber-50/60 via-white to-white pointer-events-none" />

      {/* Decorative top-right glow */}
      <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full bg-brand-200/20 blur-[120px] pointer-events-none" />
      <div className="absolute -bottom-40 -left-40 w-[400px] h-[400px] rounded-full bg-brand-100/30 blur-[100px] pointer-events-none" />

      <div className="relative mx-auto max-w-[1400px] px-6 w-full pt-24 pb-16 md:pt-28 md:pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left: copy */}
          <motion.div
            initial={reduce ? {} : { opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          >
            <motion.p
              initial={reduce ? {} : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="inline-flex items-center gap-1.5 rounded-full border border-brand-200 bg-brand-50 px-3.5 py-1 text-xs font-medium text-brand-700 tracking-wide"
            >
              <span className="flex h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse" />
              Limited demo access now open
            </motion.p>

            <motion.h1
              initial={reduce ? {} : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mt-6 text-[clamp(2.5rem,5vw,4rem)] font-bold tracking-tighter leading-[1.05] text-gray-900"
            >
              Your business runs on{" "}
              <span className="text-brand-600">intelligence</span>
              , not spreadsheets.
            </motion.h1>

            <motion.p
              initial={reduce ? {} : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-5 text-lg leading-relaxed text-gray-600 max-w-[50ch]"
            >
              Athena is your AI operating system for real estate — managing leads, listings, documents, and compliance through natural conversation. Stop juggling tools. Start closing deals.
            </motion.p>

            <motion.div
              initial={reduce ? {} : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="mt-8 flex flex-col sm:flex-row items-start sm:items-center gap-4"
            >
              <Link
                href="/signup"
                className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3.5 text-base font-semibold text-white shadow-md transition-all hover:bg-brand-700 hover:shadow-lg active:scale-[0.98]"
              >
                Get demo access
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                </svg>
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-6 py-3.5 text-base font-medium text-gray-700 shadow-sm transition-all hover:border-gray-300 hover:shadow-md active:scale-[0.98]"
              >
                Log in
              </Link>
            </motion.div>

            <motion.p
              initial={reduce ? {} : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.7 }}
              className="mt-4 text-xs text-gray-400"
            >
              No credit card required · Free tier available · For select agents
            </motion.p>
          </motion.div>

          {/* Right: animated SVG */}
          <motion.div
            initial={reduce ? {} : { opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="flex items-center justify-center"
          >
            <div className="relative w-full max-w-[500px] mx-auto">
              <AnimatedAthenaSVG />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}