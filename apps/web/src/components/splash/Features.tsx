"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import {
  Sparkles,
  MessageSquareText,
  Brain,
  Scale,
  TrendingUp,
  Clock,
  Gavel,
  MapPin,
} from "lucide-react";

const features = [
  {
    icon: MessageSquareText,
    title: "Natural conversation",
    description: "Chat with Athena like you would a colleague. She understands real estate — contracts, compliance, commissions — and speaks your language.",
  },
  {
    icon: Brain,
    title: "Remembers everything",
    description: "Every client detail, every deal nuance, every preference. Athena builds a living memory of your business across every conversation.",
  },
  {
    icon: TrendingUp,
    title: "Lead intelligence",
    description: "Hot leads surface automatically. Athena scores, prioritises, and suggests the perfect next touchpoint — before you even ask.",
  },
  {
    icon: Clock,
    title: "Proactive alerts",
    description: "Expiring listings, deadline reminders, market changes. Athena initiates — she doesn't wait for you to ask.",
  },
  {
    icon: Scale,
    title: "Canada & US legal compliance",
    description: "Athena knows OREA, RESPA, TREC, provincial real estate acts, and standard contract clauses across Canada and the United States. She extracts key terms, risks, and deadlines from any contract — and flags non-standard language before it becomes a problem.",
  },
  {
    icon: Sparkles,
    title: "16+ built-in tools",
    description: "Leads, listings, documents, campaigns, showings, market reports. Athena controls your entire platform through conversation.",
  },
];

export function Features() {
  const reduce = useReducedMotion();

  return (
    <section id="features" className="relative py-24 md:py-32">
      <div className="absolute inset-0 bg-amber-50/30 pointer-events-none" />

      <div className="relative mx-auto max-w-[1400px] px-6">
        {/* Section header */}
        <motion.div
          initial={reduce ? {} : { opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="text-[clamp(1.75rem,3.5vw,2.75rem)] font-bold tracking-tight text-gray-900 leading-[1.1]">
            Everything a real estate agent needs.
            <br />
            <span className="text-brand-600">One conversation.</span>
          </h2>
          <p className="mt-4 text-base md:text-lg leading-relaxed text-gray-500">
            Athena replaces five separate tools with a single AI secretary who knows your business, your clients, and your market.
          </p>
        </motion.div>

        {/* Feature grid */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => {
            const isCompliance = feature.title.toLowerCase().includes("compliance");
            return (
              <motion.div
                key={feature.title}
                initial={reduce ? {} : { opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.5, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
                className={`group rounded-2xl border p-6 md:p-8 transition-all hover:shadow-lg ${
                  isCompliance
                    ? "border-brand-200 bg-brand-50/60 hover:border-brand-300 hover:shadow-brand-100/30"
                    : "border-gray-100 bg-white hover:border-brand-100 hover:shadow-brand-100/20"
                }`}
              >
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg mb-4 transition-colors ${
                  isCompliance
                    ? "bg-brand-200 text-brand-700 group-hover:bg-brand-300"
                    : "bg-brand-50 text-brand-600 group-hover:bg-brand-100"
                }`}>
                  <feature.icon className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-gray-900">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">{feature.description}</p>
              </motion.div>
            );
          })}
        </div>

        {/* Legal Compliance Trust Banner */}
        <motion.div
          initial={reduce ? {} : { opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-16 rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-50 via-white to-brand-50 p-8 md:p-10"
        >
          <div className="flex flex-col lg:flex-row items-start lg:items-center gap-6">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-brand-100">
              <Gavel className="h-7 w-7 text-brand-600" />
            </div>
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-lg font-bold text-gray-900">
                  Built for regulatory compliance
                </h3>
                <span className="inline-flex items-center gap-1 rounded-full border border-brand-200 bg-white px-2.5 py-0.5 text-[11px] font-medium text-brand-700">
                  <MapPin className="h-3 w-3" /> Canada & US
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-gray-600 max-w-[70ch]">
                Athena is trained on OREA forms, RESPA guidelines, TREC rules, and provincial real estate acts across Canada and the United States. 
                She helps you identify non-standard clauses, track regulatory deadlines, and maintain compliance documentation. 
                <strong className="text-gray-800"> Always consult a qualified lawyer for legal decisions</strong> — Athena is your assistant, not your attorney.
              </p>
              <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  OREA forms (Ontario)
                </span>
                <span className="flex items-center gap-1">
                  <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  RESPA guidelines (US)
                </span>
                <span className="flex items-center gap-1">
                  <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  TREC rules (Texas)
                </span>
                <span className="flex items-center gap-1">
                  <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Provincial acts (all Canada)
                </span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Bottom CTA */}
        <motion.div
          initial={reduce ? {} : { opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-12 text-center"
        >
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-brand-700 hover:shadow-md active:scale-[0.98]"
          >
            Get started free
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}