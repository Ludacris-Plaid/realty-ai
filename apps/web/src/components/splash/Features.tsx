"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import {
  Sparkles,
  MessageSquareText,
  Brain,
  TrendingUp,
  Clock,
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
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={reduce ? {} : { opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.5, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
              className="group rounded-2xl border border-gray-100 bg-white p-6 md:p-8 transition-all hover:border-brand-100 hover:shadow-lg hover:shadow-brand-100/20"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600 mb-4 transition-colors group-hover:bg-brand-100">
                <feature.icon className="h-5 w-5" />
              </div>
              <h3 className="text-base font-semibold text-gray-900">{feature.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-500">{feature.description}</p>
            </motion.div>
          ))}
        </div>

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