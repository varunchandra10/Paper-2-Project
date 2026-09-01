import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import mrNerdyStandSleep from '../../assets/mr_nerdy_stand_sleep-removebg-preview.png';
import { SystemWideLoader } from './Loader';
import { FiUser, FiMail, FiArrowRight, FiAlertCircle, FiTerminal } from 'react-icons/fi';

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

    if (!/\S+@\S+\.\S+/.test(trimmedEmail)) {
      setError('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);
    try {
      await loginLocalUser(trimmedUser, trimmedEmail);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to initialize local workspace.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {isLoading && <SystemWideLoader message="Connecting local workspace profile..." />}
      
      <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-[var(--bg-base)]/80 backdrop-blur-xl p-4 animate-fade-in select-none">
        <div className="w-full max-w-md p-7 rounded-2xl border app-border bg-[var(--bg-card)] text-[var(--text-main)] shadow-[0_20px_60px_rgba(0,0,0,0.6)] flex flex-col items-center text-center relative overflow-hidden">
          
          {/* HUD Corner Accents */}
          <div className="absolute top-3 left-3 w-3 h-3 border-t-2 border-l-2 border-[var(--accent-border)] pointer-events-none" />
          <div className="absolute top-3 right-3 w-3 h-3 border-t-2 border-r-2 border-[var(--accent-border)] pointer-events-none" />
          <div className="absolute bottom-3 left-3 w-3 h-3 border-b-2 border-l-2 border-[var(--accent-border)] pointer-events-none" />
          <div className="absolute bottom-3 right-3 w-3 h-3 border-b-2 border-r-2 border-[var(--accent-border)] pointer-events-none" />

          {/* Background Ambient Glows */}
          <div className="absolute -top-16 -left-16 w-36 h-36 bg-[var(--accent-subtle)] rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-16 -right-16 w-36 h-36 bg-[var(--accent-subtle)] rounded-full blur-3xl pointer-events-none" />

          {/* Mascot Avatar Container */}
          <div className="w-20 h-20 mb-4 bg-[var(--accent-subtle)] rounded-2xl flex items-center justify-center border border-[var(--accent-border)] shadow-xs relative overflow-hidden group shrink-0">
            <div className="w-full h-full flex items-start justify-center overflow-hidden pt-1">
              <img 
                src={mrNerdyStandSleep} 
                alt="Mr. Nerdy Mascot" 
                className="w-[180%] max-w-none object-cover select-none filter drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)] group-hover:scale-105 transition-transform duration-300 -translate-y-[5%]" 
              />
            </div>
          </div>

          {/* Header Title & Subtitle */}
          <div className="flex items-center gap-1.5 text-[var(--accent)] font-mono text-[11px] font-bold tracking-widest uppercase mb-1">
            <FiTerminal className="text-xs" /> Synthexis 
          </div>
          <h2 className="text-xl font-mono font-bold tracking-tight text-[var(--text-main)] mb-1.5">
            Initialize Workspace
          </h2>
          <p className="text-xs font-mono text-[var(--text-muted)] mb-6 max-w-xs leading-relaxed">
            Set up your developer profile to isolate research papers, parameter extractions, and PyTorch builds.
          </p>

          <form onSubmit={handleSubmit} className="w-full text-left space-y-4">
            
            {/* Error Banner */}
            {error && (
              <div className="p-3 rounded-xl border border-red-500/40 bg-red-500/10 text-red-400 text-xs font-mono flex items-center gap-2 animate-fade-in">
                <FiAlertCircle className="text-sm shrink-0 text-red-400" />
                <span>{error}</span>
              </div>
            )}

            {/* Username Input */}
            <div>
              <label className="block text-[10px] font-mono font-bold text-[var(--text-muted)] mb-1.5 uppercase tracking-wider">
                Developer Identity (Username)
              </label>
              <div className="relative">
                <FiUser className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
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
                <FiMail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
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
              <FiArrowRight className="text-sm stroke-[2.5]" />
            </button>
          </form>
        </div>
      </div>
    </>
  );
};