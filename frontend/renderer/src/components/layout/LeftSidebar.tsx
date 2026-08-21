import React from 'react';
import { usePanelStore } from '../../store/panelStore';
import { FiUser } from 'react-icons/fi';

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
    reportContent
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

    let idleTimeout: any;

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

  // Handle mascot transitions exactly like mascot.js state machine (no micro-animations)
  React.useEffect(() => {
    const prevSheet = prevSheetRef.current;
    const prevFrame = prevFrameRef.current;
    const nextSheet = targetSheet;
    const nextFrame = targetFrame;

    prevSheetRef.current = nextSheet;
    prevFrameRef.current = nextFrame;

    if (prevSheet === nextSheet && prevFrame === nextFrame) return;

    const timeouts: any[] = [];

    // Case 1: Image sheet changed
    if (prevSheet !== nextSheet) {
      if (nextSheet !== mrNerdyStandSleep) {
        // Transitioning to action: Action sheet frame 0 -> 1 -> 2
        setDisplaySprite(nextSheet);
        setFrameIndex(0);

        const t1 = setTimeout(() => setFrameIndex(1), 150);
        const t2 = setTimeout(() => setFrameIndex(2), 300);
        timeouts.push(t1, t2);
      } else {
        // Transitioning back to standing/sleep: Action sheet frame 2 -> 1 -> 0 -> Standing sheet frame 0 (or 2 if sleeping)
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
    // Case 2: Same sheet, but target pose changed (e.g. stand 0 <-> sleep 2)
    else {
      setDisplaySprite(nextSheet);
      if (prevFrame < nextFrame) {
        // Falling asleep: 0 -> 1 -> 2
        setFrameIndex(0);
        const t1 = setTimeout(() => setFrameIndex(1), 150);
        const t2 = setTimeout(() => setFrameIndex(2), 300);
        timeouts.push(t1, t2);
      } else {
        // Waking up: 2 -> 1 -> 0
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

  if (!isMaximized) return null;

  return (
    <aside
      className={`h-full flex flex-col bg-card border-r border-border/60 z-20 select-none shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${
        isOpen ? 'w-[260px]' : 'w-[56px]'
      }`}
    >
      {/* ── Project Title ─────────────────────────────────── */}
      <div className={`border-b border-border/40 flex items-center shrink-0 ${isOpen ? 'px-4 py-3.5' : 'px-0 py-3.5 justify-center'}`}>
        {isOpen ? (
          <>
            <h1 className="text-[11px] font-black tracking-[0.2em] font-mono bg-gradient-to-r from-brass to-foreground text-transparent bg-clip-text leading-none">
              Paper_2_Project
            </h1>
          </>
        ) : (
          <span className="text-[11px] font-black font-mono text-brass/90 tracking-widest leading-none text-center">
            P_2_P
          </span>
        )}
      </div>

      {/* ── New Analysis Button ───────────────────────────── */}
      <div className={`border-b border-border/40 shrink-0 ${isOpen ? 'px-4 py-3' : 'px-2 py-3 flex justify-center'}`}>
        {isOpen ? (
          <button
            onClick={resetAnalysis}
            className="py-1.5 px-3 rounded-lg bg-brass/8 hover:bg-brass/15 text-[10px] font-mono tracking-wide font-bold text-brass uppercase transition-all duration-200 active:scale-95 cursor-pointer flex items-center gap-1.5"
          >
            <span className="text-[12px] leading-none">+</span> New Analysis
          </button>
        ) : (
          <button
            onClick={resetAnalysis}
            title="New Analysis"
            className="w-10 h-8 rounded-lg bg-brass/8 hover:bg-brass/15 text-brass transition-all duration-200 active:scale-95 cursor-pointer flex items-center justify-center"
          >
            <span className="text-[9px] font-mono uppercase tracking-wider font-bold">New</span>
          </button>
        )}
      </div>

      {/* ── Middle Spacer ─────────────────────────────────── */}
      <div className="flex-1" />

      {/* ── Bottom: Mascot + Profile ──────────────────────── */}
      <div className={`border-t border-border/40 flex flex-col bg-background/30 backdrop-blur-md shrink-0 ${isOpen ? 'p-4 gap-2.5' : 'p-2 gap-2 items-center'}`}>

        {/* Mascot box */}
        {isOpen ? (
          <div className="w-[148px] aspect-square mx-auto rounded-xl border border-border/50 bg-black/15 flex flex-col items-center justify-between p-2.5 relative overflow-hidden shadow-[inset_0_2px_8px_rgba(0,0,0,0.3)] mb-1 select-none">
            <div className="absolute inset-0 bg-gradient-to-b from-brass/5 to-transparent pointer-events-none opacity-30" />

            {isSleeping && (
              <div className="absolute top-2 right-4 flex flex-col gap-0.5 pointer-events-none z-10">
                <span className="text-[10px] font-bold text-brass/70 animate-bounce select-none" style={{ animationDelay: '0s', animationDuration: '2.5s' }}>Z</span>
                <span className="text-[7px] font-bold text-brass/55 animate-bounce select-none ml-1" style={{ animationDelay: '0.6s', animationDuration: '2.5s' }}>z</span>
                <span className="text-[6px] font-bold text-brass/40 animate-bounce select-none ml-2" style={{ animationDelay: '1.2s', animationDuration: '2.5s' }}>z</span>
              </div>
            )}

            <div className="flex-1" />
            <div
              className="h-[88px] aspect-[5/6] filter drop-shadow-[0_2px_6px_rgba(0,0,0,0.25)] shrink-0"
              style={{
                backgroundImage: `url(${displaySprite})`,
                backgroundSize: '300% 100%',
                backgroundPosition: `${(frameIndex * 100) / 2}% 0%`,
                backgroundRepeat: 'no-repeat',
              }}
            />
            <div className="flex-1" />
            <span className="text-[8px] font-mono font-black tracking-[0.25em] text-brass/90 uppercase shrink-0">
              Mr. Nerd
            </span>
          </div>
        ) : (
          /* Icon-rail mascot — tiny sprite only */
          <div className="w-10 h-10 rounded-lg border border-border/40 bg-black/15 relative overflow-hidden flex items-center justify-center shadow-[inset_0_1px_4px_rgba(0,0,0,0.3)]">
            <div
              className="h-[36px] aspect-[5/6]"
              style={{
                backgroundImage: `url(${displaySprite})`,
                backgroundSize: '300% 100%',
                backgroundPosition: `${(frameIndex * 100) / 2}% 0%`,
                backgroundRepeat: 'no-repeat',
              }}
            />
          </div>
        )}

        {/* Profile row */}
        {isOpen ? (
          <div className="w-full flex items-center gap-3.5 p-3.5 rounded-xl border border-border/50 bg-black/10 hover:bg-foreground/5 hover:border-border/70 transition-all duration-300 cursor-pointer select-none">
            <div className="w-10 h-10 rounded-full bg-brass/10 border border-brass/35 text-brass flex items-center justify-center font-mono shadow-[0_0_8px_rgba(212,175,55,0.1)] shrink-0">
              <FiUser className="text-lg" />
            </div>
            <div className="flex flex-col items-start min-w-0">
              <span className="text-xs font-black tracking-wide text-foreground/80 leading-none">Varun</span>
              <span className="text-[10px] font-mono text-foreground/40 leading-none mt-1.5">Developer</span>
            </div>
          </div>
        ) : (
          /* Icon-rail profile — avatar only */
          <div className="w-10 h-10 rounded-full bg-brass/10 border border-brass/35 text-brass flex items-center justify-center cursor-pointer hover:bg-brass/20 transition-all duration-200 shadow-[0_0_8px_rgba(212,175,55,0.08)]">
            <FiUser className="text-base" />
          </div>
        )}
      </div>
    </aside>
  );
};
