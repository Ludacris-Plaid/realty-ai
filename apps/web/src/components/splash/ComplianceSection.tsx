"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { Scale, ShieldCheck, FileText, Gavel } from "lucide-react";

const regulations = [
  {
    name: "OREA",
    full: "Ontario Real Estate Association",
    description: "Standard forms, disclosure rules, and code of ethics for Ontario agents.",
  },
  {
    name: "RESPA",
    full: "Real Estate Settlement Procedures Act",
    description: "US federal rules for settlement services, disclosures, and referral fees.",
  },
  {
    name: "TREC",
    full: "Texas Real Estate Commission",
    description: "License standards, contract forms, and continuing education requirements.",
  },
];

export function ComplianceSection() {
  const reduce = useReducedMotion();

  return (
    <section id="compliance" className="relative py-24 md:py-32 overflow-hidden">
      {/* Background — warm amber/brand gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-600 via-brand-700 to-amber-800 pointer-events-none" />

      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] rounded-full bg-amber-400/10 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-white/5 blur-[80px] pointer-events-none" />

      {/* Subtle grid */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, white 1px, transparent 0)`,
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative mx-auto max-w-[1400px] px-6">
        <div className="mx-auto max-w-5xl">
          {/* Header */}
          <motion.div
            initial={reduce ? {} : { opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="text-center"
          >
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/20 bg-amber-400/10 px-3.5 py-1 text-xs font-medium text-amber-200 tracking-wide backdrop-blur-sm">
              <Scale className="h-3 w-3" />
              Cross-border compliance
            </span>

            <h2 className="mt-6 text-[clamp(1.75rem,3.5vw,2.75rem)] font-bold tracking-tight text-white leading-[1.1]">
              Built for Canada &amp; US
              <br />
              <span className="text-amber-200">regulatory compliance</span>
            </h2>

            <p className="mt-4 text-base md:text-lg leading-relaxed text-amber-100/80 max-w-[65ch] mx-auto">
              Athena is purpose-built for the regulatory landscape on both sides of the border. She understands
              provincial real estate acts, OREA forms, RESPA guidelines, TREC rules — and flags risks before they
              become problems.
            </p>
          </motion.div>

          {/* Regulation badges */}
          <motion.div
            initial={reduce ? {} : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4"
          >
            {regulations.map((reg) => (
              <div
                key={reg.name}
                className="rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm transition-all hover:bg-white/10"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-400/15">
                    <span className="text-xs font-bold text-amber-200">{reg.name}</span>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{reg.name}</p>
                    <p className="text-[11px] text-amber-100/60">{reg.full}</p>
                  </div>
                </div>
                <p className="mt-3 text-xs text-amber-100/70 leading-relaxed">
                  {reg.description}
                </p>
              </div>
            ))}
          </motion.div>

          {/* Feature highlights + disclaimer */}
          <motion.div
            initial={reduce ? {} : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-10 rounded-xl border border-white/10 bg-white/[0.04] p-6 md:p-8 backdrop-blur-sm"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  icon: FileText,
                  label: "Contract analysis",
                  desc: "Extracts key terms, deadlines, and non-standard clauses from any real estate contract — OREA, TREC, or custom.",
                },
                {
                  icon: ShieldCheck,
                  label: "Risk flagging",
                  desc: "Identifies regulatory deadlines, disclosure gaps, and non-compliant language before it becomes a liability.",
                },
              ].map((item) => (
                <div key={item.label} className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-400/15">
                    <item.icon className="h-4 w-4 text-amber-300" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{item.label}</p>
                    <p className="mt-0.5 text-xs text-amber-100/70 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* * Disclaimer */}
          <motion.div
            initial={reduce ? {} : { opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.45 }}
            className="mt-10 text-center"
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-400/15 bg-white/[0.03] px-5 py-2 backdrop-blur-sm">
              <Gavel className="h-3.5 w-3.5 text-amber-300 shrink-0" />
              <p className="text-xs text-amber-200/80 leading-relaxed">
                <span className="font-semibold text-amber-200">*</span>{" "}
                Athena is a compliance assistant, not a replacement for professional legal advice.{" "}
                <span className="font-semibold text-amber-200">
                  Always consult a qualified lawyer for legal decisions.
                </span>
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}