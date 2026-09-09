import React from "react";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  borderGlow?: boolean;
  onClick?: () => void;
}

export function GlassCard({
  children,
  className = "",
  hoverEffect = true,
  borderGlow = false,
  onClick,
}: GlassCardProps) {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl p-6 transition-all duration-300 relative overflow-hidden ${
        hoverEffect ? "glass-card" : "glass-panel"
      } ${
        borderGlow
          ? "border-[#DA7756]/40 shadow-[0_0_24px_-4px_rgba(218,119,86,0.2)]"
          : "border-white/8"
      } ${onClick ? "cursor-pointer" : ""} ${className}`}
    >
      {children}
    </div>
  );
}
