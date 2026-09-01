import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import mrNerdyStandSleep from '../../assets/mr_nerdy_stand_sleep-removebg-preview.png';
import { SystemWideLoader } from './Loader';
import { IconUser, IconMail, IconArrowRight, IconAlertCircle, IconTerminal } from './Icons';

export const LocalAuthModal: React.FC = () => {
  const { userId, loginLocalUser } = usePanelStore();
  const [usernameInput, setUsernameInput] = React.useState('');
  const [emailInput, setEmailInput] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);

  // If userId is already set in store, do not render
  if (userId) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedUser = usernameInput.trim();
    const trimmedEmail = emailInput.trim();

    if (!trimmedUser || !trimmedEmail) {
      setError('Please fill in both fields.');
      return;
    }

    setIsLoading(true);

    try {
      await loginLocalUser(trimmedUser, trimmedEmail);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Full-screen Loading Overlay during Auth Verification */}
      {isLoading && <SystemWideLoader text="INITIALIZING LOCAL ENVIRONMENT..." />}

      {/* Main Glassmorphic Modal Backdrop */}
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-fade-in select-none">
        
        <div className="relative w-full max-w-sm rounded-3xl bg-[var(--bg-card)] border app-border p-6 shadow-2xl flex flex-col items-center text-center overflow-hidden">
          
          {/* Subtle Ambient Glow Effect */}
          <div className="absolute -top-16 -right-16 w-32 h-32 bg-[var(--accent-subtle)] rounded-full blur-3xl pointer-events-none" />

          {/* Mascot Header Avatar */}
          <div className="relative w-20 h-20 rounded-2xl bg-[var(--bg-base)] border app-border flex items-center justify-center p-2 mb-4 shadow-inner group">
            <img 
              src={mrNerdyStandSleep} 
              alt="Mr. Nerdy Mascot" 
              className="h-16 w-auto object-contain translate-y-1 transition-transform group-hover:scale-105" 
            />
            <div className="absolute -bottom-1 -right-1 p-1 rounded-lg bg-[var(--accent)] text-white shadow-xs">
              <IconTerminal className="text-[10px]" />
            </div>
          </div>

          {/* Title & Tagline */}
          <h2 className="text-base font-bold tracking-tight text-[var(--text-main)] mb-1">
            Initialize Developer Environment
          </h2>
          <p className="text-xs font-mono text-[var(--text-muted)] mb-6 max-w-xs leading-relaxed">
            Set up your developer profile to isolate research papers, parameter extractions, and PyTorch builds.
          </p>

          <form onSubmit={handleSubmit} className="w-full text-left space-y-4">
            
            {/* Error Banner */}
            {error && (
              <div className="p-3 rounded-xl border border-red-500/40 bg-red-500/10 text-red-400 text-xs font-mono flex items-center gap-2 animate-fade-in">
                <IconAlertCircle className="text-sm shrink-0 text-red-400" />
                <span>{error}</span>
              </div>
            )}

            {/* Username Input */}
            <div>
              <label className="block text-[10px] font-mono font-bold text-[var(--text-muted)] mb-1.5 uppercase tracking-wider">
                Developer Identity (Username)
              </label>
              <div className="relative">
                <IconUser className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                <input
                  type="text"
                  placeholder="e.g. Varun Chandra"
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border app-border bg-[var(--bg-base)] text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all text-xs font-mono disabled:opacity-50"
                  disabled={isLoading}
                  required
                />
              </div>
            </div>

            {/* Email Address Input */}
            <div>
              <label className="block text-[10px] font-mono font-bold text-[var(--text-muted)] mb-1.5 uppercase tracking-wider">
                Research Contact (Email)
              </label>
              <div className="relative">
                <IconMail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                <input
                  type="email"
                  placeholder="e.g. varun@example.com"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border app-border bg-[var(--bg-base)] text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all text-xs font-mono disabled:opacity-50"
                  disabled={isLoading}
                  required
                />
              </div>
            </div>

            {/* Submit Action Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 mt-2 bg-[var(--accent)] hover:opacity-90 active:scale-[0.99] disabled:opacity-50 text-white font-mono font-bold tracking-wider text-xs uppercase rounded-xl transition-all duration-200 shadow-md flex items-center justify-center gap-2 cursor-pointer select-none"
            >
              <span>Start Local Workspace</span>
              <IconArrowRight className="text-sm stroke-[2.5]" />
            </button>
          </form>
        </div>
      </div>
    </>
  );
};