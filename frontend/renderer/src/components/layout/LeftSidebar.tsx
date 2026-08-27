import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { FiUser, FiPlus } from 'react-icons/fi';

import mrNerdyStandSleep from '../../assets/mr_nerdy_stand_sleep-removebg-preview.png';
import mrNerdyStandToExcite from '../../assets/mr_nerdy_stand_to_excite-removebg-preview.png';
import mrNerdStandToHunch from '../../assets/mr_nerd_stand_to_hunch-removebg-preview.png';

interface LeftSidebarProps {
  isMaximized: boolean;
  isOpen: boolean;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({ isMaximized, isOpen }) => {
  const { 
    resetAnalysis,
    isAnalyzing,
    activeMilestoneIndex,
    reportContent,
    username,
    setActiveView
  } = usePanelStore();

  const [isSleeping, setIsSleeping] = React.useState(false);
  const [displaySprite, setDisplaySprite] = React.useState(mrNerdyStandSleep);
  const [frameIndex, setFrameIndex] = React.useState(0);
  const prevSheetRef = React.useRef(mrNerdyStandSleep);
  const prevFrameRef = React.useRef(0);

  // Inactivity tracking (1 minute timeout for testing)
  React.useEffect(() => {
    if (!isMaximized || isAnalyzing) {
      setIsSleeping(false);
      return;
    }

    let idleTimeout: ReturnType<typeof setTimeout>;

    const resetIdleTimer = () => {
      setIsSleeping(false);
      clearTimeout(idleTimeout);
      
      if (isAnalyzing) return;

      idleTimeout = setTimeout(() => {
        setIsSleeping(true);
      }, 60000);
    };

    const events = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart'];
    events.forEach((event) => {
      window.addEventListener(event, resetIdleTimer);
    });

    resetIdleTimer();

    return () => {
      clearTimeout(idleTimeout);
      events.forEach((event) => {
        window.removeEventListener(event, resetIdleTimer);
      });
    };
  }, [isMaximized, isAnalyzing]);

  // Determine target sheet and frame based on state machine
  let targetSheet = mrNerdyStandSleep;
  let targetFrame = 0;

  if (reportContent) {
    targetSheet = mrNerdyStandToExcite;
    targetFrame = 2;
  } else if (isAnalyzing) {
    targetFrame = 2;
    if (activeMilestoneIndex >= 2) {
      targetSheet = mrNerdStandToHunch;
    } else {
      targetSheet = mrNerdyStandToExcite;
    }
  } else if (isSleeping) {
    targetSheet = mrNerdyStandSleep;
    targetFrame = 2; // Sleep pose
  } else {
    targetSheet = mrNerdyStandSleep;
    targetFrame = 0; // Stand pose
  }

  // Handle mascot transitions matching state machine
  React.useEffect(() => {
    const prevSheet = prevSheetRef.current;
    const prevFrame = prevFrameRef.current;
    const nextSheet = targetSheet;
    const nextFrame = targetFrame;

    prevSheetRef.current = nextSheet;
    prevFrameRef.current = nextFrame;

    if (prevSheet === nextSheet && prevFrame === nextFrame) return;

    const timeouts: ReturnType<typeof setTimeout>[] = [];

    // Case 1: Image sheet changed
    if (prevSheet !== nextSheet) {
      if (nextSheet !== mrNerdyStandSleep) {
        setDisplaySprite(nextSheet);
        setFrameIndex(0);

        const t1 = setTimeout(() => setFrameIndex(1), 150);
        const t2 = setTimeout(() => setFrameIndex(2), 300);
        timeouts.push(t1, t2);
      } else {
        setDisplaySprite(prevSheet);
        setFrameIndex(2);

        const t1 = setTimeout(() => setFrameIndex(1), 150);
        const t2 = setTimeout(() => setFrameIndex(0), 300);
        const t3 = setTimeout(() => {
          setDisplaySprite(mrNerdyStandSleep);
          if (nextFrame === 2) {
            setFrameIndex(0);
            const t4 = setTimeout(() => setFrameIndex(1), 150);
            const t5 = setTimeout(() => setFrameIndex(2), 300);
            timeouts.push(t4, t5);
          } else {
            setFrameIndex(0);
          }
        }, 450);
        timeouts.push(t1, t2, t3);
      }
    } 
    // Case 2: Same sheet, but target pose changed
    else {
      setDisplaySprite(nextSheet);
      if (prevFrame < nextFrame) {
        setFrameIndex(0);
        const t1 = setTimeout(() => setFrameIndex(1), 150);
        const t2 = setTimeout(() => setFrameIndex(2), 300);
        timeouts.push(t1, t2);
      } else {
        setFrameIndex(2);
        const t1 = setTimeout(() => setFrameIndex(1), 150);
        const t2 = setTimeout(() => setFrameIndex(0), 300);
        timeouts.push(t1, t2);
      }
    }

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, [targetSheet, targetFrame]);

  return (
    <aside
      className={`h-full flex flex-col bg-card/95 backdrop-blur-md z-20 select-none shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${
        !isMaximized 
          ? 'w-0 border-r-0' 
          : `${isOpen ? 'w-[260px]' : 'w-[64px]'} border-r border-border/40 shadow-xl`
      }`}
    >
      {/* ── Project Title & Logo ─────────────────────────── */}
      <div className={`border-b border-border/30 flex items-center shrink-0 ${isOpen ? 'px-4 h-14 gap-3' : 'px-0 h-14 justify-center'}`}>
        <div className="relative group cursor-pointer">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brass/20 to-brass/5 flex items-center justify-center font-serif text-sm font-bold text-brass border border-brass/30 shrink-0 shadow-[0_0_10px_rgba(212,175,55,0.1)] group-hover:border-brass/50 group-hover:shadow-[0_0_14px_rgba(212,175,55,0.2)] transition-all">
            S
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-brass animate-pulse" />
        </div>
        {isOpen && (
          <div className="flex flex-col">
            <h1 className="text-[11px] font-black tracking-[0.25em] font-mono bg-gradient-to-r from-brass via-brass/90 to-foreground text-transparent bg-clip-text leading-none">
              SYNTHEXIS
            </h1>
            <span className="text-[8px] font-mono text-muted-foreground tracking-wider mt-1">ANALYTICS ENGINE</span>
          </div>
        )}
      </div>

      {/* ── New Analysis Button ───────────────────────────── */}
      <div className={`border-b border-border/30 shrink-0 ${isOpen ? 'p-3' : 'p-2 flex justify-center'}`}>
        {isOpen ? (
          <button
            onClick={resetAnalysis}
            className="w-full group relative py-2 px-3 rounded-lg bg-brass/10 hover:bg-brass/20 border border-brass/20 hover:border-brass/40 text-[10px] font-mono tracking-wider font-bold text-brass uppercase transition-all duration-200 active:scale-[0.98] cursor-pointer flex items-center justify-center gap-2 shadow-[0_2px_8px_rgba(212,175,55,0.08)]"
          >
            <FiPlus className="text-xs transition-transform group-hover:rotate-90 duration-300" />
            <span>New Analysis</span>
          </button>
        ) : (
          <button
            onClick={resetAnalysis}
            title="New Analysis"
            className="w-10 h-10 rounded-lg bg-brass/10 hover:bg-brass/20 border border-brass/20 hover:border-brass/40 text-brass transition-all duration-200 active:scale-95 cursor-pointer flex items-center justify-center shadow-[0_2px_8px_rgba(212,175,55,0.08)]"
          >
            <FiPlus className="text-base" />
          </button>
        )}
      </div>

      {/* ── Middle Spacer ─────────────────────────────────── */}
      <div className="flex-1" />

      {/* ── Bottom: Mascot + Profile ──────────────────────── */}
      <div className={`border-t border-border/30 flex flex-col bg-background/40 shrink-0 ${isOpen ? 'p-3.5 gap-3' : 'p-2 gap-2.5 items-center'}`}>

        {/* Mascot Box */}
        {isOpen ? (
          <div className="w-full aspect-[4/3] rounded-xl border border-border/60 bg-gradient-to-b from-muted/40 to-muted/80 flex flex-col items-center justify-between p-2.5 relative overflow-hidden shadow-inner group">
            <div className="absolute inset-0 bg-gradient-to-b from-brass/5 via-transparent to-brass/5 pointer-events-none opacity-50" />
            
            {/* Status indicator badge */}
            <div className="w-full flex justify-between items-center z-10 px-1">
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-background/60 border border-border/40 text-[8px] font-mono text-muted-foreground backdrop-blur-sm">
                <span className={`w-1.5 h-1.5 rounded-full ${isAnalyzing ? 'bg-amber-400 animate-ping' : isSleeping ? 'bg-blue-400' : 'bg-emerald-400'}`} />
                {isAnalyzing ? 'THINKING' : isSleeping ? 'IDLE' : 'READY'}
              </span>

              {isSleeping && (
                <div className="flex items-center gap-0.5 pointer-events-none z-10">
                  <span className="text-[10px] font-bold text-brass/80 animate-bounce" style={{ animationDelay: '0s', animationDuration: '2s' }}>Z</span>
                  <span className="text-[8px] font-bold text-brass/60 animate-bounce" style={{ animationDelay: '0.4s', animationDuration: '2s' }}>z</span>
                  <span className="text-[6px] font-bold text-brass/40 animate-bounce" style={{ animationDelay: '0.8s', animationDuration: '2s' }}>z</span>
                </div>
              )}
            </div>

            <div
              className="h-[84px] aspect-[5/6] filter drop-shadow-[0_4px_8px_rgba(0,0,0,0.35)] shrink-0 transition-transform duration-300 group-hover:scale-105"
              style={{
                backgroundImage: `url(${displaySprite})`,
                backgroundSize: '300% 100%',
                backgroundPosition: `${(frameIndex * 100) / 2}% 0%`,
                backgroundRepeat: 'no-repeat',
              }}
            />

            <span className="text-[9px] font-mono font-black tracking-[0.2em] text-brass/90 uppercase shrink-0">
              Mr. Nerd
            </span>
          </div>
        ) : (
          /* Rail view mascot */
          <div 
            title={isSleeping ? 'Mr. Nerd (Sleeping)' : 'Mr. Nerd'}
            className="w-10 h-10 rounded-xl border border-border/60 bg-muted/60 relative overflow-hidden flex items-center justify-center shadow-inner hover:border-brass/30 transition-all cursor-pointer"
          >
            <div
              className="h-[34px] aspect-[5/6]"
              style={{
                backgroundImage: `url(${displaySprite})`,
                backgroundSize: '300% 100%',
                backgroundPosition: `${(frameIndex * 100) / 2}% 0%`,
                backgroundRepeat: 'no-repeat',
              }}
            />
          </div>
        )}

        {/* Profile Card */}
        {isOpen ? (
          <div 
            onClick={() => setActiveView('profile')}
            className="w-full flex items-center gap-3 p-2.5 rounded-xl border border-border/50 bg-muted/40 hover:bg-muted/80 hover:border-border/80 transition-all duration-200 cursor-pointer select-none group"
          >
            <div className="w-9 h-9 rounded-lg bg-brass/10 border border-brass/30 text-brass flex items-center justify-center font-mono shadow-[0_0_10px_rgba(212,175,55,0.1)] shrink-0 group-hover:scale-105 transition-transform">
              <FiUser className="text-base" />
            </div>
            <div className="flex flex-col items-start min-w-0 flex-1">
              <span className="text-xs font-bold tracking-wide text-foreground leading-tight truncate">{username || 'Varun'}</span>
              <span className="text-[9px] font-mono text-muted-foreground leading-none mt-1">Developer</span>
            </div>
          </div>
        ) : (
          /* Rail view profile */
          <div 
            onClick={() => setActiveView('profile')}
            title={`${username || 'Varun'} (Developer)`}
            className="w-10 h-10 rounded-xl bg-brass/10 border border-brass/30 text-brass flex items-center justify-center cursor-pointer hover:bg-brass/20 transition-all duration-200 shadow-[0_0_8px_rgba(212,175,55,0.08)] active:scale-95"
          >
            <FiUser className="text-base" />
          </div>
        )}
      </div>
    </aside>
  );
};