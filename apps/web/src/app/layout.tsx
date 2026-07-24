import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RealtyAI — AI Operating System for Real Estate Agents",
  description:
    "Athena is your AI secretary for real estate. Manage leads, listings, documents, and compliance through natural conversation. Demo access now open.",
  openGraph: {
    title: "RealtyAI — Athena for Real Estate",
    description:
      "Your business runs on intelligence, not spreadsheets. Meet Athena.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body className="antialiased font-sans">{children}</body>
    </html>
  );
}