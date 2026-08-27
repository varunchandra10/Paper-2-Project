import React from 'react';
import { useThemeStore } from '../../store/themeStore';
import { FaSun, FaMoon } from 'react-icons/fa6';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useThemeStore();
  const isLight = theme === 'light';

  return (
    <button
      onClick={toggleTheme}
      className="text-foreground/55 hover:bg-foreground/10 hover:text-foreground transition-all cursor-pointer flex items-center justify-center w-6 h-6 rounded-full"
      title={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
      aria-label={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
    >
      {isLight
        ? <FaMoon className="text-[9.5px]" />
        : <FaSun  className="text-[9.5px] text-brass" />
      }
    </button>
  );
};
