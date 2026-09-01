import React, { useState, useEffect, useRef } from 'react';
import { usePanelStore } from '../../store/panelStore';

import mrNerdyStandSleep from '../../assets/mr_nerdy_stand_sleep-removebg-preview.png';
import mrNerdyStandToExcite from '../../assets/mr_nerdy_stand_to_excite-removebg-preview.png';
import mrNerdStandToHunch from '../../assets/mr_nerd_stand_to_hunch-removebg-preview.png';

interface MascotBoxProps {
  isOpen: boolean;
  isMaximized: boolean;
}

export const MascotBox: React.FC<MascotBoxProps> = ({ isOpen, isMaximized }) => {
  const { 
    isAnalyzing,
    activeMilestoneIndex,
    reportContent
  } = usePanelStore();

  const [isSleeping, setIsSleeping] = useState(false);
  const [displaySprite, setDisplaySprite] = useState(mrNerdyStandSleep);
  const [frameIndex, setFrameIndex] = useState(0);
  const prevSheetRef = useRef(mrNerdyStandSleep);
  const prevFrameRef = useRef(0);

  // Inactivity tracking (1 minute timeout for testing)
  useEffect(() => {
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
    const handleEvent = () => resetIdleTimer();

    events.forEach((event) => {
      window.addEventListener(event, handleEvent);
    });

    resetIdleTimer();

    return () => {
      clearTimeout(idleTimeout);
      events.forEach((event) => {
        window.removeEventListener(event, handleEvent);
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
  useEffect(() => {
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

  /* Expanded Drawer Mascot Container */
  if (isOpen) {
    return (
      <div className="w-full aspect-[4/3] rounded-2xl border border-border/60 bg-card/80 flex flex-col items-center justify-between p-2.5 relative overflow-hidden shadow-sm group select-none">
        {/* HUD Frame Brackets */}
        <div className="absolute top-2 left-2 w-2 h-2 border-t border-l border-brass/50 pointer-events-none" />
        <div className="absolute top-2 right-2 w-2 h-2 border-t border-r border-brass/50 pointer-events-none" />
        <div className="absolute bottom-2 left-2 w-2 h-2 border-b border-l border-brass/50 pointer-events-none" />
        <div className="absolute bottom-2 right-2 w-2 h-2 border-b border-r border-brass/50 pointer-events-none" />

        {/* Status Indicator Pill Header */}
        <div className="w-full flex justify-between items-center z-10 px-1">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-background/80 border border-border/50 text-[8px] font-mono font-bold tracking-wider text-foreground backdrop-blur-sm shadow-xs">
            <span className={`w-1.5 h-1.5 rounded-full ${
              isAnalyzing 
                ? 'bg-inferred animate-ping' 
                : isSleeping 
                  ? 'bg-synthesis' 
                  : 'bg-confirmed'
            }`} />
            {isAnalyzing ? 'SYNTHESIZING' : isSleeping ? 'IDLE' : 'READY'}
          </span>

          {/* Floating Sleep Zzz's */}
          {isSleeping && (
            <div className="flex items-center gap-0.5 pointer-events-none z-10">
              <span className="text-[10px] font-mono font-bold text-brass/90 animate-bounce" style={{ animationDelay: '0s', animationDuration: '1.8s' }}>Z</span>
              <span className="text-[8px] font-mono font-bold text-brass/70 animate-bounce" style={{ animationDelay: '0.3s', animationDuration: '1.8s' }}>z</span>
              <span className="text-[6px] font-mono font-bold text-brass/50 animate-bounce" style={{ animationDelay: '0.6s', animationDuration: '1.8s' }}>z</span>
            </div>
          )}
        </div>

        {/* Mascot Animated Sprite */}
        <div
          className="h-[84px] aspect-[5/6] filter drop-shadow-[0_4px_12px_rgba(0,0,0,0.4)] shrink-0 transition-transform duration-300 group-hover:scale-105"
          style={{
            backgroundImage: `url(${displaySprite})`,
            backgroundSize: '300% 100%',
            backgroundPosition: `${(frameIndex * 100) / 2}% 0%`,
            backgroundRepeat: 'no-repeat',
          }}
        />

        {/* Mascot Name Badge */}
        <span className="text-[9px] font-mono font-bold tracking-[0.22em] text-brass uppercase shrink-0">
          Mr. Nerdy
        </span>
      </div>
    );
  }

  /* Collapsed Rail View Mascot Badge */
  return (
    <div 
      title={isSleeping ? 'Mr. Nerdy (Idle)' : 'Mr. Nerdy'}
      className="w-10 h-10 rounded-xl border border-border/60 bg-card/80 relative overflow-hidden flex items-center justify-center shadow-xs hover:border-brass/50 hover:shadow-[0_0_12px_rgba(212,163,56,0.18)] transition-all duration-200 cursor-pointer group"
    >
      <div
        className="h-[34px] aspect-[5/6] transition-transform duration-200 group-hover:scale-110"
        style={{
          backgroundImage: `url(${displaySprite})`,
          backgroundSize: '300% 100%',
          backgroundPosition: `${(frameIndex * 100) / 2}% 0%`,
          backgroundRepeat: 'no-repeat',
        }}
      />
    </div>
  );
};