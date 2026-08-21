import React from 'react';
import { useThemeStore } from '../../store/themeStore';
import { FaSun, FaMoon } from 'react-icons/fa6';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useThemeStore();
  const isLight = theme === 'light';

  return (
    <button
      onClick={toggleTheme}
      className="p-2.5 text-sm text-foreground/45 hover:bg-foreground/10 hover:text-foreground transition-all cursor-pointer flex items-center justify-center w-9 h-9"
      title={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
      aria-label={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
    >
      {isLight
        ? <FaMoon className="text-[13px]" />
        : <FaSun  className="text-[13px] text-brass/70" />
      }
    </button>
  );
};
