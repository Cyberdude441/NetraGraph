import React from "react";
import { useTheme } from "@/lib/theme";

interface NetraLogoProps {
  className?: string;
  size?: number;
  showText?: boolean;
}

export function NetraLogo({
  className = "",
  size = 26,
  showText = true,
}: NetraLogoProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {/* Dynamic Emblem */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 36 36"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
      >
        {/* Shield Structure */}
        <polygon
          points="18,2 33,9 33,25 18,34 3,25 3,9"
          stroke={isDark ? "#374045" : "#CBD5E1"}
          strokeWidth="1.5"
          fill={isDark ? "#1F2C34" : "#F1F5F9"}
        />

        {/* Network Connections */}
        <line x1="18" y1="9" x2="11" y2="17" stroke={isDark ? "#374045" : "#94A3B8"} strokeWidth="1.2" />
        <line x1="18" y1="9" x2="25" y2="17" stroke={isDark ? "#374045" : "#94A3B8"} strokeWidth="1.2" />
        <line x1="11" y1="17" x2="18" y2="23" stroke={isDark ? "#00A884" : "#2563EB"} strokeWidth="1.5" />
        <line x1="25" y1="17" x2="18" y2="23" stroke={isDark ? "#00A884" : "#2563EB"} strokeWidth="1.5" />
        <line x1="18" y1="23" x2="13" y2="28" stroke={isDark ? "#374045" : "#94A3B8"} strokeWidth="1.2" />
        <line x1="18" y1="23" x2="23" y2="28" stroke={isDark ? "#374045" : "#94A3B8"} strokeWidth="1.2" />

        {/* Focal Nodes */}
        <circle cx="18" cy="9" r="2.2" fill={isDark ? "#8696A0" : "#64748B"} />
        <circle cx="11" cy="17" r="2.2" fill={isDark ? "#8696A0" : "#64748B"} />
        <circle cx="25" cy="17" r="2.2" fill={isDark ? "#8696A0" : "#64748B"} />
        <circle cx="18" cy="23" r="2.8" fill={isDark ? "#00A884" : "#2563EB"} />
        <circle cx="13" cy="28" r="1.8" fill={isDark ? "#667781" : "#94A3B8"} />
        <circle cx="23" cy="28" r="1.8" fill={isDark ? "#667781" : "#94A3B8"} />
      </svg>

      {showText && (
        <div className="flex flex-col text-left">
          <span className="font-display font-bold tracking-tight text-sm leading-tight text-[var(--text-primary)] flex items-center gap-1.5">
            NetraGraph
            <span className="text-[9px] font-sans font-semibold px-1.5 py-0.2 rounded bg-[var(--panel-sec)] text-[var(--brand)] border border-[var(--border-theme)]">
              AI
            </span>
          </span>
          <span className="text-[9px] font-sans font-medium tracking-normal text-[var(--text-secondary)] leading-none mt-0.5">
            Criminal Intelligence Platform
          </span>
        </div>
      )}
    </div>
  );
}

export default NetraLogo;
