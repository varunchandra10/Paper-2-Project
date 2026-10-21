import type { MascotPose } from './mascotAssetRegistry';

export interface FullAnimationMeta {
  animId: string;
  frameCount: number;
  frameDurationMs: number;
  fps: number;
  spritesheetUrl: string;
  isLoop: boolean;
}

export const FULL_MASCOT_ANIMATIONS: Record<string, Record<string, FullAnimationMeta>> = {
  'mr-nerdy': {
    blinking: {
      animId: 'blinking',
      frameCount: 6,
      frameDurationMs: 400,
      fps: 2.5,
      spritesheetUrl: '/mascots/mr_nerdy/blinking/spritesheet.png',
      isLoop: true,
    },
    confused: {
      animId: 'confused',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/mr_nerdy/confused/spritesheet.png',
      isLoop: true,
    },
    doc_catching: {
      animId: 'doc_catching',
      frameCount: 9,
      frameDurationMs: 110,
      fps: 9.1,
      spritesheetUrl: '/mascots/mr_nerdy/doc_catching/spritesheet.png',
      isLoop: false,
    },
    excited: {
      animId: 'excited',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/mr_nerdy/excited/spritesheet.png',
      isLoop: true,
    },
    huncing: {
      animId: 'huncing',
      frameCount: 17,
      frameDurationMs: 141,
      fps: 7.1,
      spritesheetUrl: '/mascots/mr_nerdy/huncing/spritesheet.png',
      isLoop: true,
    },
    mad: {
      animId: 'mad',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/mr_nerdy/mad/spritesheet.png',
      isLoop: true,
    },
    peeking: {
      animId: 'peeking',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/mr_nerdy/peeking/spritesheet.png',
      isLoop: true,
    },
    sleeping: {
      animId: 'sleeping',
      frameCount: 16,
      frameDurationMs: 150,
      fps: 6.7,
      spritesheetUrl: '/mascots/mr_nerdy/sleeping/spritesheet.png',
      isLoop: false, // Transitions 0 to 15 and rests on frame 15
    },
    thinking: {
      animId: 'thinking',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/mr_nerdy/thinking/spritesheet.png',
      isLoop: true,
    },
    turnaround: {
      animId: 'turnaround',
      frameCount: 12,
      frameDurationMs: 200,
      fps: 5.0,
      spritesheetUrl: '/mascots/mr_nerdy/turnaround/spritesheet.png',
      isLoop: true,
    },
    walking: {
      animId: 'walking',
      frameCount: 16,
      frameDurationMs: 150,
      fps: 6.7,
      spritesheetUrl: '/mascots/mr_nerdy/walking/spritesheet.png',
      isLoop: true,
    },
    waving_hii: {
      animId: 'waving_hii',
      frameCount: 8,
      frameDurationMs: 110,
      fps: 9.1,
      spritesheetUrl: '/mascots/mr_nerdy/waving_hii/spritesheet.png',
      isLoop: false,
    },
  },
  'ms-nerdy': {
    blinking: {
      animId: 'blinking',
      frameCount: 6,
      frameDurationMs: 400,
      fps: 2.5,
      spritesheetUrl: '/mascots/ms_nerdy/blinking/spritesheet.png',
      isLoop: true,
    },
    confused: {
      animId: 'confused',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/ms_nerdy/confused/spritesheet.png',
      isLoop: true,
    },
    doc_catching: {
      animId: 'doc_catching',
      frameCount: 8,
      frameDurationMs: 120,
      fps: 8.3,
      spritesheetUrl: '/mascots/ms_nerdy/doc_catching/spritesheet.png',
      isLoop: false,
    },
    excited: {
      animId: 'excited',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/ms_nerdy/excited/spritesheet.png',
      isLoop: true,
    },
    huncing: {
      animId: 'huncing',
      frameCount: 17,
      frameDurationMs: 141,
      fps: 7.1,
      spritesheetUrl: '/mascots/ms_nerdy/huncing/spritesheet.png',
      isLoop: true,
    },
    mad: {
      animId: 'mad',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/ms_nerdy/mad/spritesheet.png',
      isLoop: true,
    },
    peeking: {
      animId: 'peeking',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/ms_nerdy/peeking/spritesheet.png',
      isLoop: true,
    },
    sleeping: {
      animId: 'sleeping',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/ms_nerdy/sleeping/spritesheet.png',
      isLoop: false,
    },
    thinking: {
      animId: 'thinking',
      frameCount: 8,
      frameDurationMs: 300,
      fps: 3.3,
      spritesheetUrl: '/mascots/ms_nerdy/thinking/spritesheet.png',
      isLoop: true,
    },
    turnaround: {
      animId: 'turnaround',
      frameCount: 13,
      frameDurationMs: 185,
      fps: 5.4,
      spritesheetUrl: '/mascots/ms_nerdy/turnaround/spritesheet.png',
      isLoop: true,
    },
    walking: {
      animId: 'walking',
      frameCount: 26,
      frameDurationMs: 92,
      fps: 10.8,
      spritesheetUrl: '/mascots/ms_nerdy/walking/spritesheet.png',
      isLoop: true,
    },
    waving_hii: {
      animId: 'waving_hii',
      frameCount: 8,
      frameDurationMs: 110,
      fps: 9.1,
      spritesheetUrl: '/mascots/ms_nerdy/waving_hii/spritesheet.png',
      isLoop: false,
    },
  },
};

// Aliases for retro characters if selected
FULL_MASCOT_ANIMATIONS['mr-nerd'] = FULL_MASCOT_ANIMATIONS['mr-nerdy'];
FULL_MASCOT_ANIMATIONS['ms-nerd'] = FULL_MASCOT_ANIMATIONS['ms-nerdy'];

/**
 * Maps high-level MascotPose states to the corresponding full-spritesheet animation.
 */
export function getAnimationForPose(pose: MascotPose): { animKey: string; isStaticFrame0?: boolean } {
  switch (pose) {
    case 'standing':
      return { animKey: 'blinking', isStaticFrame0: true };
    case 'blinking':
      return { animKey: 'blinking' };
    case 'waving':
      return { animKey: 'waving_hii' };
    case 'hunching':
    case 'sipping_coffee':
    case 'tired':
      return { animKey: 'huncing' };
    case 'sleeping':
      return { animKey: 'sleeping' };
    case 'peeking':
      return { animKey: 'peeking' };
    case 'thinking':
      return { animKey: 'thinking' };
    case 'document_catching':
      return { animKey: 'doc_catching' };
    case 'confused':
      return { animKey: 'confused' };
    case 'excited':
      return { animKey: 'excited' };
    case 'angry':
      return { animKey: 'mad' };
    case 'walking':
      return { animKey: 'walking' };
    case 'turnaround':
      return { animKey: 'turnaround' };
    default:
      return { animKey: 'blinking', isStaticFrame0: true };
  }
}
