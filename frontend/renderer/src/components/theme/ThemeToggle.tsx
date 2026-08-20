import React from 'react';
import { useThemeStore } from '../../store/themeStore';
import { FaSun, FaMoon } from 'react-icons/fa6';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useThemeStore();
  const isLight = theme === 'light';

  return (
    <label 
      className="relative inline-flex items-center cursor-pointer select-none group" 
      title="Toggle Theme"
      aria-label={`Switch to ${isLight ? 'dark' : 'light'} mode`}
    >
      {/* Accessible visually hidden input */}
      <input
        type="checkbox"
        id="theme-toggle"
        className="sr-only peer"
        checked={isLight}
        onChange={toggleTheme}
      />
      
      {/* Switch Track */}
      <div className="w-[42px] h-[22px] bg-black/20 border border-border/50 rounded-full transition-colors duration-300 shadow-inner group-hover:border-brass/40 peer-focus-visible:ring-2 peer-focus-visible:ring-brass/40 relative overflow-hidden">
        
        {/* Background Icons (Stationary) */}
        <div className="absolute inset-0 flex justify-between items-center px-1.5 pointer-events-none">
          <FaMoon className="text-[10px] text-foreground/30" />
          <FaSun className="text-[10px] text-brass/30" />
        </div>

        {/* Sliding Thumb */}
        <div 
          className={`absolute top-[2px] left-[2px] h-[16px] w-[16px] bg-foreground rounded-full shadow-sm transition-transform duration-500 ease-[cubic-bezier(0.68,-0.55,0.265,1.55)] flex items-center justify-center z-10 ${
            isLight ? 'translate-x-[20px]' : 'translate-x-0'
          }`}
        >
          {/* Active icon inside the thumb */}
          {isLight ? (
            <FaSun className="text-[9px] text-background" />
          ) : (
            <FaMoon className="text-[9px] text-background" />
          )}
        </div>
      </div>
    </label>
  );
};