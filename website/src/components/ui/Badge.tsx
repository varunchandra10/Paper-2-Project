import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "accent" | "cyan" | "purple" | "green" | "amber" | "neutral";
  size?: "sm" | "md";
  className?: string;
  icon?: React.ReactNode;
}

export function Badge({
  children,
  variant = "accent",
  size = "sm",
  className = "",
  icon,
}: BadgeProps) {
  const variantStyles = {
    accent: "bg-[#DA7756]/15 text-[#DA7756] border-[#DA7756]/30",
    cyan: "bg-[#38BDF8]/15 text-[#38BDF8] border-[#38BDF8]/30",
    purple: "bg-[#818CF8]/15 text-[#818CF8] border-[#818CF8]/30",
    green: "bg-[#34D399]/15 text-[#34D399] border-[#34D399]/30",
    amber: "bg-[#FBBF24]/15 text-[#FBBF24] border-[#FBBF24]/30",
    neutral: "bg-white/5 text-[#9E9E99] border-white/10",
  };

  const sizeStyles = {
    sm: "text-xs px-2.5 py-0.5",
    md: "text-sm px-3.5 py-1",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider font-semibold rounded-full border ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {icon && <span className="inline-block text-[0.9em]">{icon}</span>}
      {children}
    </span>
  );
}
