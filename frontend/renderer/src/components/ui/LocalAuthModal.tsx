import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import mrNerdyStandSleep from '../../assets/mr_nerdy_stand_sleep-removebg-preview.png';
import { SystemWideLoader } from './Loader';
import { FiUser, FiMail, FiArrowRight, FiAlertCircle } from 'react-icons/fi';

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
      
      <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-xl p-4 animate-fade-in">
        <div className="w-full max-w-md p-7 rounded-3xl border border-border/60 bg-card/95 text-card-foreground shadow-[0_20px_60px_rgba(0,0,0,0.5)] flex flex-col items-center text-center relative overflow-hidden">
          
          {/* Background Ambient Glow */}
          <div className="absolute -top-20 -left-20 w-40 h-40 bg-brass/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-20 -right-20 w-40 h-40 bg-brass/10 rounded-full blur-3xl pointer-events-none" />

          {/* Mr. Nerdy Face Close-up Badge */}
          <div className="w-20 h-20 mb-4 bg-gradient-to-br from-brass/20 via-muted to-muted/80 rounded-2xl flex items-center justify-center border border-brass/40 shadow-[0_0_20px_rgba(212,175,55,0.15)] relative overflow-hidden group shrink-0">
            {/* Mascot Image cropped to show face */}
            <div className="w-full h-full flex items-start justify-center overflow-hidden pt-1">
              <img 
                src={mrNerdyStandSleep} 
                alt="Mr. Nerdy Face" 
                className="w-[180%] max-w-none object-cover select-none filter drop-shadow-[0_2px_8px_rgba(0,0,0,0.4)] group-hover:scale-105 transition-transform duration-300 translate-y-[-5%]" 
              />
            </div>
          </div>

          <h2 className="text-xl font-bold font-sans tracking-tight text-foreground mb-1">
            Welcome to Synthexis
          </h2>
          <p className="text-xs text-muted-foreground mb-6 max-w-xs leading-relaxed">
            Set up your local developer profile to isolate chat sessions, preference facts, and generated codebases.
          </p>

          <form onSubmit={handleSubmit} className="w-full text-left space-y-4">
            
            {/* Error Banner */}
            {error && (
              <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-xs font-sans flex items-center gap-2 animate-fade-in">
                <FiAlertCircle className="text-sm shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Username Input */}
            <div>
              <label className="block text-[10px] font-mono font-bold text-muted-foreground/80 mb-1.5 uppercase tracking-wider">
                Username
              </label>
              <div className="relative">
                <FiUser className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-sm" />
                <input
                  type="text"
                  placeholder="e.g. Alex Smith"
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border/60 bg-muted/40 text-foreground placeholder:text-muted-foreground/40 outline-none focus:border-brass/60 focus:ring-1 focus:ring-brass/30 transition-all text-xs font-sans disabled:opacity-50"
                  disabled={isLoading}
                  required
                />
              </div>
            </div>

            {/* Email Address Input */}
            <div>
              <label className="block text-[10px] font-mono font-bold text-muted-foreground/80 mb-1.5 uppercase tracking-wider">
                Email Address
              </label>
              <div className="relative">
                <FiMail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-sm" />
                <input
                  type="email"
                  placeholder="e.g. alex@example.com"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border/60 bg-muted/40 text-foreground placeholder:text-muted-foreground/40 outline-none focus:border-brass/60 focus:ring-1 focus:ring-brass/30 transition-all text-xs font-sans disabled:opacity-50"
                  disabled={isLoading}
                  required
                />
              </div>
            </div>

            {/* Submit Action Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 mt-2 bg-brass hover:bg-brass/90 active:scale-[0.99] disabled:bg-muted disabled:text-muted-foreground text-slate-950 font-bold font-sans tracking-wide text-xs rounded-xl transition-all duration-200 shadow-md shadow-brass/10 flex items-center justify-center gap-2 cursor-pointer select-none"
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