'use client';

import React from 'react';

interface EcoDishLogoProps {
  className?: string; // Apply width/height like w-16 h-16 from parent
  variant?: 'icon' | 'brand'; // 'brand' renders icon + wordmark; 'icon' shows just the glyph
  labelClassName?: string; // Additional classes for the wordmark text
}

// A sleek, 3D-styled EcoDish365 logo with layered gradients and subtle depth
// Accessible SVG; supports an icon-only or brand wordmark variant
export default function EcoDishLogo({ className = '', variant = 'icon', labelClassName = '' }: EcoDishLogoProps) {
  const Icon = ({ embedText }: { embedText: boolean }) => (
    <div
      className={`relative inline-flex items-center justify-center select-none ${className}`}
      aria-hidden="true"
    >
      {/* Outer 3D ring */}
      <div
        className="absolute inset-0 rounded-full bg-[conic-gradient(from_220deg_at_50%_50%,_#22c55e,_#06b6d4,_#3b82f6,_#22c55e)] shadow-[inset_0_2px_6px_rgba(255,255,255,0.5),_inset_0_-8px_18px_rgba(0,0,0,0.25),_0_12px_24px_rgba(0,0,0,0.12)]"
      />

      {/* Inner disc */}
      <div
        className="absolute rounded-full inset-[9%] bg-[radial-gradient(120%_120%_at_30%_30%,_rgba(255,255,255,0.9)_0%,_rgba(255,255,255,0.65)_35%,_rgba(14,165,233,0.2)_100%)] shadow-[inset_0_8px_18px_rgba(255,255,255,0.85),_inset_0_-10px_24px_rgba(2,132,199,0.25)]"
      />

      {/* Stylized leaf + globe marks (SVG) */}
      <svg
        viewBox="0 0 100 100"
        className="relative drop-shadow-[0_6px_8px_rgba(0,0,0,0.2)] w-[70%] h-[70%]"
        aria-label="EcoDish365 logo"
        role="img"
      >
        <defs>
          <linearGradient id="leafGradient" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="100%" stopColor="#16a34a" />
          </linearGradient>
          <linearGradient id="globeGradient" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
        </defs>

        {/* Globe circle */}
        <circle cx="50" cy="50" r="34" fill="url(#globeGradient)" opacity="0.25" />
        {/* Globe lat/long lines */}
        <g stroke="#0ea5e9" strokeWidth="1" opacity="0.45">
          <ellipse cx="50" cy="50" rx="30" ry="20" fill="none" />
          <ellipse cx="50" cy="50" rx="25" ry="16" fill="none" />
          <path d="M20,50 H80" fill="none" />
          <path d="M50,20 V80" fill="none" />
          <path d="M32,28 C50,42 50,58 32,72" fill="none" />
          <path d="M68,28 C50,42 50,58 68,72" fill="none" />
        </g>

        {/* Leaf shape */}
        <path
          d="M23 62c18-4 34-14 46-30 6 24-8 45-29 47-10 1-17-5-17-17z"
          fill="url(#leafGradient)"
          stroke="#16a34a"
          strokeWidth="1.25"
          opacity="0.95"
        />
        {/* Leaf vein */}
        <path d="M26 61c10-3 20-9 29-18" stroke="#15803d" strokeWidth="1.2" fill="none" opacity="0.7" />

        {/* Embedded brand text (only for icon variant) */}
        {embedText && (
          <text
            x="50"
            y="90"
            textAnchor="middle"
            fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial"
            fontWeight="700"
            fontSize="12"
            fill="#0f172a"
            opacity="0.9"
          >
            EcoDish365
          </text>
        )}
      </svg>

      {/* Gloss highlight */}
      <div className="pointer-events-none absolute -top-1 left-1/2 -translate-x-1/2 w-3/4 h-1/3 rounded-[999px] bg-[linear-gradient(180deg,_rgba(255,255,255,0.65)_0%,_rgba(255,255,255,0.05)_85%)] blur-[1px]" />
    </div>
  );

  if (variant === 'brand') {
    return (
      <div className={`inline-flex items-center gap-3 ${className}`}>
        <Icon embedText={false} />
        <div className="leading-none">
          <span
            className={`text-lg sm:text-xl font-extrabold tracking-tight bg-gradient-to-r from-blue-700 via-emerald-600 to-blue-600 bg-clip-text text-transparent drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)] ${labelClassName}`}
          >
            EcoDish365
          </span>
          <div className="mt-0.5 h-[3px] w-full max-w-[110px] bg-gradient-to-r from-blue-500 via-green-500 to-emerald-500 rounded-full opacity-70" />
        </div>
      </div>
    );
  }

  // Default: icon variant (with embedded small text for legacy parity)
  return <Icon embedText={true} />;
}


