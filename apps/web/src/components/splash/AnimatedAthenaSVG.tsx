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
            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.4" />
            <stop offset="40%" stopColor="#f59e0b" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="pulseGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#fcd34d" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="dataStream" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0" />
            <stop offset="40%" stopColor="#fbbf24" stopOpacity="0.8" />
            <stop offset="60%" stopColor="#fbbf24" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="dataStream2" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0" />
            <stop offset="40%" stopColor="#fcd34d" stopOpacity="0.6" />
            <stop offset="60%" stopColor="#fcd34d" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
          </linearGradient>
          <filter id="glowFilter">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="strongGlow">
            <feGaussianBlur stdDeviation="6" />
          </filter>
        </defs>

        {/* === Ambient glow === */}
        <circle cx="300" cy="300" r="260" fill="url(#coreGlow)" />

        {/* === Expanding pulse rings (sonar/radar — represents AI processing) === */}
        {reduce ? null : (
          <>
            {[0, 1, 2, 3].map((i) => (
              <motion.circle
                key={`pulse-${i}`}
                cx="300" cy="300" r="60"
                stroke="#fcd34d"
                strokeWidth="1.5"
                strokeOpacity="0.4"
                fill="none"
                animate={{
                  r: [60, 220],
                  opacity: [0.5, 0],
                  strokeWidth: [1.5, 0.3],
                }}
                transition={{
                  duration: 3.5,
                  repeat: Infinity,
                  delay: i * 0.9,
                  ease: "easeOut",
                }}
              />
            ))}
          </>
        )}

        {/* === Outer data rings === */}
        <motion.g
          animate={reduce ? {} : { rotate: 360 }}
          transition={{ duration: 35, repeat: Infinity, ease: "linear" }}
          style={{ originX: "300px", originY: "300px" }}
        >
          <circle cx="300" cy="300" r="190" stroke="url(#dataStream)" strokeWidth="1" strokeDasharray="3 10" />
          <circle cx="300" cy="300" r="230" stroke="url(#dataStream2)" strokeWidth="0.5" strokeDasharray="1 14" opacity="0.5" />
        </motion.g>

        {/* === Inner counter-rotating ellipses (orbital paths) === */}
        <motion.g
          animate={reduce ? {} : { rotate: -360 }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
          style={{ originX: "300px", originY: "300px" }}
        >
          <ellipse cx="300" cy="300" rx="140" ry="70" stroke="#fcd34d" strokeWidth="0.6" strokeOpacity="0.15" />
          <ellipse cx="300" cy="300" rx="70" ry="140" stroke="#fbbf24" strokeWidth="0.6" strokeOpacity="0.12" />
          {/* Orbit nodes — represent leads/properties */}
          <circle cx="440" cy="300" r="2" fill="#fbbf24" opacity="0.5" />
          <circle cx="160" cy="300" r="2.5" fill="#fcd34d" opacity="0.4" />
          <circle cx="300" cy="160" r="2" fill="#f59e0b" opacity="0.5" />
          <circle cx="300" cy="440" r="2" fill="#d97706" opacity="0.4" />
        </motion.g>

        {/* === Orbiting data nodes (fast orbiters — represent data flow) === */}
        <motion.g
          animate={reduce ? {} : { rotate: 360 }}
          transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
          style={{ originX: "300px", originY: "300px" }}
        >
          <motion.circle
            cx="300" cy="80" r="3" fill="#fbbf24" filter="url(#glowFilter)"
            animate={{ r: [3, 5, 3] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.circle
            cx="300" cy="80" r="6" fill="#fbbf24" opacity="0.15"
            animate={{ r: [6, 12, 6] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          />
        </motion.g>
        <motion.g
          animate={reduce ? {} : { rotate: -360 }}
          transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
          style={{ originX: "300px", originY: "300px" }}
        >
          <motion.circle
            cx="300" cy="520" r="2.5" fill="#fcd34d" filter="url(#glowFilter)"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          />
        </motion.g>
        <motion.g
          animate={reduce ? {} : { rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
          style={{ originX: "300px", originY: "300px" }}
        >
          <circle cx="300" cy="140" r="1.8" fill="#f59e0b" opacity="0.6" />
        </motion.g>

        {/* === Data streaming arcs (pulsing dash-offset paths) === */}
        {reduce ? null : (
          <>
            <motion.path
              d="M120 300 Q300 80 480 300"
              stroke="#fbbf24"
              strokeWidth="1"
              strokeOpacity="0.15"
              fill="none"
              strokeDasharray="6 18"
              animate={{ strokeDashoffset: [0, -48] }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            />
            <motion.path
              d="M120 300 Q300 520 480 300"
              stroke="#fcd34d"
              strokeWidth="1"
              strokeOpacity="0.12"
              fill="none"
              strokeDasharray="4 16"
              animate={{ strokeDashoffset: [0, -40] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: "linear", delay: 0.5 }}
            />
            <motion.path
              d="M300 110 Q480 300 300 490"
              stroke="#f59e0b"
              strokeWidth="0.8"
              strokeOpacity="0.1"
              fill="none"
              strokeDasharray="3 20"
              animate={{ strokeDashoffset: [0, -46] }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear", delay: 1 }}
            />
          </>
        )}

        {/* === Athena core symbol — layered geometric intelligence === */}
        <motion.g
          animate={reduce ? {} : { scale: [1, 1.04, 1] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        >
          {/* Outermost diamond */}
          <path
            d="M300 150 L420 300 L300 450 L180 300 Z"
            stroke="#f59e0b"
            strokeWidth="1.2"
            fill="rgba(245, 158, 11, 0.06)"
            filter="url(#glowFilter)"
            opacity="0.6"
          />
          {/* Inner diamond */}
          <motion.path
            d="M300 190 L390 300 L300 410 L210 300 Z"
            stroke="#fbbf24"
            strokeWidth="1"
            fill="rgba(251, 191, 36, 0.08)"
            animate={reduce ? {} : { rotate: [0, 5, 0, -5, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            style={{ originX: "300px", originY: "300px" }}
          />
          {/* Central core */}
          <motion.path
            d="M300 225 L355 300 L300 375 L245 300 Z"
            stroke="#fcd34d"
            strokeWidth="1.5"
            fill="rgba(252, 211, 77, 0.15)"
            filter="url(#glowFilter)"
            animate={reduce ? {} : { scale: [1, 1.05, 1] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            style={{ originX: "300px", originY: "300px" }}
          />
          {/* Innermost point — the spark */}
          <motion.circle
            cx="300" cy="300" r="4" fill="#fde68a"
            animate={{ r: [4, 7, 4], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            filter="url(#glowFilter)"
          />

          {/* Vertical axis */}
          <line x1="300" y1="150" x2="300" y2="450" stroke="#fbbf24" strokeWidth="0.8" strokeOpacity="0.3" />
          {/* Horizontal axis */}
          <line x1="180" y1="300" x2="420" y2="300" stroke="#fbbf24" strokeWidth="0.8" strokeOpacity="0.25" />

          {/* Cross diagonals */}
          <line x1="190" y1="200" x2="410" y2="400" stroke="#fcd34d" strokeWidth="0.5" strokeOpacity="0.15" />
          <line x1="410" y1="200" x2="190" y2="400" stroke="#fcd34d" strokeWidth="0.5" strokeOpacity="0.15" />
        </motion.g>

        {/* === Floating data bits (representing leads, documents, conversations) === */}
        {reduce ? null : (
          <>
            {/* Document / contract shapes */}
            <motion.g
              animate={{ y: [-6, 6, -6], opacity: [0, 0.6, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              <rect x="140" y="170" width="10" height="12" rx="1" stroke="#fde68a" strokeWidth="0.8" fill="none" />
              <line x1="143" y1="174" x2="147" y2="174" stroke="#fde68a" strokeWidth="0.5" />
              <line x1="143" y1="177" x2="147" y2="177" stroke="#fde68a" strokeWidth="0.5" />
            </motion.g>
            <motion.g
              animate={{ y: [8, -8, 8], opacity: [0, 0.5, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            >
              <rect x="440" y="370" width="10" height="12" rx="1" stroke="#fcd34d" strokeWidth="0.8" fill="none" />
              <line x1="443" y1="374" x2="447" y2="374" stroke="#fcd34d" strokeWidth="0.5" />
              <line x1="443" y1="377" x2="447" y2="377" stroke="#fcd34d" strokeWidth="0.5" />
            </motion.g>

            {/* Small star/burst particles */}
            <motion.g
              animate={{ rotate: 360, opacity: [0, 0.8, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
              style={{ originX: "200px", originY: "400px" }}
            >
              <line x1="196" y1="396" x2="204" y2="404" stroke="#fde68a" strokeWidth="0.8" opacity="0.4" />
              <line x1="204" y1="396" x2="196" y2="404" stroke="#fde68a" strokeWidth="0.8" opacity="0.4" />
            </motion.g>
            <motion.g
              animate={{ rotate: -360, opacity: [0, 0.6, 0] }}
              transition={{ duration: 8, repeat: Infinity, ease: "linear", delay: 2 }}
              style={{ originX: "400px", originY: "200px" }}
            >
              <line x1="396" y1="196" x2="404" y2="204" stroke="#fbbf24" strokeWidth="0.8" opacity="0.3" />
              <line x1="404" y1="196" x2="396" y2="204" stroke="#fbbf24" strokeWidth="0.8" opacity="0.3" />
            </motion.g>

            {/* Micro-dot clusters */}
            <motion.circle cx="160" cy="220" r="1.5" fill="#fde68a" animate={{ y: [0, -12, 0] }} transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }} />
            <motion.circle cx="430" cy="250" r="1.2" fill="#fcd34d" animate={{ y: [0, 10, 0] }} transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }} />
            <motion.circle cx="180" cy="360" r="1" fill="#fbbf24" animate={{ y: [0, 8, 0] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }} />
            <motion.circle cx="420" cy="380" r="1.8" fill="#f59e0b" animate={{ y: [0, -8, 0] }} transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut", delay: 1.5 }} />
            <motion.circle cx="350" cy="130" r="1.2" fill="#fde68a" animate={{ y: [0, 14, 0] }} transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 0.3 }} />
            <motion.circle cx="230" cy="480" r="1" fill="#fcd34d" animate={{ y: [0, -10, 0] }} transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut", delay: 2 }} />
            <motion.circle cx="370" cy="460" r="1.5" fill="#fbbf24" animate={{ y: [0, 6, 0] }} transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut", delay: 0.8 }} />
          </>
        )}

        {/* === Stable anchor nodes (always visible) === */}
        <circle cx="300" cy="160" r="1.5" fill="#fbbf24" opacity="0.3" />
        <circle cx="440" cy="300" r="1.5" fill="#fcd34d" opacity="0.3" />
        <circle cx="300" cy="440" r="1.5" fill="#f59e0b" opacity="0.3" />
        <circle cx="160" cy="300" r="1.5" fill="#fde68a" opacity="0.3" />
      </svg>
    </div>
  );
}