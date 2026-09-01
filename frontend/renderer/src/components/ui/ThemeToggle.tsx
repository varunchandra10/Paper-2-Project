import React from 'react';
import { useThemeStore } from '../../store/themeStore';
import { FaSun, FaMoon } from 'react-icons/fa6';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useThemeStore();
  const isLight = theme === 'light';

  return (
    <button
      onClick={toggleTheme}
      className="relative flex items-center justify-center w-7 h-7 rounded-xl border border-border/60 bg-card/80 hover:bg-muted text-foreground/80 hover:text-brass transition-all duration-200 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-brass active:scale-95 shadow-xs group"
      title={isLight ? 'Switch to Dark Mode (Desk at Night)' : 'Switch to Light Mode (Archival Daylight)'}
      aria-label={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
    >
      <div className="transition-transform duration-300 transform group-hover:scale-110 flex items-center justify-center">
        {isLight ? (
          <FaMoon className="text-xs text-foreground/80 group-hover:text-brass transition-colors" />
        ) : (
          <FaSun className="text-xs text-brass drop-shadow-[0_0_6px_rgba(212,163,56,0.5)] group-hover:rotate-45 transition-transform duration-300" />
        )}
      </div>
    </button>
  );
};