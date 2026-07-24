"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";

export function DemoAccess() {
  const reduce = useReducedMotion();

  return (
    <section id="demo" className="relative py-24 md:py-32 overflow-hidden">
      {/* Branded background */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-600 via-brand-700 to-amber-800 pointer-events-none" />

      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] rounded-full bg-white/5 blur-[80px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-amber-400/10 blur-[60px] pointer-events-none" />

      {/* Subtle grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, white 1px, transparent 0)`,
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative mx-auto max-w-[1400px] px-6">
        <div className="mx-auto max-w-3xl text-center">
          <motion.div
            initial={reduce ? {} : { opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-3.5 py-1 text-xs font-medium text-amber-200 tracking-wide backdrop-blur-sm">
              Limited availability
            </span>

            <h2 className="mt-6 text-[clamp(1.75rem,3.5vw,2.75rem)] font-bold tracking-tight text-white leading-[1.1]">
              Demo access is open —
              <br />
              <span className="text-amber-200">for a limited time only.</span>
            </h2>

            <p className="mt-4 text-base md:text-lg leading-relaxed text-amber-100/80 max-w-[55ch] mx-auto">
              We're onboarding a select group of real estate agents to experience Athena before general release. 
              Priority access goes to agents actively listing and closing — no fluff, no sales pitch, just the tool.
            </p>
          </motion.div>

          <motion.div
            initial={reduce ? {} : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3.5 text-base font-semibold text-brand-700 shadow-md transition-all hover:bg-amber-50 hover:shadow-lg active:scale-[0.98]"
            >
              Claim your demo access
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/10 px-6 py-3.5 text-base font-medium text-white backdrop-blur-sm transition-all hover:bg-white/20 active:scale-[0.98]"
            >
              Already have access? Log in
            </Link>
          </motion.div>

          <motion.div
            initial={reduce ? {} : { opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-6 text-left"
          >
            {[
              { label: "Free tier", desc: "No credit card required. Start using Athena immediately." },
              { label: "No contracts", desc: "Use it, love it, or walk away. Month-to-month, zero lock-in." },
              { label: "Priority support", desc: "Demo users get direct access to the founding team." },
            ].map((item) => (
              <div key={item.label} className="rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
                <p className="text-sm font-semibold text-white">{item.label}</p>
                <p className="mt-1 text-xs text-amber-100/70">{item.desc}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}