import { MascotCanvasPlayer } from './MascotCanvasPlayer';
import React, { useState, useEffect } from 'react';
import { IconCheck } from '../ui/Icons';

import {
  type AvatarId,
  type MascotPose,
  type MascotInfo,
  MASCOT_REGISTRY,
  getMascotAsset
} from './mascotAssetRegistry';

export {
  type AvatarId,
  type MascotPose,
  type MascotInfo,
  MASCOT_REGISTRY,
  getMascotAsset
};

export interface UseMascotTransitionOptions {
  avatarId?: AvatarId;
  isAnalyzing?: boolean;
  activeMilestoneIndex?: number;
  reportContent?: string | null;
  isSleeping?: boolean;
  isTired?: boolean;
  isError?: boolean;
  isDraggingFile?: boolean;
  isChatGenerating?: boolean;
  isInputThinking?: boolean;
  isLongAnalyzing?: boolean;
  isJustUploaded?: boolean;
  isCoffeeSipping?: boolean;
  isIngestionSuccess?: boolean;
  isRateLimited?: boolean;
  customPoseOverride?: MascotPose | null;
  customSpeechOverride?: string | null;
}

/**
 * Custom React hook for unified mascot pose state machine transitions & frame stepping.
 * Supports:
 *  1) Wave greeting only on 1st panel open in session
 *  2) Inactivity: tired slump (45s) -> sleep on book with Zzz (60s)
 *  3) Catching document on PDF drop (800ms-1s) -> coffee sipping during ingestion
 *  4) Confused pose if parsing takes > 15s
 *  5) Hunching over laptop during ReACT query reasoning
 *  6) Peeking when input area is focused & blank for > 5s
 *  7) Excited celebration on verified ingestion (transient 3s)
 *  8) Angry reaction on rate limits or errors
 *  9) Subtle lifelike eye blinking during idle standing (every 12s)
 */
export function useMascotTransition({
  avatarId = 'mr-nerdy',
  isAnalyzing = false,
  isSleeping = false,
  isTired = false,
  isError = false,
  isDraggingFile = false,
  isChatGenerating = false,
  isInputThinking = false,
  isLongAnalyzing = false,
  isJustUploaded = false,
  isCoffeeSipping = false,
  isIngestionSuccess = false,
  isRateLimited = false,
  customPoseOverride = null,
  customSpeechOverride = null,
}: UseMascotTransitionOptions) {
  const info = MASCOT_REGISTRY[avatarId] || MASCOT_REGISTRY['mr-nerdy'];

  // Handwave greeting triggers every time the user opens / loads the application
  const [isFirstOpenWave, setIsFirstOpenWave] = useState<boolean>(true);

  // Finish initial greeting wave after single complete cycle and transition cleanly to standing idle
  useEffect(() => {
    if (isFirstOpenWave) {
      if (typeof window !== 'undefined' && (window as any).mascotAPI?.setMascotState) {
        (window as any).mascotAPI.setMascotState('wave-intro');
      }
      // Single smooth wave cycle (8 frames * 110ms = 880ms), resting naturally on frame 7 while pill is read
      const timer = setTimeout(() => {
        setIsFirstOpenWave(false);
        if (typeof window !== 'undefined' && (window as any).mascotAPI?.setMascotState) {
          (window as any).mascotAPI.setMascotState('idle');
        }
      }, 2200);
      return () => clearTimeout(timer);
    }
  }, [isFirstOpenWave]);

  // Periodic natural eye blinking when standing idle
  const [isBlinking, setIsBlinking] = useState(false);

  // Determine target pose and context quip (pills removed unless explicitly requested)
  let targetPose: MascotPose = 'standing';
  let speechText: string | null = null;

  if (customPoseOverride) {
    targetPose = customPoseOverride;
    speechText = customSpeechOverride || null;
  } else if (isDraggingFile || isJustUploaded) {
    targetPose = 'document_catching';
    speechText = null;
  } else if (isFirstOpenWave) {
    // Wave hand and say Hello researcher..! on app open
    targetPose = 'waving';
    speechText = 'Hello researcher..!';
  } else if (isRateLimited || isError) {
    targetPose = 'angry';
    speechText = null;
  } else if (isChatGenerating) {
    targetPose = 'hunching';
    speechText = null;
  } else if (isLongAnalyzing) {
    targetPose = 'confused';
    speechText = null;
  } else if (isCoffeeSipping || isAnalyzing) {
    targetPose = 'sipping_coffee';
    speechText = null;
  } else if (isIngestionSuccess) {
    targetPose = 'excited';
    speechText = null;
  } else if (isInputThinking) {
    targetPose = 'thinking';
    speechText = null;
  } else if (isSleeping) {
    targetPose = 'sleeping';
    speechText = null;
  } else if (isTired) {
    targetPose = 'tired';
    speechText = null;
  } else {
    targetPose = isBlinking ? 'blinking' : 'standing';
    speechText = null;
  }

  // Periodic blink timer (every 10 seconds when standing idle, plays full eye-blink cycle)
  useEffect(() => {
    if (targetPose !== 'standing' && targetPose !== 'blinking') {
      setIsBlinking(false);
      return;
    }

    const blinkInterval = setInterval(() => {
      setIsBlinking(true);
      setTimeout(() => {
        setIsBlinking(false);
      }, 1600);
    }, 10000);

    return () => clearInterval(blinkInterval);
  }, [targetPose]);

  // Frame index for legacy consumers (MascotCanvasPlayer drives high-precision RAF loops directly)
  const frameIndex = 1;

  const activeImage = info.poses[targetPose] || info.standingImage;

  return {
    mascotInfo: info,
    currentPose: targetPose,
    frameIndex,
    activeImage,
    speechText,
  };
}

/**
 * Full Multi-Frame Canvas Player Component (up to 26 frames).
 * Dynamically plays complete high-res sprite sheets with exact frame durations and zero compression.
 */
export const MascotAnimatedSprite: React.FC<{
  avatarId?: AvatarId;
  pose?: MascotPose;
  frameIndex?: number;
  className?: string;
  imageOverride?: string;
  onClick?: () => void;
  style?: React.CSSProperties;
}> = ({
  avatarId = 'mr-nerdy',
  pose = 'standing',
  className = '',
  onClick,
  style,
}) => {
  return (
    <MascotCanvasPlayer
      avatarId={avatarId}
      pose={pose}
      className={className}
      onClick={onClick}
      style={style}
    />
  );
};

export { MascotCanvasPlayer };

/**
 * Waist-Up Framed Standing Card Component for Developer Profile selection.
 */
export const MascotWaistUpCard: React.FC<{
  avatarId: AvatarId;
  isSelected: boolean;
  onClick: () => void;
}> = ({ avatarId, isSelected, onClick }) => {
  const info = MASCOT_REGISTRY[avatarId];
  if (!info) return null;

  return (
    <div
      onClick={onClick}
      className={`group rounded-xl border p-2 flex flex-col justify-between items-center text-center gap-1.5 transition-all duration-200 cursor-pointer select-none overflow-hidden relative h-full ${
        isSelected
          ? 'border-[var(--accent)] bg-[var(--accent-subtle)] shadow-md ring-2 ring-[var(--accent)]/50'
          : 'border app-border bg-[var(--bg-base)]/50 hover:bg-[var(--accent-subtle)]/40 hover:border-[var(--accent-border)]'
      }`}
    >
      {/* Mascot Waist-up Standing Image Window (Compact Height) */}
      <div className="w-full h-24 rounded-lg bg-white/90 border app-border relative overflow-hidden flex items-start justify-center pt-0.5 shadow-inner group-hover:scale-[1.02] transition-transform duration-200">
        <img
          src={info.standingImage}
          alt={info.name}
          className="h-38 w-auto max-w-none object-contain object-top transition-transform duration-300 group-hover:scale-105"
        />
        {isSelected && (
          <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-[var(--accent)] text-white rounded-full flex items-center justify-center text-[9px] font-black border border-white shadow-md z-10">
            <IconCheck />
          </span>
        )}
      </div>

      <div className="flex flex-col min-w-0 w-full pt-0.5">
        <span className={`text-[11px] font-bold leading-tight ${isSelected ? 'text-[var(--accent)]' : 'text-[var(--text-main)]'}`}>
          {info.name}
        </span>
        <span className="text-[8px] font-mono font-semibold text-[var(--accent)] uppercase tracking-wider mt-0.5 truncate">
          {info.role}
        </span>
        <span className="text-[8.5px] text-[var(--text-muted)] mt-0.5 leading-tight font-sans line-clamp-1">
          {info.description}
        </span>
      </div>
    </div>
  );
};
