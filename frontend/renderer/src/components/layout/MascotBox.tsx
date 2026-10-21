import React, { useState, useEffect, useRef } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { 
  type AvatarId, 
  type MascotPose,
  useMascotTransition, 
  MascotAnimatedSprite 
} from '../mascot/MascotCompanion';
import { IconMinimize, IconMaximize, IconMessageSquare } from '../ui/Icons';

interface MascotBoxProps {
  isOpen: boolean;
  isMaximized: boolean;
  isDragging?: boolean;
}

export const MascotBox: React.FC<MascotBoxProps> = ({ isOpen, isMaximized, isDragging = false }) => {
  const { 
    isAnalyzing,
    activeMilestoneIndex,
    reportContent,
    avatarId,
    isChatGenerating,
    isInputThinking,
    analysisStatus,
    messages
  } = usePanelStore();

  const [isSleeping, setIsSleeping] = useState(false);
  const [isTired, setIsTired] = useState(false);
  const isBubbleVisible = true;
  const [isMinimized, setIsMinimized] = useState(false);

  // Inactivity tracking (45s tired slump -> 60s sleep with Zzz)
  useEffect(() => {
    let tiredTimeout: ReturnType<typeof setTimeout>;
    let sleepTimeout: ReturnType<typeof setTimeout>;

    const resetIdleTimer = () => {
      setIsSleeping(false);
      setIsTired(false);
      clearTimeout(tiredTimeout);
      clearTimeout(sleepTimeout);
      
      if (isAnalyzing || isChatGenerating) return;

      tiredTimeout = setTimeout(() => {
        setIsTired(true);
        if (typeof window !== 'undefined' && (window as any).mascotAPI?.setMascotState) {
          (window as any).mascotAPI.setMascotState('tired');
        }
      }, 45000);

      sleepTimeout = setTimeout(() => {
        setIsTired(false);
        setIsSleeping(true);
        if (typeof window !== 'undefined' && (window as any).mascotAPI?.setMascotState) {
          (window as any).mascotAPI.setMascotState('sleep');
        }
      }, 60000);
    };

    const events = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart'];
    const handleEvent = () => resetIdleTimer();

    events.forEach((event) => {
      window.addEventListener(event, handleEvent);
    });

    resetIdleTimer();

    return () => {
      clearTimeout(tiredTimeout);
      clearTimeout(sleepTimeout);
      events.forEach((event) => {
        window.removeEventListener(event, handleEvent);
      });
    };
  }, [isAnalyzing, isChatGenerating]);

  // Robust PDF Upload & Ingestion State Machine:
  // Phase 1: Document catching (1000ms)
  // Phase 2: Coffee sipping (guaranteed 3.5s minimum while analyzing/digesting)
  // Phase 3: Prolonged ingestion (>15s) -> confused
  // Phase 4: Ingestion success -> excited celebration (2.5s)
  // Phase 5: Smooth return to standing / idle
  const [isJustUploaded, setIsJustUploaded] = useState(false);
  const [isCoffeeSipping, setIsCoffeeSipping] = useState(false);
  const [isLongAnalyzing, setIsLongAnalyzing] = useState(false);
  const [isIngestionSuccess, setIsIngestionSuccess] = useState(false);

  const prevAnalyzingRef = useRef(false);
  const activeTimeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearIngestionTimeouts = () => {
    activeTimeoutsRef.current.forEach((t) => clearTimeout(t));
    activeTimeoutsRef.current = [];
  };

  useEffect(() => {
    // Only trigger sequence on the rising edge of isAnalyzing
    if (isAnalyzing && !prevAnalyzingRef.current) {
      clearIngestionTimeouts();

      setIsJustUploaded(true);
      setIsCoffeeSipping(false);
      setIsIngestionSuccess(false);

      if (typeof window !== 'undefined' && (window as any).mascotAPI?.setMascotState) {
        (window as any).mascotAPI.setMascotState('catching');
      }

      // Step 1: 1.0s of document catching
      const t1 = setTimeout(() => {
        setIsJustUploaded(false);
        setIsCoffeeSipping(true);

        if (typeof window !== 'undefined' && (window as any).mascotAPI?.setMascotState) {
          (window as any).mascotAPI.setMascotState('having_sipping');
        }

        // Step 2: 3.5s of coffee sipping
        const t2 = setTimeout(() => {
          setIsCoffeeSipping(false);

          // Step 3: Verified celebration
          setIsIngestionSuccess(true);
          if (typeof window !== 'undefined' && (window as any).mascotAPI?.setMascotState) {
            (window as any).mascotAPI.setMascotState('excited');
          }

          // Step 4: Return to normal idle
          const t3 = setTimeout(() => {
            setIsIngestionSuccess(false);
            if (typeof window !== 'undefined' && (window as any).mascotAPI?.setMascotState) {
              (window as any).mascotAPI.setMascotState('idle');
            }
          }, 2500);
          activeTimeoutsRef.current.push(t3);

        }, 3500);
        activeTimeoutsRef.current.push(t2);

      }, 1000);
      activeTimeoutsRef.current.push(t1);
    }

    prevAnalyzingRef.current = isAnalyzing;
  }, [isAnalyzing]);

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      clearIngestionTimeouts();
    };
  }, []);

  // Prolonged ingestion (> 15 seconds) -> confused pose
  useEffect(() => {
    if (!isAnalyzing) {
      setIsLongAnalyzing(false);
      return;
    }

    const timer = setTimeout(() => {
      setIsLongAnalyzing(true);
      if (typeof window !== 'undefined' && (window as any).mascotAPI?.setMascotState) {
        (window as any).mascotAPI.setMascotState('confused');
      }
    }, 15000);

    return () => clearTimeout(timer);
  }, [isAnalyzing]);

  // Check for rate limit or error in last assistant message
  const lastMessage = messages[messages.length - 1];
  const isRateLimited = 
    analysisStatus === 'error' ||
    (lastMessage && lastMessage.role === 'assistant' && (
      lastMessage.content.includes('429') ||
      lastMessage.content.includes('rate limit') ||
      lastMessage.content.includes('⚠️')
    ));

  // Click Easter Egg state
  const [clickPoseOverride, setClickPoseOverride] = useState<MascotPose | null>(null);

  const handleMascotClick = () => {
    setIsSleeping(false);
    setIsTired(false);

    // Cycle playful poses on click without popping up unnecessary text pills
    const poses: MascotPose[] = ['document_catching', 'waving', 'excited', 'thinking', 'turnaround', 'confused', 'sipping_coffee', 'angry', 'walking'];
    const chosenPose = poses[Math.floor(Math.random() * poses.length)];
    
    const overrideDuration = (chosenPose === 'waving' || chosenPose === 'document_catching') ? 1100 : 2500;
    setClickPoseOverride(chosenPose);
    setTimeout(() => {
      setClickPoseOverride(null);
    }, overrideDuration);
  };

  // Consume central transition hook with all integrated triggers
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
    isSleeping,
    isTired,
    isChatGenerating,
    isInputThinking,
    isLongAnalyzing,
    isDraggingFile: isDragging,
    isJustUploaded,
    isCoffeeSipping,
    isIngestionSuccess,
    isRateLimited: !!isRateLimited,
    customPoseOverride: clickPoseOverride,
    customSpeechOverride: null
  });

  // In Electron native minimized overlay mode, let the external window handle the mascot
  // Allowed to render within the in-panel dock for both minimized & maximized screens

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
    const bubbleContent = speechText;

    return (
      <div className="flex flex-col items-center select-none relative group/mascot">
        {/* Dynamic Speech Bubble (Only shown when a message pill is explicitly active) */}
        {isBubbleVisible && !!bubbleContent && (
          <div className={`relative mb-1.5 bg-[var(--bg-card)]/95 backdrop-blur-md border app-border rounded-2xl shadow-lg animate-fade-in group-hover/mascot:border-[var(--accent-border)] transition-colors ${
            isMaximized
              ? 'max-w-[200px] p-2'
              : 'max-w-[155px] p-1.5'
          }`}>
            <div className="flex items-start gap-1.5">
              <IconMessageSquare className={`text-[var(--accent)] shrink-0 mt-0.5 ${
                isMaximized ? 'w-3.5 h-3.5' : 'w-3 h-3'
              }`} />
              <p className={`font-sans leading-tight text-[var(--text-main)] ${
                isMaximized ? 'text-[11px]' : 'text-[9.5px]'
              }`}>
                {bubbleContent}
              </p>
            </div>

            {/* Speech bubble tail pointer */}
            <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-2.5 h-2.5 bg-[var(--bg-card)] border-r border-b app-border rotate-45" />
          </div>
        )}

        {/* Mascot Interactive Sprite Area */}
        <div 
          onClick={handleMascotClick}
          className="relative cursor-pointer transition-transform duration-200 active:scale-95 hover:scale-105"
          title={`Click to interact with ${mascotInfo.name}`}
        >
          <MascotAnimatedSprite
            avatarId={activeAvatarId}
            pose={currentPose}
            frameIndex={frameIndex}
            className="w-19 h-auto"
          />

          {/* Quick minimize button on top-right of sprite */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsMinimized(true);
            }}
            className="absolute -top-1 -right-1 w-4.5 h-4.5 rounded-full bg-[var(--bg-card)]/80 border app-border text-[var(--text-muted)] hover:text-[var(--text-main)] flex items-center justify-center opacity-0 group-hover/mascot:opacity-100 transition-opacity shadow-xs"
            title="Minimize mascot"
          >
            <IconMinimize className="w-2.5 h-2.5" />
          </button>
        </div>
      </div>
    );
  }

  return null;
};