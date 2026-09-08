import React, { useState, useRef, useEffect } from 'react';

export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  content: React.ReactNode;
  shortcut?: string;
  position?: TooltipPosition;
  delay?: number;
  disabled?: boolean;
  className?: string;
  children: React.ReactElement;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  shortcut,
  position = 'top',
  delay = 150,
  disabled = false,
  className = '',
  children,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showTooltip = () => {
    if (disabled || !content) return;
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  if (disabled || !content) {
    return children;
  }

  // Positioning utility classes
  const getPositionClasses = () => {
    switch (position) {
      case 'bottom':
        return 'top-full left-1/2 -translate-x-1/2 mt-2';
      case 'left':
        return 'right-full top-1/2 -translate-y-1/2 mr-2';
      case 'right':
        return 'left-full top-1/2 -translate-y-1/2 ml-2';
      case 'top':
      default:
        return 'bottom-full left-1/2 -translate-x-1/2 mb-2';
    }
  };

  // Arrow orientation classes
  const getArrowClasses = () => {
    switch (position) {
      case 'bottom':
        return 'bottom-full left-1/2 -translate-x-1/2 border-b-[var(--bg-card)] border-x-transparent border-t-transparent border-[5px] mb-[-1px]';
      case 'left':
        return 'left-full top-1/2 -translate-y-1/2 border-l-[var(--bg-card)] border-y-transparent border-r-transparent border-[5px] ml-[-1px]';
      case 'right':
        return 'right-full top-1/2 -translate-y-1/2 border-r-[var(--bg-card)] border-y-transparent border-l-transparent border-[5px] mr-[-1px]';
      case 'top':
      default:
        return 'top-full left-1/2 -translate-x-1/2 border-t-[var(--bg-card)] border-x-transparent border-b-transparent border-[5px] mt-[-1px]';
    }
  };

  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}

      {isVisible && (
        <div
          role="tooltip"
          className={`absolute z-50 pointer-events-none whitespace-nowrap animate-fade-in ${getPositionClasses()} ${className}`}
        >
          <div className="relative flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-sans font-medium tracking-normal text-[var(--text-main)] bg-[var(--bg-card)]/95 backdrop-blur-md rounded-lg border border-[var(--accent-border)] shadow-xl shadow-black/20 dark:shadow-black/50 transition-all duration-150 select-none">
            {/* Tooltip Content */}
            <span>{content}</span>

            {/* Optional Keyboard Shortcut Badge */}
            {shortcut && (
              <span className="text-[9px] font-mono font-semibold px-1 py-0.2 rounded bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] ml-0.5">
                {shortcut}
              </span>
            )}

            {/* Subtle Triangle Arrow */}
            <div className={`absolute w-0 h-0 pointer-events-none ${getArrowClasses()}`} />
          </div>
        </div>
      )}
    </div>
  );
};
