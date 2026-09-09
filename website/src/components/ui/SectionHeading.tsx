import React from "react";
import { Badge } from "./Badge";

interface SectionHeadingProps {
  badge?: string;
  badgeVariant?: "accent" | "cyan" | "purple" | "green" | "amber" | "neutral";
  title: string;
  highlightText?: string;
  description?: string;
  align?: "left" | "center";
  className?: string;
}

export function SectionHeading({
  badge,
  badgeVariant = "accent",
  title,
  highlightText,
  description,
  align = "center",
  className = "",
}: SectionHeadingProps) {
  const isCenter = align === "center";

  return (
    <div
      className={`mb-12 md:mb-16 ${
        isCenter ? "text-center max-w-3xl mx-auto" : "text-left max-w-4xl"
      } ${className}`}
    >
      {badge && (
        <div className={`mb-3.5 flex ${isCenter ? "justify-center" : "justify-start"}`}>
          <Badge variant={badgeVariant}>{badge}</Badge>
        </div>
      )}
      <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-[#F4F3EE] font-heading leading-tight">
        {title}{" "}
        {highlightText && (
          <span className="text-[#DA7756] glow-accent">{highlightText}</span>
        )}
      </h2>
      {description && (
        <p className="mt-4 text-base md:text-lg text-[#9E9E99] leading-relaxed font-sans">
          {description}
        </p>
      )}
    </div>
  );
}
