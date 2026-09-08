import React, { useState, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { 
  type AvatarId, 
  useMascotTransition, 
  MascotAnimatedSprite 
} from '../mascot/MascotCompanion';
import { IconMinimize, IconMaximize, IconMessageSquare } from '../ui/Icons';

interface MascotBoxProps {
  isOpen: boolean;
  isMaximized: boolean;
}

const GEN_Z_QUIPS = [
  "100% Local Ollama, zero cloud API bills 💅",
  "Bro parsed a 40-page arXiv paper in 8 seconds 💀",
  "AST Auto-healing just saved your thesis 🚀",
  "Feed me a 50-page PDF, I won't choke 🧠",
  "PyTorch tensors aligned and ready to train ⚡"
];

export const MascotBox: React.FC<MascotBoxProps> = ({ isOpen, isMaximized }) => {
  const { 
    isAnalyzing,
    activeMilestoneIndex,
    reportContent,
    avatarId
  } = usePanelStore();

  const [isSleeping, setIsSleeping] = useState(false);
  const [isBubbleVisible, setIsBubbleVisible] = useState(true);
  const [customQuote, setCustomQuote] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);

  // Inactivity tracking (1 minute idle timeout)
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

  // Consume central transition hook
  const activeAvatarId = (avatarId as AvatarId) || 'mr-nerdy';
  const {
    mascotInfo,
    currentPose,
    frameIndex,
    speechText
  } = useMascotTransition({
    avatarId: activeAvatarId,
    isAnalyzing,
    activeMilestoneIndex,
    reportContent,
    isSleeping
  });

  const handleMascotClick = () => {
    // Cycle playful quote on tap
    const randomQuip = GEN_Z_QUIPS[Math.floor(Math.random() * GEN_Z_QUIPS.length)];
    setCustomQuote(randomQuip);
    setIsBubbleVisible(true);
    setIsSleeping(false);
  };

  // On minimized / docked screen mode, do not render the mascot inside the renderer (the taskbar mascot overlay is active)
  if (!isMaximized) return null;

  /* Minimized Badge State */
  if (isMinimized) {
    return (
      <div 
        onClick={() => setIsMinimized(false)}
        className="flex items-center gap-2 p-2 rounded-xl border app-border bg-[var(--bg-card)]/90 backdrop-blur-md shadow-md cursor-pointer hover:border-[var(--accent)] transition-all group select-none"
        title={`Click to expand ${mascotInfo.name}`}
      >
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-[10px] font-mono font-bold text-[var(--accent)]">
          {mascotInfo.name}
        </span>
        <IconMaximize className="text-[10px] text-[var(--text-muted)] group-hover:text-[var(--text-main)] ml-1" />
      </div>
    );
  }

  /* Full Expanded Mascot Box */
  if (isOpen) {
    const bubbleContent = customQuote || speechText;

    return (
      <div className="relative flex flex-col items-center select-none">
        
        {/* Floating Speech Bubble with Pointer Tail */}
        {isBubbleVisible && (
          <div className="w-[136px] mb-2 px-2.5 py-1.5 rounded-xl bg-[var(--bg-card)]/95 border app-border text-[9px] font-sans text-[var(--text-main)] shadow-lg backdrop-blur-md flex items-start gap-1.5 relative animate-fade-in group">
            <IconMessageSquare className="text-[10px] text-[var(--accent)] shrink-0 mt-0.5" />
            <p className="flex-1 leading-tight select-text selection:bg-[var(--accent-subtle)] line-clamp-3 text-[8px]">
              {bubbleContent}
            </p>
            <button 
              onClick={(e) => { e.stopPropagation(); setIsBubbleVisible(false); }}
              className="text-[9px] text-[var(--text-muted)] hover:text-[var(--text-main)] ml-0.5 cursor-pointer shrink-0"
              title="Dismiss quote"
            >
              ✕
            </button>
            {/* Bubble Tail */}
            <div className="absolute -bottom-1 left-5 w-2 h-2 bg-[var(--bg-card)] border-b border-r app-border rotate-45" />
          </div>
        )}

        {/* Main Companion Box Frame - Compact Square (124px x 124px) */}
        <div 
          onClick={handleMascotClick}
          className="w-[124px] h-[124px] aspect-square shrink-0 rounded-2xl border app-border bg-[var(--bg-card)]/90 backdrop-blur-md flex flex-col items-center justify-between p-2 relative overflow-hidden shadow-lg group hover:border-[var(--accent)]/50 transition-all duration-200 cursor-pointer"
        >
          {/* Status Indicator Pill Header + Minimize Button */}
          <div className="w-full flex justify-between items-center z-10 px-0.5 pb-0.5">
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-[var(--bg-base)]/80 border app-border text-[7px] font-mono font-bold tracking-wider text-[var(--text-main)] backdrop-blur-sm shadow-xs">
              <span className={`w-1.5 h-1.5 rounded-full ${
                isAnalyzing 
                  ? 'bg-amber-400 animate-ping' 
                  : isSleeping 
                    ? 'bg-sky-400' 
                    : 'bg-emerald-400'
              }`} />
              {isAnalyzing ? 'ACTIVE' : isSleeping ? 'IDLE' : 'READY'}
            </span>

            <div className="flex items-center gap-1">
              {/* Floating Sleep Zzz's */}
              {isSleeping && (
                <div className="flex items-center gap-0.5 pointer-events-none mr-1">
                  <span className="text-[9px] font-mono font-bold text-[var(--accent)] animate-bounce" style={{ animationDelay: '0s', animationDuration: '1.8s' }}>Z</span>
                  <span className="text-[7px] font-mono font-bold text-[var(--accent)]/70 animate-bounce" style={{ animationDelay: '0.3s', animationDuration: '1.8s' }}>z</span>
                  <span className="text-[5px] font-mono font-bold text-[var(--accent)]/50 animate-bounce" style={{ animationDelay: '0.6s', animationDuration: '1.8s' }}>z</span>
                </div>
              )}

              {/* Minimize Box Button */}
              <button
                onClick={(e) => { e.stopPropagation(); setIsMinimized(true); }}
                className="w-4 h-4 rounded flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] transition-colors cursor-pointer"
                title="Minimize mascot box"
              >
                <IconMinimize className="text-[8px]" />
              </button>
            </div>
          </div>

          {/* Mascot Animated Sprite - Centered & Strictly Uncompressed */}
          <div className="flex-1 flex items-center justify-center w-full overflow-hidden my-0.5">
            <MascotAnimatedSprite
              avatarId={activeAvatarId}
              pose={currentPose}
              frameIndex={frameIndex}
              className="h-[74px] transition-transform duration-300 group-hover:scale-105"
            />
          </div>

          {/* Mascot Info Footer */}
          <div className="w-full flex items-center justify-between pt-1 border-t app-border text-[8px] font-mono">
            <span className="font-bold tracking-wider text-[var(--accent)] uppercase truncate max-w-[70px]">
              {mascotInfo.name}
            </span>
            <span className="text-[7px] text-[var(--text-muted)] uppercase tracking-wider truncate max-w-[50px]">
              {mascotInfo.role}
            </span>
          </div>
        </div>
      </div>
    );
  }

  /* Collapsed Rail View Mascot Badge */
  return (
    <div 
      title={`${mascotInfo.name} (${isSleeping ? 'Idle' : 'Active'})`}
      className="w-10 h-10 rounded-xl border app-border bg-[var(--bg-card)]/80 relative overflow-hidden flex items-center justify-center shadow-xs hover:border-[var(--accent)] transition-all duration-200 cursor-pointer group"
    >
      <MascotAnimatedSprite
        avatarId={activeAvatarId}
        pose={currentPose}
        frameIndex={frameIndex}
        className="h-[32px] transition-transform duration-200 group-hover:scale-110"
      />
    </div>
  );
};