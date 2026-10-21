import React, { useRef, useEffect, useState } from 'react';
import type { AvatarId, MascotPose } from './mascotAssetRegistry';
import { FULL_MASCOT_ANIMATIONS, getAnimationForPose } from './fullMascotRegistry';

interface MascotCanvasPlayerProps {
  avatarId?: AvatarId;
  pose?: MascotPose;
  className?: string;
  style?: React.CSSProperties;
  onClick?: () => void;
  imageOverride?: string;
}

// Global in-memory image cache so spritesheets load once and render instantly with 0 flicker
const imageCache = new Map<string, HTMLImageElement>();

function getImage(src: string): Promise<HTMLImageElement> {
  if (imageCache.has(src)) {
    const cached = imageCache.get(src)!;
    if (cached.complete && cached.naturalWidth > 0) {
      return Promise.resolve(cached);
    }
  }

  return new Promise((resolve, reject) => {
    const img = new Image();
    img.src = src;
    img.onload = () => {
      imageCache.set(src, img);
      resolve(img);
    };
    img.onerror = (e) => reject(e);
  });
}

// Eagerly preload primary standing, greeting, and doc catching animations for instant seamless transitions
if (typeof window !== 'undefined') {
  getImage('/mascots/mr_nerdy/blinking/spritesheet.png').catch(() => {});
  getImage('/mascots/mr_nerdy/waving_hii/spritesheet.png').catch(() => {});
  getImage('/mascots/mr_nerdy/doc_catching/spritesheet.png').catch(() => {});
  getImage('/mascots/ms_nerdy/blinking/spritesheet.png').catch(() => {});
  getImage('/mascots/ms_nerdy/waving_hii/spritesheet.png').catch(() => {});
  getImage('/mascots/ms_nerdy/doc_catching/spritesheet.png').catch(() => {});
}

// Centered viewport dimensions (crops out empty side margins so character size matches 225:369)
const CROP_WIDTH = 450;
const CROP_HEIGHT = 740;
const CROP_OFFSET_X = 95; // (640 - 450) / 2 = 95px centered on 320 anchor

export const MascotCanvasPlayer: React.FC<MascotCanvasPlayerProps> = ({
  avatarId = 'mr-nerdy',
  pose = 'standing',
  className = '',
  style = {},
  onClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const normalizedChar = avatarId === 'ms-nerdy' ? 'ms-nerdy' : 'mr-nerdy';

  const animInfo = getAnimationForPose(pose);
  const charAnims = FULL_MASCOT_ANIMATIONS[normalizedChar] || FULL_MASCOT_ANIMATIONS['mr-nerdy'];
  const animMeta = charAnims[animInfo.animKey] || charAnims['blinking'];

  const [loadedImage, setLoadedImage] = useState<HTMLImageElement | null>(() => {
    const cached = imageCache.get(animMeta.spritesheetUrl);
    return cached && cached.complete && cached.naturalWidth > 0 ? cached : null;
  });

  // Preload and cache spritesheet on pose / avatar change
  useEffect(() => {
    let isCurrent = true;
    getImage(animMeta.spritesheetUrl)
      .then((img) => {
        if (isCurrent) setLoadedImage(img);
      })
      .catch((err) => {
        console.warn(`[MascotCanvasPlayer] Failed to load spritesheet ${animMeta.spritesheetUrl}:`, err);
      });

    return () => {
      isCurrent = false;
    };
  }, [animMeta.spritesheetUrl]);

  // Synchronous image resolver: checks memory cache first to eliminate any 1-frame async gap
  const getActiveImage = (): HTMLImageElement | null => {
    const cached = imageCache.get(animMeta.spritesheetUrl);
    if (cached && cached.complete && cached.naturalWidth > 0) return cached;
    if (loadedImage && loadedImage.complete && loadedImage.naturalWidth > 0 && loadedImage.src.includes(animMeta.spritesheetUrl.replace(/^\//, ''))) {
      return loadedImage;
    }
    return null;
  };

  // High-performance canvas animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.imageSmoothingEnabled = false; // Sharp pixel-art rendering

    const masterFrameWidth = 640;
    const totalFrames = animMeta.frameCount;
    const frameDuration = animMeta.frameDurationMs || 250;

    // Handle static standing pose (frame 0)
    if (animInfo.isStaticFrame0) {
      const img = getActiveImage();
      if (img) {
        ctx.clearRect(0, 0, CROP_WIDTH, CROP_HEIGHT);
        ctx.drawImage(
          img,
          CROP_OFFSET_X,
          0,
          CROP_WIDTH,
          CROP_HEIGHT,
          0,
          0,
          CROP_WIDTH,
          CROP_HEIGHT
        );
      }
      return;
    }

    let rafId: number;
    let startTime = performance.now();

    const render = (now: number) => {
      const img = getActiveImage();
      if (!img) {
        rafId = requestAnimationFrame(render);
        return;
      }

      const elapsed = now - startTime;
      let frameIndex = 0;

      if (animMeta.isLoop) {
        frameIndex = Math.floor(elapsed / frameDuration) % totalFrames;
      } else {
        // One-shot animation: clamp to last frame and hold
        frameIndex = Math.min(Math.floor(elapsed / frameDuration), totalFrames - 1);
      }

      ctx.clearRect(0, 0, CROP_WIDTH, CROP_HEIGHT);
      ctx.drawImage(
        img,
        frameIndex * masterFrameWidth + CROP_OFFSET_X,
        0,
        CROP_WIDTH,
        CROP_HEIGHT,
        0,
        0,
        CROP_WIDTH,
        CROP_HEIGHT
      );

      rafId = requestAnimationFrame(render);
    };

    rafId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(rafId);
    };
  }, [loadedImage, animMeta, animInfo.isStaticFrame0]);

  return (
    <canvas
      ref={canvasRef}
      width={CROP_WIDTH}
      height={CROP_HEIGHT}
      onClick={onClick}
      className={`filter drop-shadow-[0_4px_12px_rgba(0,0,0,0.35)] shrink-0 overflow-hidden select-none pointer-events-auto ${className}`}
      style={{
        aspectRatio: `${CROP_WIDTH} / ${CROP_HEIGHT}`,
        imageRendering: 'pixelated',
        ...style,
      }}
    />
  );
};
