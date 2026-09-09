"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { SectionHeading } from "../ui/SectionHeading";
import { Badge } from "../ui/Badge";
import { 
  Volume2, 
  Play, 
  Square, 
  Repeat,
  ChevronDown
} from "lucide-react";
import { getAssetPath } from "@/lib/basePath";

export type AvatarId = "mr-nerdy" | "ms-nerdy" | "mr-nerd" | "ms-nerd";

export interface MascotInfo {
  id: AvatarId;
  label: string;
  name: string;
  role: string;
  gender: string;
  avatarThumb: string;
  sheets: {
    standing: string;
    angry: string;
    blinking: string;
    coffee_sipping: string;
    confused: string;
    document_catching: string;
    excited: string;
    huncing: string;
    peeking: string;
    sleeping: string;
    thinking: string;
    tired: string;
    waving: string;
  };
}

export const MASCOTS: Record<AvatarId, MascotInfo> = {
  "mr-nerdy": {
    id: "mr-nerdy",
    label: "Mascot 1",
    name: "Mr. Nerdy",
    role: "Autonomous Research Companion",
    gender: "Male",
    avatarThumb: "/mascots/mr_nerdy/mr_nerdy_standing.png",
    sheets: {
      standing: "/mascots/mr_nerdy/mr_nerdy_standing.png",
      angry: "/mascots/mr_nerdy/mr_nerdy_angry.png",
      blinking: "/mascots/mr_nerdy/mr_nerdy_eye_blinking.png",
      coffee_sipping: "/mascots/mr_nerdy/mr_nerdy_having_sipping.png",
      confused: "/mascots/mr_nerdy/mr_nerdy_confused.png",
      document_catching: "/mascots/mr_nerdy/mr_nerdy_document_catching.png",
      excited: "/mascots/mr_nerdy/mr_nerdy_excited.png",
      huncing: "/mascots/mr_nerdy/mr_nerdy_huncing.png",
      peeking: "/mascots/mr_nerdy/mr_nerdy_peeking.png",
      sleeping: "/mascots/mr_nerdy/mr_nerdy_sleeping.png",
      thinking: "/mascots/mr_nerdy/mr_nerdy_thinking.png",
      tired: "/mascots/mr_nerdy/mr_nerdy_tired.png",
      waving: "/mascots/mr_nerdy/mr_nerdy_waving.png",
    },
  },
  "ms-nerdy": {
    id: "ms-nerdy",
    label: "Mascot 2",
    name: "Ms. Nerdy",
    role: "Autonomous Research Companion",
    gender: "Female",
    avatarThumb: "/mascots/ms_nerdy/ms_nerdy_standing.png",
    sheets: {
      standing: "/mascots/ms_nerdy/ms_nerdy_standing.png",
      angry: "/mascots/ms_nerdy/ms_nerdy_angry.png",
      blinking: "/mascots/ms_nerdy/ms_nerdy_blinking.png",
      coffee_sipping: "/mascots/ms_nerdy/ms_nerdy_sipping_coffee.png",
      confused: "/mascots/ms_nerdy/ms_nerdy_confused.png",
      document_catching: "/mascots/ms_nerdy/ms_nerdy_document_catching.png",
      excited: "/mascots/ms_nerdy/ms_nerdy_excited.png",
      huncing: "/mascots/ms_nerdy/ms_nerdy_hunching.png",
      peeking: "/mascots/ms_nerdy/ms_nerdy_peeking.png",
      sleeping: "/mascots/ms_nerdy/ms_nerdy_sleeping.png",
      thinking: "/mascots/ms_nerdy/ms_nerdy_thinking.png",
      tired: "/mascots/ms_nerdy/ms_nerdy_tired.png",
      waving: "/mascots/ms_nerdy/ms_nerdy_hand_waving.png",
    },
  },
  "mr-nerd": {
    id: "mr-nerd",
    label: "Mascot 3",
    name: "Mr. Nerd",
    role: "Senior Engineering Specialist",
    gender: "Male",
    avatarThumb: "/mascots/mr_nerd/mr_nerd_standing.png",
    sheets: {
      standing: "/mascots/mr_nerd/mr_nerd_standing.png",
      angry: "/mascots/mr_nerd/mr_nerd_angry.png",
      blinking: "/mascots/mr_nerd/mr_nerd_blinking.png",
      coffee_sipping: "/mascots/mr_nerd/mr_nerd_coffee_sipping.png",
      confused: "/mascots/mr_nerd/mr_nerd_confused.png",
      document_catching: "/mascots/mr_nerd/mr_nerd_document_catching.png",
      excited: "/mascots/mr_nerd/mr_nerd_excited.png",
      huncing: "/mascots/mr_nerd/mr_nerd_hunching.png",
      peeking: "/mascots/mr_nerd/mr_nerd_peeking.png",
      sleeping: "/mascots/mr_nerd/mr_nerd_sleeping.png",
      thinking: "/mascots/mr_nerd/mr_nerd_thinking.png",
      tired: "/mascots/mr_nerd/mr_nerd_tired.png",
      waving: "/mascots/mr_nerd/mr_nerd_waving.png",
    },
  },
  "ms-nerd": {
    id: "ms-nerd",
    label: "Mascot 4",
    name: "Ms. Nerd",
    role: "Senior Mathematical Specialist",
    gender: "Female",
    avatarThumb: "/mascots/ms_nerd/ms_nerd_standing.png",
    sheets: {
      standing: "/mascots/ms_nerd/ms_nerd_standing.png",
      angry: "/mascots/ms_nerd/ms_nerd_angry.png",
      blinking: "/mascots/ms_nerd/ms_nerd_eye_blinking.png",
      coffee_sipping: "/mascots/ms_nerd/ms_nerd_coffee_sipping.png",
      confused: "/mascots/ms_nerd/ms_nerd_confused.png",
      document_catching: "/mascots/ms_nerd/ms_nerd_document_catching.png",
      excited: "/mascots/ms_nerd/ms_nerd_excited.png",
      huncing: "/mascots/ms_nerd/ms_nerd_hunching.png",
      peeking: "/mascots/ms_nerd/ms_nerd_peeking.png",
      sleeping: "/mascots/ms_nerd/ms_nerd_sleeping.png",
      thinking: "/mascots/ms_nerd/ms_nerd_thinking.png",
      tired: "/mascots/ms_nerd/ms_nerd_tired.png",
      waving: "/mascots/ms_nerd/ms_nerd_hii.png",
    },
  },
};

export type ActionKey =
  | "angry"
  | "blinking"
  | "coffee_sipping"
  | "confused"
  | "document_catching"
  | "excited"
  | "huncing"
  | "peeking"
  | "sleeping"
  | "thinking"
  | "tired"
  | "waving";

export interface MascotActionConfig {
  key: ActionKey;
  label: string;
  accentColor: string;
  soundType: "chirp" | "triumph" | "alert" | "low" | "silent";
}

// 12 Authentic actions: Clean linear 3-frame progression (0 -> 1 -> 2)
export const MASCOT_ACTIONS: MascotActionConfig[] = [
  { key: "angry", label: "Angry", accentColor: "#EF4444", soundType: "alert" },
  { key: "blinking", label: "Blinking", accentColor: "#38BDF8", soundType: "silent" },
  { key: "coffee_sipping", label: "Coffee Sipping", accentColor: "#A855F7", soundType: "chirp" },
  { key: "confused", label: "Confused", accentColor: "#F59E0B", soundType: "low" },
  { key: "document_catching", label: "Document Catching", accentColor: "#818CF8", soundType: "chirp" },
  { key: "excited", label: "Excited", accentColor: "#34D399", soundType: "triumph" },
  { key: "huncing", label: "Huncing", accentColor: "#DA7756", soundType: "chirp" },
  { key: "peeking", label: "Peeking", accentColor: "#06B6D4", soundType: "chirp" },
  { key: "sleeping", label: "Sleeping", accentColor: "#38BDF8", soundType: "silent" },
  { key: "thinking", label: "Thinking", accentColor: "#FBBF24", soundType: "low" },
  { key: "tired", label: "Tired", accentColor: "#71717A", soundType: "low" },
  { key: "waving", label: "Waving", accentColor: "#FBBF24", soundType: "chirp" },
];

export function MascotFSMSection() {
  const [activeMascotId, setActiveMascotId] = useState<AvatarId>("mr-nerdy");
  const [activeActionKey, setActiveActionKey] = useState<ActionKey | "standing">("standing");
  const [isLooping, setIsLooping] = useState<boolean>(false);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(1.0); // 0.5x, 1.0x, 1.5x, 2.0x
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Canvas and animation refs
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const loadedImagesRef = useRef<Record<string, HTMLImageElement>>({});
  const animationFrameIdRef = useRef<number | null>(null);
  const animStateRef = useRef({
    actionKey: "standing" as ActionKey | "standing",
    mascotId: "mr-nerdy" as AvatarId,
    isLooping: false,
    speed: 1.0,
    startTime: 0,
    lastFrameTime: 0,
    sequenceIdx: 0,
    cycleCount: 0,
  });

  // Keep animStateRef in sync with React state
  useEffect(() => {
    animStateRef.current.actionKey = activeActionKey;
    animStateRef.current.mascotId = activeMascotId;
    animStateRef.current.isLooping = isLooping;
    animStateRef.current.speed = speedMultiplier;
  }, [activeActionKey, activeMascotId, isLooping, speedMultiplier]);

  // Web Audio synthesizer chirp
  const playAudioCue = useCallback((soundType: MascotActionConfig["soundType"]) => {
    if (soundType === "silent") return;
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      if (soundType === "triumph") {
        osc.type = "triangle";
        osc.frequency.setValueAtTime(523.25, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.18);
      } else if (soundType === "alert") {
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(260, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(140, ctx.currentTime + 0.22);
      } else if (soundType === "low") {
        osc.type = "sine";
        osc.frequency.setValueAtTime(220, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(180, ctx.currentTime + 0.25);
      } else {
        osc.type = "sine";
        osc.frequency.setValueAtTime(440, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(660, ctx.currentTime + 0.12);
      }

      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.005, ctx.currentTime + 0.22);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.25);
      setIsPlayingAudio(true);
      setTimeout(() => setIsPlayingAudio(false), 260);
    } catch {
      // Ignored
    }
  }, []);

  // Preload mascot sprite sheets
  useEffect(() => {
    const mascot = MASCOTS[activeMascotId];
    Object.entries(mascot.sheets).forEach(([key, src]) => {
      const cacheKey = `${activeMascotId}_${key}`;
      if (!loadedImagesRef.current[cacheKey]) {
        const img = new Image();
        img.src = getAssetPath(src);
        img.onload = () => {
          loadedImagesRef.current[cacheKey] = img;
          // Trigger immediate redraw if currently displaying this sheet
          if (animStateRef.current.actionKey === key || (animStateRef.current.actionKey === "standing" && key === "standing")) {
            drawCurrentFrame(animStateRef.current.actionKey, 1);
          }
        };
      }
    });
  }, [activeMascotId]);

  // Core Drawing Function onto Canvas
  const drawCurrentFrame = useCallback((actionKey: ActionKey | "standing", frameIndex: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const cacheKey = `${animStateRef.current.mascotId}_${actionKey}`;
    const img = loadedImagesRef.current[cacheKey];

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!img || !img.naturalWidth || !img.naturalHeight) {
      // Try fallback to standing image
      const fallbackImg = loadedImagesRef.current[`${animStateRef.current.mascotId}_standing`];
      if (fallbackImg && fallbackImg.naturalWidth) {
        renderImageToCanvas(ctx, canvas, fallbackImg, 3, 1);
      }
      return;
    }

    // Every mascot spritesheet (including standing) is a 3-frame horizontal strip (~676x369 px).
    // For standing, the mascot is placed at frameIndex 1 (the center).
    // For actions, frameIndex spans 0, 1, 2.
    // By keeping frameCount = 3 universally, the scale and size remain 100% constant between standing and all actions.
    const frameCount = 3;
    const targetFrame = actionKey === "standing" ? 1 : Math.max(0, Math.min(frameIndex, 2));
    renderImageToCanvas(ctx, canvas, img, frameCount, targetFrame);
  }, []);

  // Accurate centered rendering preserving exact aspect ratio with zero distortion
  const renderImageToCanvas = (
    ctx: CanvasRenderingContext2D,
    canvas: HTMLCanvasElement,
    img: HTMLImageElement,
    frameCount: number,
    frameIndex: number
  ) => {
    const frameW = img.naturalWidth / frameCount;
    const frameH = img.naturalHeight;

    // Scale to fit canvas while preserving exact natural aspect ratio
    const scale = Math.min((canvas.width * 0.9) / frameW, (canvas.height * 0.9) / frameH);
    const drawW = frameW * scale;
    const drawH = frameH * scale;
    const dx = (canvas.width - drawW) / 2;
    const dy = (canvas.height - drawH) / 2 + 10;

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";

    ctx.drawImage(
      img,
      frameIndex * frameW,
      0,
      frameW,
      frameH,
      dx,
      dy,
      drawW,
      drawH
    );
  };

  // Clean linear 3-frame animation loop (Frame 0 -> Frame 1 -> Frame 2)
  useEffect(() => {
    let lastTimestamp = 0;
    animStateRef.current.sequenceIdx = 0;
    animStateRef.current.cycleCount = 0;

    let returnTimeout: NodeJS.Timeout | null = null;

    const clearReturnTimeout = () => {
      if (returnTimeout) {
        clearTimeout(returnTimeout);
        returnTimeout = null;
      }
    };

    const tick = (timestamp: number) => {
      if (!lastTimestamp) lastTimestamp = timestamp;
      const elapsed = timestamp - lastTimestamp;

      const currentAction = animStateRef.current.actionKey;
      const speed = animStateRef.current.speed;
      const isLoop = animStateRef.current.isLooping;

      // Base frame duration: 180ms at 1.0x (deliberate, clearly visible pacing)
      const frameDuration = Math.max(60, 180 / speed);

      if (currentAction === "standing") {
        clearReturnTimeout();
        drawCurrentFrame("standing", 1);
        lastTimestamp = timestamp;
      } else {
        // Linear 3-frame progression: Frame 0 -> Frame 1 -> Frame 2
        if (elapsed >= frameDuration) {
          lastTimestamp = timestamp;

          const currentIdx = animStateRef.current.sequenceIdx;
          drawCurrentFrame(currentAction, currentIdx);

          if (currentIdx < 2) {
            animStateRef.current.sequenceIdx = currentIdx + 1;
          } else {
            // Reached peak frame (Frame 2)
            if (isLoop) {
              // In loop mode: wrap directly to Frame 0
              animStateRef.current.sequenceIdx = 0;
            } else if (currentAction === "sleeping" || currentAction === "tired") {
              // Resting states stay on Frame 2
              animStateRef.current.sequenceIdx = 2;
            } else {
              // Single-play: hold peak Frame 2 for 850ms so the user can clearly see the action before returning to standing
              if (!returnTimeout) {
                returnTimeout = setTimeout(() => {
                  returnTimeout = null;
                  setActiveActionKey("standing");
                  animStateRef.current.actionKey = "standing";
                  animStateRef.current.sequenceIdx = 0;
                  drawCurrentFrame("standing", 1);
                }, 850 / speed);
              }
            }
          }
        }
      }

      animationFrameIdRef.current = requestAnimationFrame(tick);
    };

    animationFrameIdRef.current = requestAnimationFrame(tick);

    return () => {
      clearReturnTimeout();
      if (animationFrameIdRef.current) {
        cancelAnimationFrame(animationFrameIdRef.current);
      }
    };
  }, [drawCurrentFrame]);

  // Handle Action Selection
  const handleSelectAction = (actionKey: ActionKey) => {
    setActiveActionKey(actionKey);
    animStateRef.current.actionKey = actionKey;
    animStateRef.current.sequenceIdx = 0;
    animStateRef.current.cycleCount = 0;

    // Immediately render frame 0 of the action without waiting for next tick
    drawCurrentFrame(actionKey, 0);

    const action = MASCOT_ACTIONS.find((a) => a.key === actionKey);
    if (action) {
      playAudioCue(action.soundType);
    }
  };

  // Stop Button: Immediately return to standing
  const handleStop = () => {
    setActiveActionKey("standing");
    animStateRef.current.actionKey = "standing";
    animStateRef.current.sequenceIdx = 0;
    animStateRef.current.cycleCount = 0;
    drawCurrentFrame("standing", 1);
  };

  // Toggle Looping Mode
  const handleToggleLoop = () => {
    setIsLooping((prev) => {
      const next = !prev;
      animStateRef.current.isLooping = next;
      animStateRef.current.sequenceIdx = 0;
      return next;
    });
  };

  // Switch Mascot Character
  const handleSelectMascot = (mascotId: AvatarId) => {
    setActiveMascotId(mascotId);
    animStateRef.current.mascotId = mascotId;
    setActiveActionKey("standing");
    animStateRef.current.actionKey = "standing";
    animStateRef.current.sequenceIdx = 0;
    animStateRef.current.cycleCount = 0;
    drawCurrentFrame("standing", 1);
  };

  // Click Mascot Viewport (Poke or Wake)
  const handleMascotClick = () => {
    if (activeActionKey === "sleeping") {
      handleSelectAction("waving");
    } else {
      handleSelectAction("waving");
    }
  };

  const activeMascot = MASCOTS[activeMascotId];
  const isSleepingState = activeActionKey === "sleeping";
  const currentActionConfig = MASCOT_ACTIONS.find((a) => a.key === activeActionKey);
  const currentAccent = currentActionConfig ? currentActionConfig.accentColor : "#34D399";

  return (
    <section id="mascot" className="py-20 bg-[#18181B] border-t border-white/8 relative overflow-hidden">
      {/* Ambient background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-[#DA7756]/8 rounded-full blur-[140px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeading
          badge="13-STATE FSM & SPRITE ENGINE"
          badgeVariant="accent"
          title="Interactive Mascot FSM"
          highlightText="12 Animated Actions"
          description="Select any of the 4 characters and 12 distinct action transitions to preview the desktop mascot sprite animations, speed controls, loop toggle, and reactive state transitions."
        />

        {/* Main Mascot Action & Controls Workbench */}
        <div className="rounded-2xl bg-[#222227] border border-white/10 p-6 md:p-8 backdrop-blur-xl shadow-2xl flex flex-col justify-between gap-8">
          
          {/* TOP ROW: Left (Avatar Selector Boxes + Mascot Name + Speed Selector + Loop/Stop) & Right (Mascot Action Display Stage) */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
            
            {/* Top-Left: Avatar Selector Boxes + Mascot Name & Action Controls */}
            <div className="md:col-span-6 flex flex-col justify-between h-full space-y-4">
              
              {/* Avatar Selector Boxes Side-by-Side (Above the Name) */}
              <div className="p-4 rounded-xl bg-[#18181B] border border-white/8 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono uppercase tracking-wider text-[#9E9E99]">
                    Select Mascot:
                  </span>
                  <span className="text-xs font-mono font-bold text-[#DA7756]">
                    4 Avatars
                  </span>
                </div>

                <div className="grid grid-cols-4 gap-3">
                  {(Object.keys(MASCOTS) as AvatarId[]).map((mId) => {
                    const mascot = MASCOTS[mId];
                    const isSelected = activeMascotId === mId;

                    return (
                      <button
                        key={mascot.id}
                        onClick={() => handleSelectMascot(mascot.id)}
                        className={`aspect-square rounded-xl border relative transition-all duration-200 flex items-center justify-center overflow-hidden p-1.5 group cursor-pointer ${
                          isSelected
                            ? "bg-[#222227] border-[#DA7756] shadow-[0_0_18px_rgba(218,119,86,0.35)] ring-2 ring-[#DA7756]/50 scale-[1.03]"
                            : "bg-[#18181B] border-white/10 hover:border-white/30 hover:bg-[#222227]"
                        }`}
                        title={`${mascot.name} (${mascot.gender})`}
                      >
                        {/* Portrait Avatar Focused on Face (Uncompressed) */}
                        <div
                          className="w-full h-full rounded-lg"
                          style={{
                            backgroundImage: `url(${getAssetPath(mascot.avatarThumb)})`,
                            backgroundSize: "280%",
                            backgroundPosition: "center 8%",
                            backgroundRepeat: "no-repeat",
                          }}
                        />

                        {/* Active Indicator Dot */}
                        {isSelected && (
                          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#DA7756] shadow-[0_0_6px_#DA7756]" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
                
              {/* Mascot Name Header */}
              <div className="p-4 rounded-xl bg-[#18181B] border border-white/8">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono uppercase tracking-wider text-[#DA7756] font-semibold">
                    Active Companion
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-[#71717A] capitalize">
                      {activeMascot.gender}
                    </span>
                    <Badge variant="accent" size="sm">
                      {activeMascot.label}
                    </Badge>
                  </div>
                </div>
                <h3 className="text-2xl font-black font-heading text-[#F4F3EE] mt-1">
                  {activeMascot.name}
                </h3>
              </div>

              {/* Merged Playback & Animation Controls (Dropdown Speed + Side-by-Side Loop & Stop) */}
              <div className="p-4 rounded-xl bg-[#18181B] border border-white/8 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono uppercase tracking-wider text-[#9E9E99]">
                    Animation Controls
                  </span>
                  <span className="text-xs font-mono font-bold text-[#38BDF8]">
                    {speedMultiplier.toFixed(1)}x Speed
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 items-center">
                  {/* Speed Selector Dropdown */}
                  <div className="relative">
                    <select
                      value={speedMultiplier}
                      onChange={(e) => setSpeedMultiplier(parseFloat(e.target.value))}
                      className="w-full appearance-none bg-[#222227] border border-white/10 hover:border-white/20 text-[#F4F3EE] text-xs font-mono font-semibold py-3 pl-3 pr-8 rounded-xl cursor-pointer focus:outline-none focus:border-[#38BDF8] transition-all"
                    >
                      <option value={0.5} className="bg-[#18181B] text-[#F4F3EE]">0.5x Speed</option>
                      <option value={1.0} className="bg-[#18181B] text-[#F4F3EE]">1.0x Speed</option>
                      <option value={1.5} className="bg-[#18181B] text-[#F4F3EE]">1.5x Speed</option>
                      <option value={2.0} className="bg-[#18181B] text-[#F4F3EE]">2.0x Speed</option>
                    </select>
                    <ChevronDown className="w-4 h-4 text-[#9E9E99] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>

                  {/* Loop Toggle Button */}
                  <button
                    onClick={handleToggleLoop}
                    className={`flex items-center justify-center gap-2 py-3 px-3 rounded-xl text-xs font-heading font-bold border transition-all ${
                      isLooping
                        ? "bg-[#34D399]/20 border-[#34D399] text-[#34D399] shadow-[0_0_16px_rgba(52,211,153,0.3)]"
                        : "bg-[#222227] border-white/10 text-[#9E9E99] hover:text-[#F4F3EE] hover:border-white/20"
                    }`}
                  >
                    <Repeat className={`w-3.5 h-3.5 ${isLooping ? "animate-spin-slow text-[#34D399]" : ""}`} />
                    <span>{isLooping ? "Loop: ON" : "Loop: OFF"}</span>
                  </button>

                  {/* Stop Button */}
                  <button
                    onClick={handleStop}
                    className="flex items-center justify-center gap-2 py-3 px-3 rounded-xl text-xs font-heading font-bold bg-[#EF4444]/15 border border-[#EF4444]/30 text-[#EF4444] hover:bg-[#EF4444]/25 hover:border-[#EF4444] transition-all"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>Stop</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Top-Right: Mascot Action Viewport Stage */}
            <div className="md:col-span-6 rounded-2xl bg-[#18181B] border border-white/10 p-6 flex flex-col items-center justify-between text-center relative overflow-hidden min-h-[380px] shadow-inner">
                
                {/* Main Mascot Stage Hitbox */}
                <div
                  onClick={handleMascotClick}
                  className="relative w-full h-72 flex items-center justify-center cursor-pointer select-none group my-auto"
                  title="Click mascot to interact!"
                >
                  {/* Floating ZZZ for sleep state */}
                  {isSleepingState && (
                    <div className="absolute top-6 right-16 pointer-events-none z-20">
                      <span className="absolute font-mono font-black text-xs text-[#38BDF8] animate-float-z1">
                        Z
                      </span>
                      <span className="absolute font-mono font-black text-sm text-[#A855F7] animate-float-z2">
                        Z
                      </span>
                      <span className="absolute font-mono font-black text-base text-[#F43F5E] animate-float-z3">
                        Z
                      </span>
                    </div>
                  )}

                  {/* Ambient Glow Aura */}
                  <div
                    className="absolute inset-8 rounded-full opacity-25 blur-2xl pointer-events-none transition-colors duration-300"
                    style={{ backgroundColor: currentAccent }}
                  />

                  {/* High-Performance 60FPS Sprite Canvas with Zero Distortion */}
                  <canvas
                    ref={canvasRef}
                    width={320}
                    height={320}
                    className="w-72 h-72 object-contain filter drop-shadow-[0_10px_24px_rgba(0,0,0,0.6)] transition-transform duration-200 group-hover:scale-105"
                  />
                </div>

                {/* Stage Telemetry Footer without frame counter */}
                <div className="w-full flex items-center justify-between pt-3 border-t border-white/8 text-[11px] font-mono">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full animate-pulse"
                      style={{ backgroundColor: currentAccent }}
                    />
                    <span className="font-bold text-[#F4F3EE] uppercase tracking-wider">
                      {activeActionKey}
                    </span>
                  </div>

                  <button
                    onClick={() => playAudioCue("chirp")}
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-[#DA7756] transition-colors"
                    title="Play micro-chirp sound"
                  >
                    <Volume2 className={`w-4 h-4 ${isPlayingAudio ? "animate-bounce" : ""}`} />
                  </button>
                </div>
              </div>
            </div>

            {/* BOTTOM SECTION: 12 Action Buttons Grid (Excluding standing) */}
            <div>
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/8">
                <div className="flex items-center gap-2">
                  <Play className="w-3.5 h-3.5 text-[#DA7756]" />
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#F4F3EE]">
                    Mascot Action Trigger Matrix:
                  </span>
                </div>
                <span className="text-xs font-mono text-[#DA7756]">
                  12 Actions Mapped
                </span>
              </div>

              {/* 12 Action Named Buttons */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
                {MASCOT_ACTIONS.map((action) => {
                  const isSelected = activeActionKey === action.key;

                  return (
                    <button
                      key={action.key}
                      onClick={() => handleSelectAction(action.key)}
                      className={`py-3 px-4 rounded-xl text-center font-heading font-semibold text-xs sm:text-sm border transition-all duration-200 capitalize ${
                        isSelected
                          ? "bg-[#DA7756] text-white border-[#DA7756] shadow-[0_0_18px_rgba(218,119,86,0.4)] scale-[1.02]"
                          : "bg-[#1C1C20] text-[#F4F3EE] border-white/8 hover:bg-[#222227] hover:border-white/20 hover:text-white"
                      }`}
                    >
                      {action.label}
                    </button>
                  );
                })}
              </div>
            </div>

          </div>
        </div>
      </section>
  );
}
