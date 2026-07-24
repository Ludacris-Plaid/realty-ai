"use client";

import { motion, useReducedMotion } from "motion/react";

export function AnimatedAthenaSVG() {
  const reduce = useReducedMotion();

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <svg
        viewBox="0 0 600 600"
        className="w-full h-full max-w-[600px]"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.35" />
            <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.1" />
            <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="ringGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#fcd34d" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.5" />
            <stop offset="50%" stopColor="#fbbf24" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#d97706" stopOpacity="0.5" />
          </linearGradient>
          <filter id="glowFilter">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="softGlow">
            <feGaussianBlur stdDeviation="8" />
          </filter>
        </defs>

        {/* Ambient glow */}
        <circle cx="300" cy="300" r="240" fill="url(#coreGlow)" />

        {/* Outer ring — animating rotation */}
        <motion.g
          animate={reduce ? {} : { rotate: 360 }}
          transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
          style={{ originX: "300px", originY: "300px" }}
        >
          <circle cx="300" cy="300" r="160" stroke="url(#ringGlow)" strokeWidth="1" strokeDasharray="4 12" />
          <circle cx="300" cy="300" r="200" stroke="url(#ringGlow)" strokeWidth="0.5" strokeDasharray="2 16" opacity="0.6" />
        </motion.g>

        {/* Inner ring — counter-rotating */}
        <motion.g
          animate={reduce ? {} : { rotate: -360 }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
          style={{ originX: "300px", originY: "300px" }}
        >
          <ellipse cx="300" cy="300" rx="120" ry="80" stroke="#fcd34d" strokeWidth="0.75" strokeOpacity="0.25" />
          <ellipse cx="300" cy="300" rx="80" ry="120" stroke="#fbbf24" strokeWidth="0.75" strokeOpacity="0.2" />
        </motion.g>

        {/* Central geometric core — Athena symbol */}
        <motion.g
          animate={reduce ? {} : { scale: [1, 1.03, 1], opacity: [0.8, 1, 0.8] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        >
          {/* Main diamond/octahedron shape */}
          <path
            d="M300 180 L380 260 L300 400 L220 260 Z"
            stroke="#f59e0b"
            strokeWidth="1.5"
            fill="rgba(245, 158, 11, 0.08)"
            filter="url(#glowFilter)"
          />
          <path
            d="M300 180 L300 400"
            stroke="#fbbf24"
            strokeWidth="1"
            strokeOpacity="0.5"
          />
          <path
            d="M220 260 L380 260"
            stroke="#fbbf24"
            strokeWidth="1"
            strokeOpacity="0.4"
          />
          <path
            d="M260 220 L340 220"
            stroke="#fcd34d"
            strokeWidth="1"
            strokeOpacity="0.3"
          />
        </motion.g>

        {/* Orbiting particles */}
        <motion.circle
          cx="300" cy="140" r="3" fill="#fbbf24"
          animate={reduce ? {} : { opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.circle
          cx="420" cy="300" r="2.5" fill="#fcd34d"
          animate={reduce ? {} : { opacity: [1, 0.3, 1] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
        />
        <motion.circle
          cx="300" cy="460" r="2" fill="#f59e0b"
          animate={reduce ? {} : { opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        />
        <motion.circle
          cx="180" cy="300" r="3.5" fill="#d97706"
          animate={reduce ? {} : { opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
        />

        {/* Geodesic connecting lines */}
        <motion.g
          animate={reduce ? {} : { opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        >
          <line x1="300" y1="180" x2="380" y2="260" stroke="#fcd34d" strokeWidth="0.5" strokeOpacity="0.4" />
          <line x1="380" y1="260" x2="300" y2="400" stroke="#fbbf24" strokeWidth="0.5" strokeOpacity="0.3" />
          <line x1="300" y1="400" x2="220" y2="260" stroke="#fcd34d" strokeWidth="0.5" strokeOpacity="0.4" />
          <line x1="220" y1="260" x2="300" y2="180" stroke="#fbbf24" strokeWidth="0.5" strokeOpacity="0.3" />
        </motion.g>

        {/* Floating micro-particles */}
        {reduce ? null : (
          <>
            <motion.circle
              cx="250" cy="200" r="1.5" fill="#fde68a"
              animate={{ y: [-8, 8, -8], opacity: [0, 0.8, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.circle
              cx="350" cy="180" r="1" fill="#fbbf24"
              animate={{ y: [6, -6, 6], opacity: [0, 0.7, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            />
            <motion.circle
              cx="200" cy="320" r="1.2" fill="#fcd34d"
              animate={{ y: [-5, 5, -5], opacity: [0, 0.6, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 2 }}
            />
            <motion.circle
              cx="400" cy="340" r="1.8" fill="#f59e0b"
              animate={{ y: [8, -8, 8], opacity: [0, 0.5, 0] }}
              transition={{ duration: 5.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
            />
            <motion.circle
              cx="330" cy="440" r="1" fill="#d97706"
              animate={{ y: [-4, 4, -4], opacity: [0, 0.7, 0] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 1.5 }}
            />
          </>
        )}
      </svg>
    </div>
  );
}