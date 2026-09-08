import React from 'react';
import { IconUser, IconForward } from '../ui/Icons';
import { usePanelStore } from '../../store/panelStore';

interface UserProfileCardProps {
  isOpen: boolean;
}

export const UserProfileCard: React.FC<UserProfileCardProps> = ({ isOpen }) => {
  const { username, setActiveView } = usePanelStore();

  const handleOpenProfile = () => {
    setActiveView('profile');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleOpenProfile();
    }
  };

  /* Expanded Sidebar Drawer Profile Card */
  if (isOpen) {
    return (
      <div 
        onClick={handleOpenProfile}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        className="w-full flex items-center justify-between p-2.5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--accent-subtle)] hover:border-[var(--accent-border)] shadow-xs transition-all duration-200 cursor-pointer select-none group outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
      >
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {/* Avatar Icon Box */}
          <div className="relative w-9 h-9 rounded-xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)] flex items-center justify-center font-mono shrink-0 group-hover:scale-105 group-hover:border-[var(--accent)] transition-all duration-200">
            <IconUser className="text-base" />
            <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-processing animate-pulse shadow-[0_0_6px_var(--processing)]" />
          </div>

          {/* User Meta Identifiers */}
          <div className="flex flex-col items-start min-w-0 flex-1 font-mono">
            <span className="text-xs font-bold tracking-tight text-[var(--text-main)] leading-tight truncate group-hover:text-[var(--accent)] transition-colors">
              {username || 'Varun Chandra'}
            </span>
            <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider mt-0.5 flex items-center gap-1">
              <span>Developer Profile</span>
            </span>
          </div>
        </div>

        <IconForward className="text-xs text-[var(--text-muted)] group-hover:text-[var(--accent)] group-hover:translate-x-0.5 transition-all duration-200 shrink-0 ml-1" />
      </div>
    );
  }

  /* Collapsed Rail View Profile Icon Button */
  return (
    <div 
      onClick={handleOpenProfile}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      title={`${username || 'Varun Chandra'} (Developer Profile)`}
      aria-label="Open developer profile"
      className="relative w-10 h-10 rounded-xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)] flex items-center justify-center cursor-pointer hover:bg-[var(--accent-subtle)]/80 hover:border-[var(--accent)] transition-all duration-200 shadow-xs active:scale-95 outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] group"
    >
      <IconUser className="text-base group-hover:scale-110 transition-transform duration-200" />
      <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-processing animate-pulse shadow-[0_0_6px_var(--processing)]" />
    </div>
  );
};