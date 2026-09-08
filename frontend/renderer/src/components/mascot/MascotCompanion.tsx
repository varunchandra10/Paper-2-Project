import React, { useState, useEffect, useRef } from 'react';
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
  isError?: boolean;
  isDraggingFile?: boolean;
}

/**
 * Custom React hook for unified mascot pose state machine transitions & frame stepping.
 */
export function useMascotTransition({
  avatarId = 'mr-nerdy',
  isAnalyzing = false,
  activeMilestoneIndex = 0,
  reportContent = null,
  isSleeping = false,
  isError = false,
  isDraggingFile = false
}: UseMascotTransitionOptions) {
  const info = MASCOT_REGISTRY[avatarId] || MASCOT_REGISTRY['mr-nerdy'];

  let targetPose: MascotPose = 'standing';
  let speechText = 'Standing by for research paper ingestion.';

  if (isDraggingFile) {
    targetPose = 'document_catching';
    speechText = 'Drop the PDF right here! Ingesting layout elements...';
  } else if (isError) {
    targetPose = 'angry';
    speechText = 'Pipeline exception encountered! Checking AST syntax errors.';
  } else if (reportContent) {
    targetPose = 'excited';
    speechText = 'PyTorch model synthesis completed successfully!';
  } else if (isAnalyzing) {
    if (activeMilestoneIndex >= 3) {
      targetPose = 'hunching';
      speechText = 'Synthesizing PyTorch modules & running AST reflexion...';
    } else if (activeMilestoneIndex >= 1) {
      targetPose = 'thinking';
      speechText = 'Extracting hyperparameters & Tavily groundings...';
    } else {
      targetPose = 'peeking';
      speechText = 'Parsing PDF layout structure & arXiv headers...';
    }
  } else if (isSleeping) {
    targetPose = 'sleeping';
    speechText = 'Zzz... Idle state. Drop a paper or ask a question to wake me!';
  } else {
    targetPose = 'standing';
    speechText = `Ready to assist! Selected avatar: ${info.name}.`;
  }

  const [currentPose, setCurrentPose] = useState<MascotPose>(targetPose);
  const [frameIndex, setFrameIndex] = useState<number>(0);

  const prevPoseRef = useRef<MascotPose>(targetPose);

  useEffect(() => {
    const prevPose = prevPoseRef.current;
    prevPoseRef.current = targetPose;

    if (prevPose === targetPose) return;

    setCurrentPose(targetPose);
    setFrameIndex(0);

    const t1 = setTimeout(() => setFrameIndex(1), 150);
    const t2 = setTimeout(() => setFrameIndex(2), 300);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [targetPose]);

  const activeImage = info.poses[currentPose] || info.standingImage;

  return {
    mascotInfo: info,
    currentPose,
    frameIndex,
    activeImage,
    speechText,
  };
}

/**
 * Animated Mascot Sprite Component - 3 Horizontal Frame Slicing.
 * Preserves exact natural 225:369 aspect ratio with zero compression.
 */
export const MascotAnimatedSprite: React.FC<{
  avatarId?: AvatarId;
  pose?: MascotPose;
  frameIndex?: number;
  className?: string;
  imageOverride?: string;
}> = ({
  avatarId = 'mr-nerdy',
  pose = 'standing',
  frameIndex = 0,
  className = '',
  imageOverride
}) => {
  const info = MASCOT_REGISTRY[avatarId] || MASCOT_REGISTRY['mr-nerdy'];
  const spriteImage = imageOverride || info.poses[pose] || info.standingImage;
  const isStanding = pose === 'standing';
  // Standing PNG assets have the character centered in Frame 1 (middle of 3 frames)
  const effectiveFrame = isStanding ? 1 : Math.min(Math.max(frameIndex, 0), 2);

  return (
    <div
      className={`filter drop-shadow-[0_4px_12px_rgba(0,0,0,0.35)] shrink-0 overflow-hidden ${className}`}
      style={{
        aspectRatio: '225 / 369',
        backgroundImage: `url(${spriteImage})`,
        backgroundSize: '300% 100%',
        backgroundPosition: `${effectiveFrame * 50}% 0%`,
        backgroundRepeat: 'no-repeat',
      }}
    />
  );
};

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
