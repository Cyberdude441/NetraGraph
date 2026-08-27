import React from "react";
import { useTheme } from "@/lib/theme";

interface NetraLogoProps {
  className?: string;
  size?: number;
  showText?: boolean;
  inverted?: boolean;
}

export function NetraLogo({
  className = "",
  size = 28,
  showText = true,
  inverted = false,
}: NetraLogoProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {/* Official Government Investigation Emblem */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 36 36"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
      >
        {/* Outer Shield Container */}
        <path
          d="M18 2L32 7.5V19C32 27.2 26 33.2 18 35.5C10 33.2 4 27.2 4 19V7.5L18 2Z"
          fill={inverted ? "#064E3B" : isDark ? "#064E3B" : "#F0FDF4"}
          stroke={inverted ? "#FFFFFF" : isDark ? "#16A34A" : "#064E3B"}
          strokeWidth="2"
          strokeLinejoin="round"
        />

        {/* Inner Investigation Network Links */}
        <path
          d="M18 9V26M11 16L25 20M25 16L11 20"
          stroke={inverted ? "#86EFAC" : isDark ? "#4ADE80" : "#86EFAC"}
          strokeWidth="1.4"
        />

        {/* Central Eye / Focal Node */}
        <circle
          cx="18"
          cy="18"
          r="4.5"
          fill={inverted ? "#FFFFFF" : isDark ? "#22C55E" : "#064E3B"}
        />
        <circle
          cx="18"
          cy="18"
          r="2"
          fill={inverted ? "#064E3B" : "#FFFFFF"}
        />

        {/* Outer Nodes */}
        <circle cx="18" cy="9" r="2" fill={inverted ? "#86EFAC" : "#16A34A"} />
        <circle cx="11" cy="16" r="2" fill={inverted ? "#86EFAC" : "#16A34A"} />
        <circle cx="25" cy="16" r="2" fill={inverted ? "#86EFAC" : "#16A34A"} />
        <circle cx="11" cy="20" r="2" fill={inverted ? "#86EFAC" : "#16A34A"} />
        <circle cx="25" cy="20" r="2" fill={inverted ? "#86EFAC" : "#16A34A"} />
        <circle cx="18" cy="26" r="2" fill={inverted ? "#86EFAC" : "#16A34A"} />
      </svg>

      {showText && (
        <div className="flex flex-col text-left">
          <span
            className={`font-display font-bold tracking-tight text-sm leading-tight flex items-center gap-1.5 ${
              inverted ? "text-white" : "text-[#111827]"
            }`}
          >
            NetraGraph
            <span
              className={`text-[9px] font-sans font-semibold px-1.5 py-0.5 rounded border ${
                inverted
                  ? "bg-white/20 text-white border-white/30"
                  : "bg-emerald-50 text-[#064E3B] border-emerald-200"
              }`}
            >
              GOV
            </span>
          </span>
          <span
            className={`text-[10px] font-sans font-medium tracking-normal leading-none mt-0.5 ${
              inverted ? "text-emerald-100" : "text-[#64748B]"
            }`}
          >
            AI-Assisted Investigation & Intelligence System
          </span>
        </div>
      )}
    </div>
  );
}

export default NetraLogo;

