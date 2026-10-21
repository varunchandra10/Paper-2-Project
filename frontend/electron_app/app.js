// Mr. Nerdy Animation Transition Visualizer Logic
// Supports precision frame scheduling, adaptive anchoring, crossfades, pose-based, sequential transitions,
// side-by-side comparison, quality diagnostics, timeline scrubbing, and exports.

(function () {
  'use strict';

  // --- State Management ---
  const state = {
    animations: {},
    loadedImages: {}, // path -> HTMLImageElement
    isReady: false,
    
    // Playback state
    mode: 'transition', // 'single' | 'transition'
    isPlaying: false,
    speed: 1.0,
    zoom: 1.0,
    loopMode: 'loop_all', // 'loop_all', 'loop_target', 'once'
    bgStyle: 'checkerboard', // 'checkerboard', 'solid-dark', 'solid-light'
    showGuides: true,
    
    // Transition Configuration
    sourceId: 'idle',
    targetId: 'waving_hii',
    transitionType: 'pose_based', // 'immediate', 'crossfade', 'pose_based', 'sequential'
    transitionDurationMs: 300,
    sourceLoops: 1,
    targetLoops: 1,
    
    // Current playhead
    currentTimeMs: 0,
    totalDurationMs: 1000,
    sequenceFrames: [], // compiled list of { animId, frameIdx, timeStart, timeEnd, type, alpha }
    
    // Animation frame handle
    rafId: null,
    lastRafTime: null,
    
    activePresetId: null
  };

  // --- Preset Definitions ---
  const PRESET_GALLERY = [
    {
      id: 'idle_blink',
      title: 'Idle → Blinking → Idle',
      source: 'idle',
      target: 'blinking',
      type: 'immediate',
      duration: 130,
      description: 'Natural eye blink returning to neutral idle stance',
      available: true
    },
    {
      id: 'idle_wave',
      title: 'Idle → Waving → Idle',
      source: 'idle',
      target: 'waving_hii',
      type: 'pose_based',
      duration: 250,
      description: 'Hand waving greeting returning to neutral idle stance',
      available: true
    },
    {
      id: 'idle_thinking',
      title: 'Idle → Thinking → Idle',
      source: 'idle',
      target: 'thinking',
      type: 'pose_based',
      duration: 250,
      description: 'Hand touches chin to ponder before settling',
      available: true
    },
    {
      id: 'idle_confused',
      title: 'Idle → Confused → Idle',
      source: 'idle',
      target: 'confused',
      type: 'pose_based',
      duration: 250,
      description: 'Head scratch with confusion sweat marks',
      available: true
    },
    {
      id: 'idle_excited',
      title: 'Idle → Excited → Idle',
      source: 'idle',
      target: 'excited',
      type: 'pose_based',
      duration: 200,
      description: 'Excited hop celebration and return to standing',
      available: true
    },
    {
      id: 'idle_angry',
      title: 'Idle → Angry → Idle',
      source: 'idle',
      target: 'mad',
      type: 'pose_based',
      duration: 250,
      description: 'Fists clench with anger steam effects',
      available: true
    },
    {
      id: 'idle_tired',
      title: 'Idle → Tired → Idle',
      source: 'idle',
      target: 'tired',
      type: 'pose_based',
      duration: 300,
      description: 'Slumping shoulders into tired state',
      available: true
    },
    {
      id: 'idle_working',
      title: 'Idle → Working on Laptop',
      source: 'idle',
      target: 'working_laptop',
      type: 'sequential',
      duration: 400,
      description: 'Pulls chair, sits at desk, and opens laptop',
      available: true
    },
    {
      id: 'standing_to_sleeping',
      title: 'Idle → Standing to Sleeping',
      source: 'idle',
      target: 'standing_to_sleeping',
      type: 'sequential',
      duration: 500,
      description: 'Yawns, becomes sleepy, sits down to sleep',
      available: true
    },
    {
      id: 'working_sleeping',
      title: 'Working → Tired → Sleeping',
      source: 'working_laptop',
      target: 'sleeping_loop',
      type: 'sequential',
      duration: 600,
      description: 'Late night desk work to exhausted sleep in chair/cot',
      available: true
    },
    {
      id: 'walk_right',
      title: 'Idle → Walking Right → Idle',
      source: 'idle',
      target: 'walking_left_to_right',
      type: 'pose_based',
      duration: 200,
      description: 'Steps out into rightward walk cycle and settles',
      available: true
    },
    {
      id: 'walk_left',
      title: 'Idle → Walking Left → Idle',
      source: 'idle',
      target: 'walking_right_to_left',
      type: 'pose_based',
      duration: 200,
      description: 'Steps out into leftward walk cycle and settles',
      available: true
    },
    {
      id: 'turn_right',
      title: 'Front-facing → Turn Right',
      source: 'idle',
      target: 'turnaround',
      type: 'pose_based',
      duration: 250,
      description: 'Uses turnaround 30° and 60° rotation poses',
      available: true
    },
    {
      id: 'turn_left',
      title: 'Front-facing → Turn Left',
      source: 'idle',
      target: 'turnaround',
      type: 'pose_based',
      duration: 250,
      description: 'Uses turnaround 330° and 300° rotation poses',
      available: true
    },
    {
      id: 'doc_to_thinking',
      title: 'Catching Document → Thinking',
      source: 'doc_catching',
      target: 'thinking',
      type: 'sequential',
      duration: 350,
      description: 'Catches falling document and ponders findings',
      available: true
    },
    {
      id: 'peeking_to_idle',
      title: 'Peeking → Idle',
      source: 'peeking',
      target: 'idle',
      type: 'sequential',
      duration: 300,
      description: 'Rises from horizontal barrier and stands up straight',
      available: true
    },
    {
      id: 'sipping_coffee',
      title: 'Idle → Sipping Coffee (Unavailable)',
      source: 'idle',
      target: 'sipping_coffee',
      type: 'crossfade',
      duration: 300,
      description: 'Coffee mug drinking animation (AI sheet missing)',
      available: false
    }
  ];

  // --- DOM Elements ---
  const el = {};

  function initElements() {
    el.canvas = document.getElementById('stageCanvas');
    el.ctx = el.canvas ? el.canvas.getContext('2d') : null;
    el.stageContainer = document.getElementById('stageContainer');
    
    el.sourceSelect = document.getElementById('sourceAnimSelect');
    el.targetSelect = document.getElementById('targetAnimSelect');
    el.transitionTypeSelect = document.getElementById('transitionTypeSelect');
    el.durationSlider = document.getElementById('durationSlider');
    el.durationVal = document.getElementById('durationVal');
    
    el.btnPlay = document.getElementById('btnPlay');
    el.btnRestart = document.getElementById('btnRestart');
    el.btnPrev = document.getElementById('btnPrev');
    el.btnNext = document.getElementById('btnNext');
    el.btnLoop = document.getElementById('btnLoop');
    el.btnGuides = document.getElementById('btnGuides');
    
    el.timecodeDisplay = document.getElementById('timecodeDisplay');
    el.frameDisplay = document.getElementById('frameDisplay');
    el.canvasDimDisplay = document.getElementById('canvasDimDisplay');
    
    el.timelineTrack = document.getElementById('timelineTrack');
    el.timelinePlayhead = document.getElementById('timelinePlayhead');
    el.timelineSource = document.getElementById('timelineSource');
    el.timelineTrans = document.getElementById('timelineTrans');
    el.timelineTarget = document.getElementById('timelineTarget');
    el.timelineTimeTotal = document.getElementById('timelineTimeTotal');
    
    el.guideGround = document.getElementById('guideGround');
    el.guideCenter = document.getElementById('guideCenter');
    
    el.sourcePoseCanvas = document.getElementById('sourcePoseCanvas');
    el.transPoseCanvas = document.getElementById('transPoseCanvas');
    el.targetPoseCanvas = document.getElementById('targetPoseCanvas');
    el.sourcePoseDim = document.getElementById('sourcePoseDim');
    el.transPoseDim = document.getElementById('transPoseDim');
    el.targetPoseDim = document.getElementById('targetPoseDim');
    
    el.diagScore = document.getElementById('diagScore');
    el.diagDeltaX = document.getElementById('diagDeltaX');
    el.diagDeltaY = document.getElementById('diagDeltaY');
    el.diagScale = document.getElementById('diagScale');
    el.diagWarnings = document.getElementById('diagWarnings');
    
    el.presetsContainer = document.getElementById('presetsList');
    
    el.exportModal = document.getElementById('exportModal');
    el.btnOpenExport = document.getElementById('btnOpenExport');
    el.btnCloseExport = document.getElementById('btnCloseExport');
  }

  // --- Asset Loading ---
  async function loadAnimationsData() {
    try {
      const res = await fetch('data/animations.json');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      state.animations = await res.json();
    } catch (err) {
      console.warn("Fetch failed, falling back to embedded dataset:", err);
      if (window.EMBEDDED_ANIMATIONS_DATA) {
        state.animations = window.EMBEDDED_ANIMATIONS_DATA;
      }
    }
    
    populateDropdowns();
    renderPresets();
    await preloadAllFrames();
    
    state.isReady = true;
    compileTransitionSequence();
    updateQualityDiagnostics();
    updateSideBySidePreview();
    renderStageFrame();
  }

  function preloadAllFrames() {
    const promises = [];
    for (const animId in state.animations) {
      const anim = state.animations[animId];
      if (!anim.frames) continue;
      for (const f of anim.frames) {
        if (!state.loadedImages[f.rel_path]) {
          const img = new Image();
          img.src = '../' + f.rel_path;
          const p = new Promise(resolve => {
            img.onload = () => {
              state.loadedImages[f.rel_path] = img;
              resolve();
            };
            img.onerror = () => {
              console.warn("Failed to load frame image:", img.src);
              resolve();
            };
          });
          promises.push(p);
        }
      }
    }
    return Promise.all(promises);
  }

  // --- UI Population ---
  function populateDropdowns() {
    if (!el.sourceSelect || !el.targetSelect) return;
    el.sourceSelect.innerHTML = '';
    el.targetSelect.innerHTML = '';
    
    const sortedIds = Object.keys(state.animations).sort();
    
    for (const id of sortedIds) {
      const anim = state.animations[id];
      const opt1 = document.createElement('option');
      opt1.value = id;
      opt1.textContent = `${anim.title} (${anim.frame_count} frames)`;
      if (id === state.sourceId) opt1.selected = true;
      el.sourceSelect.appendChild(opt1);
      
      const opt2 = document.createElement('option');
      opt2.value = id;
      opt2.textContent = `${anim.title} (${anim.frame_count} frames)`;
      if (id === state.targetId) opt2.selected = true;
      el.targetSelect.appendChild(opt2);
    }
  }

  function renderPresets() {
    if (!el.presetsContainer) return;
    el.presetsContainer.innerHTML = '';
    
    PRESET_GALLERY.forEach(p => {
      const card = document.createElement('div');
      card.className = `preset-card ${p.available ? '' : 'disabled'} ${state.activePresetId === p.id ? 'active' : ''}`;
      card.innerHTML = `
        <div class="preset-info">
          <div class="preset-title">${p.title}</div>
          <div class="preset-flow">${p.source} → ${p.target} (${p.type})</div>
        </div>
        <div class="preset-badge ${p.available ? 'ready' : 'missing'}">${p.available ? 'READY' : 'MISSING'}</div>
      `;
      
      if (p.available) {
        card.addEventListener('click', () => applyPreset(p));
      }
      el.presetsContainer.appendChild(card);
    });
  }

  function applyPreset(p) {
    state.activePresetId = p.id;
    state.sourceId = p.source;
    state.targetId = p.target;
    state.transitionType = p.type;
    state.transitionDurationMs = p.duration;
    
    if (el.sourceSelect) el.sourceSelect.value = p.source;
    if (el.targetSelect) el.targetSelect.value = p.target;
    if (el.transitionTypeSelect) el.transitionTypeSelect.value = p.type;
    if (el.durationSlider) el.durationSlider.value = p.duration;
    if (el.durationVal) el.durationVal.textContent = `${p.duration}ms`;
    
    renderPresets();
    compileTransitionSequence();
    updateQualityDiagnostics();
    updateSideBySidePreview();
    seekTo(0);
    play();
  }

  // --- Sequence Compilation ---
  function compileTransitionSequence() {
    const srcAnim = state.animations[state.sourceId];
    const tgtAnim = state.animations[state.targetId];
    
    if (!srcAnim || !tgtAnim) return;
    
    const seq = [];
    let curTime = 0;
    
    // 1. Source Animation Segment
    const srcDuration = srcAnim.frame_duration_ms || 125;
    for (let l = 0; l < state.sourceLoops; l++) {
      for (let f = 0; f < srcAnim.frames.length; f++) {
        seq.push({
          phase: 'source',
          animId: state.sourceId,
          frameIdx: f,
          frameData: srcAnim.frames[f],
          timeStart: curTime,
          timeEnd: curTime + srcDuration,
          duration: srcDuration,
          type: 'solid',
          opacity: 1.0
        });
        curTime += srcDuration;
      }
    }
    const sourceEndTime = curTime;
    
    // 2. Transition Phase
    const transType = state.transitionType;
    const transDur = state.transitionDurationMs;
    
    if (transType === 'immediate') {
      // 0ms or instantaneous
    } else if (transType === 'crossfade') {
      // Interpolate crossfade across N steps
      const steps = Math.max(3, Math.round(transDur / 50));
      const stepDur = transDur / steps;
      const lastSrcFrame = srcAnim.frames[srcAnim.frames.length - 1];
      const firstTgtFrame = tgtAnim.frames[0];
      
      for (let i = 0; i < steps; i++) {
        const t = i / (steps - 1); // 0.0 to 1.0
        seq.push({
          phase: 'transition',
          animId: `${state.sourceId}→${state.targetId}`,
          timeStart: curTime,
          timeEnd: curTime + stepDur,
          duration: stepDur,
          type: 'crossfade',
          srcFrame: lastSrcFrame,
          tgtFrame: firstTgtFrame,
          srcOpacity: 1.0 - t,
          tgtOpacity: t
        });
        curTime += stepDur;
      }
    } else if (transType === 'pose_based') {
      // Check if turnaround intermediate frames or settling frames apply
      if ((state.sourceId === 'idle' || state.sourceId === 'front_facing') && state.targetId === 'turnaround') {
        const turn = state.animations['turnaround'];
        const turnDur = 100;
        // Play frame 1 (30deg), frame 2 (60deg), frame 3 (90deg)
        [1, 2, 3].forEach(idx => {
          if (turn.frames[idx]) {
            seq.push({
              phase: 'transition',
              animId: 'turnaround',
              frameIdx: idx,
              frameData: turn.frames[idx],
              timeStart: curTime,
              timeEnd: curTime + turnDur,
              duration: turnDur,
              type: 'solid',
              opacity: 1.0
            });
            curTime += turnDur;
          }
        });
      } else {
        // Natural settling: play first frame of target with small ease-in
        const stepDur = Math.max(80, transDur / 2);
        seq.push({
          phase: 'transition',
          animId: state.targetId,
          frameIdx: 0,
          frameData: tgtAnim.frames[0],
          timeStart: curTime,
          timeEnd: curTime + stepDur,
          duration: stepDur,
          type: 'solid',
          opacity: 1.0
        });
        curTime += stepDur;
      }
    } else if (transType === 'sequential') {
      // Plays natural intro of target (or scene transition frames)
      const stepDur = Math.max(100, transDur / Math.min(3, tgtAnim.frames.length));
      const introCount = Math.min(3, tgtAnim.frames.length);
      for (let f = 0; f < introCount; f++) {
        seq.push({
          phase: 'transition',
          animId: state.targetId,
          frameIdx: f,
          frameData: tgtAnim.frames[f],
          timeStart: curTime,
          timeEnd: curTime + stepDur,
          duration: stepDur,
          type: 'solid',
          opacity: 1.0
        });
        curTime += stepDur;
      }
    }
    const transEndTime = curTime;
    
    // 3. Target Animation Segment
    const tgtDuration = tgtAnim.frame_duration_ms || 125;
    for (let l = 0; l < state.targetLoops; l++) {
      for (let f = 0; f < tgtAnim.frames.length; f++) {
        seq.push({
          phase: 'target',
          animId: state.targetId,
          frameIdx: f,
          frameData: tgtAnim.frames[f],
          timeStart: curTime,
          timeEnd: curTime + tgtDuration,
          duration: tgtDuration,
          type: 'solid',
          opacity: 1.0
        });
        curTime += tgtDuration;
      }
    }
    
    state.sequenceFrames = seq;
    state.totalDurationMs = curTime;
    
    updateTimelineDisplay(sourceEndTime, transEndTime, curTime);
  }

  function updateTimelineDisplay(sourceEnd, transEnd, total) {
    if (!el.timelineSource || !el.timelineTrans || !el.timelineTarget) return;
    
    const pSrc = (sourceEnd / total) * 100;
    const pTrans = ((transEnd - sourceEnd) / total) * 100;
    const pTgt = ((total - transEnd) / total) * 100;
    
    el.timelineSource.style.width = `${pSrc}%`;
    el.timelineSource.textContent = `${state.sourceId} (${Math.round(sourceEnd)}ms)`;
    
    el.timelineTrans.style.width = `${pTrans}%`;
    el.timelineTrans.textContent = pTrans > 8 ? `${state.transitionType} (${Math.round(transEnd - sourceEnd)}ms)` : '';
    
    el.timelineTarget.style.width = `${pTgt}%`;
    el.timelineTarget.textContent = `${state.targetId} (${Math.round(total - transEnd)}ms)`;
    
    if (el.timelineTimeTotal) {
      el.timelineTimeTotal.textContent = `${Math.round(total)}ms`;
    }
  }

  // --- Rendering Stage Frame ---
  function getFrameAtTime(t) {
    if (!state.sequenceFrames.length) return null;
    const clamped = Math.max(0, Math.min(t, state.totalDurationMs));
    for (let i = 0; i < state.sequenceFrames.length; i++) {
      const f = state.sequenceFrames[i];
      if (clamped >= f.timeStart && clamped <= f.timeEnd) {
        return f;
      }
    }
    return state.sequenceFrames[state.sequenceFrames.length - 1];
  }

  function renderStageFrame() {
    if (!el.ctx || !el.canvas) return;
    
    const curFrame = getFrameAtTime(state.currentTimeMs);
    if (!curFrame) return;
    
    // Choose canvas dimensions: accommodate max bounds of source and target
    const srcAnim = state.animations[state.sourceId];
    const tgtAnim = state.animations[state.targetId];
    
    const stageW = Math.max(400, (srcAnim?.canvas?.width || 300), (tgtAnim?.canvas?.width || 300));
    const stageH = Math.max(700, (srcAnim?.canvas?.height || 700), (tgtAnim?.canvas?.height || 700));
    
    if (el.canvas.width !== stageW || el.canvas.height !== stageH) {
      el.canvas.width = stageW;
      el.canvas.height = stageH;
    }
    
    el.ctx.clearRect(0, 0, stageW, stageH);
    
    const groundY = stageH - 30;
    const centerX = stageW / 2;
    
    if (curFrame.type === 'crossfade') {
      // Render crossfade between srcFrame and tgtFrame
      renderSingleFrameItem(curFrame.srcFrame, curFrame.srcOpacity, stageW, stageH, groundY, centerX);
      renderSingleFrameItem(curFrame.tgtFrame, curFrame.tgtOpacity, stageW, stageH, groundY, centerX);
    } else {
      renderSingleFrameItem(curFrame.frameData, curFrame.opacity || 1.0, stageW, stageH, groundY, centerX);
    }
    
    // Draw visual guides if enabled
    if (state.showGuides) {
      el.ctx.save();
      el.ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
      el.ctx.lineWidth = 1;
      el.ctx.setLineDash([4, 4]);
      
      // Ground Line
      el.ctx.beginPath();
      el.ctx.moveTo(0, groundY);
      el.ctx.lineTo(stageW, groundY);
      el.ctx.stroke();
      
      // Center Line
      el.ctx.strokeStyle = 'rgba(192, 132, 252, 0.45)';
      el.ctx.beginPath();
      el.ctx.moveTo(centerX, 0);
      el.ctx.lineTo(centerX, stageH);
      el.ctx.stroke();
      
      el.ctx.restore();
    }
    
    // Update playhead on timeline
    if (el.timelinePlayhead && state.totalDurationMs > 0) {
      const pct = (state.currentTimeMs / state.totalDurationMs) * 100;
      el.timelinePlayhead.style.left = `${Math.min(100, Math.max(0, pct))}%`;
    }
    
    // Update labels
    if (el.timecodeDisplay) {
      const secs = (state.currentTimeMs / 1000).toFixed(2);
      el.timecodeDisplay.textContent = `${secs}s / ${(state.totalDurationMs / 1000).toFixed(2)}s`;
    }
    if (el.frameDisplay) {
      const idx = curFrame.frameIdx !== undefined ? curFrame.frameIdx + 1 : 'TF';
      el.frameDisplay.textContent = `Phase: ${curFrame.phase.toUpperCase()} (F${idx})`;
    }
    if (el.canvasDimDisplay) {
      el.canvasDimDisplay.textContent = `${stageW}×${stageH}`;
    }
  }

  function renderSingleFrameItem(fData, opacity, stageW, stageH, groundY, centerX) {
    if (!fData) return;
    const img = state.loadedImages[fData.rel_path];
    if (!img || !img.complete) return;
    
    el.ctx.save();
    el.ctx.globalAlpha = opacity;
    
    // Align frame
    // Anchor logic: groundY aligns with frame foot_y, centerX aligns with frame center_x
    const pasteX = centerX - (fData.center_x || fData.width / 2);
    const pasteY = groundY - (fData.foot_y || fData.height);
    
    el.ctx.drawImage(img, pasteX, pasteY);
    el.ctx.restore();
  }

  // --- Animation Scheduler ---
  function play() {
    if (state.isPlaying) return;
    state.isPlaying = true;
    state.lastRafTime = performance.now();
    if (el.btnPlay) el.btnPlay.textContent = '⏸ Pause';
    tick(performance.now());
  }

  function pause() {
    state.isPlaying = false;
    if (state.rafId) {
      cancelAnimationFrame(state.rafId);
      state.rafId = null;
    }
    if (el.btnPlay) el.btnPlay.textContent = '▶ Play';
  }

  function restart() {
    seekTo(0);
    play();
  }

  function seekTo(ms) {
    state.currentTimeMs = Math.max(0, Math.min(ms, state.totalDurationMs));
    renderStageFrame();
  }

  function stepFrame(delta) {
    pause();
    const curFrame = getFrameAtTime(state.currentTimeMs);
    const stepMs = curFrame ? curFrame.duration : 100;
    seekTo(state.currentTimeMs + delta * stepMs);
  }

  function tick(timestamp) {
    if (!state.isPlaying) return;
    
    const delta = (timestamp - (state.lastRafTime || timestamp)) * state.speed;
    state.lastRafTime = timestamp;
    
    state.currentTimeMs += delta;
    
    if (state.currentTimeMs >= state.totalDurationMs) {
      if (state.loopMode === 'once') {
        state.currentTimeMs = state.totalDurationMs;
        pause();
      } else {
        state.currentTimeMs = state.currentTimeMs % state.totalDurationMs;
      }
    }
    
    renderStageFrame();
    state.rafId = requestAnimationFrame(tick);
  }

  // --- Side-by-Side & Diagnostics ---
  function updateSideBySidePreview() {
    const srcAnim = state.animations[state.sourceId];
    const tgtAnim = state.animations[state.targetId];
    if (!srcAnim || !tgtAnim) return;
    
    const srcF = srcAnim.frames[srcAnim.frames.length - 1];
    const tgtF = tgtAnim.frames[0];
    
    renderPoseToCanvas(el.sourcePoseCanvas, srcF);
    renderPoseToCanvas(el.targetPoseCanvas, tgtF);
    
    // Middle transition pose
    if (state.transitionType === 'crossfade') {
      renderCrossfadePose(el.transPoseCanvas, srcF, tgtF);
    } else {
      renderPoseToCanvas(el.transPoseCanvas, tgtAnim.frames[0]);
    }
    
    if (el.sourcePoseDim) el.sourcePoseDim.textContent = `${srcF.fg_width}×${srcF.fg_height}`;
    if (el.targetPoseDim) el.targetPoseDim.textContent = `${tgtF.fg_width}×${tgtF.fg_height}`;
    if (el.transPoseDim) el.transPoseDim.textContent = state.transitionType.toUpperCase();
  }

  function renderPoseToCanvas(c, f) {
    if (!c || !f) return;
    const ctx = c.getContext('2d');
    const img = state.loadedImages[f.rel_path];
    ctx.clearRect(0, 0, c.width, c.height);
    if (!img) return;
    
    const scale = Math.min((c.width * 0.8) / f.width, (c.height * 0.8) / f.height);
    const drawW = f.width * scale;
    const drawH = f.height * scale;
    const ox = (c.width - drawW) / 2;
    const oy = (c.height - drawH) / 2;
    ctx.drawImage(img, ox, oy, drawW, drawH);
  }

  function renderCrossfadePose(c, f1, f2) {
    if (!c) return;
    const ctx = c.getContext('2d');
    ctx.clearRect(0, 0, c.width, c.height);
    
    ctx.globalAlpha = 0.5;
    renderPoseToCanvas(c, f1);
    ctx.globalAlpha = 0.5;
    renderPoseToCanvas(c, f2);
    ctx.globalAlpha = 1.0;
  }

  function updateQualityDiagnostics() {
    const srcAnim = state.animations[state.sourceId];
    const tgtAnim = state.animations[state.targetId];
    if (!srcAnim || !tgtAnim) return;
    
    const srcF = srcAnim.frames[srcAnim.frames.length - 1];
    const tgtF = tgtAnim.frames[0];
    
    const deltaX = Math.round(Math.abs(srcF.center_x - tgtF.center_x));
    const deltaY = Math.round(Math.abs(srcF.foot_y - tgtF.foot_y));
    const scaleRatio = (tgtF.fg_height / Math.max(1, srcF.fg_height)).toFixed(2);
    
    if (el.diagDeltaX) el.diagDeltaX.textContent = `${deltaX}px`;
    if (el.diagDeltaY) el.diagDeltaY.textContent = `${deltaY}px`;
    if (el.diagScale) el.diagScale.textContent = `${scaleRatio}×`;
    
    const warnings = [];
    
    if (deltaX > 25) {
      warnings.push({ text: `Noticeable horizontal shift (ΔX = ${deltaX}px). Recommend centering anchor.`, level: 'warn' });
    }
    if (deltaY > 35) {
      warnings.push({ text: `Ground level shift (ΔY = ${deltaY}px). Typical for standing → sitting/sleeping transition.`, level: 'warn' });
    }
    if (scaleRatio < 0.75 || scaleRatio > 1.35) {
      warnings.push({ text: `Substantial bounding height difference (${scaleRatio}×). Scene change or crouch pose.`, level: 'warn' });
    }
    if (srcAnim.canvas.width !== tgtAnim.canvas.width || srcAnim.canvas.height !== tgtAnim.canvas.height) {
      warnings.push({ text: `Canvas resolution differs (${srcAnim.canvas.dimensions} vs ${tgtAnim.canvas.dimensions}). Common stage normalization active.`, level: 'info' });
    }
    
    let rating = 'Seamless';
    let ratingClass = 'seamless';
    if (warnings.length > 2) {
      rating = 'Noticeable Jump';
      ratingClass = 'jump';
    } else if (warnings.length > 0) {
      rating = 'Minor Shift';
      ratingClass = 'minor';
    }
    
    if (el.diagScore) {
      el.diagScore.textContent = rating;
      el.diagScore.className = `diag-rating ${ratingClass}`;
    }
    
    if (el.diagWarnings) {
      el.diagWarnings.innerHTML = '';
      if (!warnings.length) {
        el.diagWarnings.innerHTML = '<div class="diag-warning-item clean">✓ Consistent foot placement and silhouette scale.</div>';
      } else {
        warnings.forEach(w => {
          const item = document.createElement('div');
          item.className = `diag-warning-item ${w.level === 'warn' ? '' : 'clean'}`;
          item.textContent = w.text;
          el.diagWarnings.appendChild(item);
        });
      }
    }
  }

  // --- Export Functionality ---
  function exportTransitionDefinitionJSON() {
    const def = {
      project: "Mr. Nerdy Mascot Animation System",
      export_timestamp: new Date().toISOString(),
      transition_id: `${state.sourceId}_to_${state.targetId}`,
      source: {
        id: state.sourceId,
        loops: state.sourceLoops,
        frame_count: state.animations[state.sourceId]?.frame_count
      },
      target: {
        id: state.targetId,
        loops: state.targetLoops,
        frame_count: state.animations[state.targetId]?.frame_count
      },
      transition: {
        type: state.transitionType,
        duration_ms: state.transitionDurationMs,
        speed_multiplier: state.speed
      },
      timeline: {
        total_duration_ms: state.totalDurationMs,
        step_count: state.sequenceFrames.length,
        steps: state.sequenceFrames.map(f => ({
          phase: f.phase,
          anim_id: f.animId,
          frame_index: f.frameIdx,
          time_start_ms: Math.round(f.timeStart),
          duration_ms: Math.round(f.duration),
          type: f.type,
          opacity: f.opacity || (f.tgtOpacity !== undefined ? f.tgtOpacity : 1.0)
        }))
      }
    };
    
    downloadFile(`transition_${state.sourceId}_to_${state.targetId}.json`, JSON.stringify(def, null, 2), 'application/json');
  }

  function exportMascotTransitionsManifest() {
    // Generates application controller consumable format (matching electron_app/src/mascot_transitions.json)
    const manifestItem = {};
    manifestItem[`${state.sourceId}_to_${state.targetId}`] = {
      loop: state.loopMode === 'loop_all',
      description: `Transition from ${state.sourceId} to ${state.targetId} via ${state.transitionType}`,
      steps: state.sequenceFrames.map(f => ({
        sheet: f.animId,
        frame: f.frameIdx !== undefined ? f.frameIdx : 0,
        hold: Math.round(f.duration),
        fade: f.type === 'crossfade' ? 50 : 0,
        bubble: false,
        zzz: f.animId.includes('sleep')
      }))
    };
    
    downloadFile(`mascot_transition_manifest.json`, JSON.stringify(manifestItem, null, 2), 'application/json');
  }

  function exportTransitionSpritesheet() {
    // Renders stitched horizontal strip of all sequence frames
    const numFrames = state.sequenceFrames.length;
    if (numFrames === 0) return;
    
    const frameW = el.canvas.width;
    const frameH = el.canvas.height;
    
    const sheetCanvas = document.createElement('canvas');
    sheetCanvas.width = frameW * numFrames;
    sheetCanvas.height = frameH;
    const sCtx = sheetCanvas.getContext('2d');
    
    const groundY = frameH - 30;
    const centerX = frameW / 2;
    
    state.sequenceFrames.forEach((curFrame, idx) => {
      sCtx.save();
      sCtx.translate(idx * frameW, 0);
      
      if (curFrame.type === 'crossfade') {
        renderFrameOnContext(sCtx, curFrame.srcFrame, curFrame.srcOpacity, frameW, frameH, groundY, centerX);
        renderFrameOnContext(sCtx, curFrame.tgtFrame, curFrame.tgtOpacity, frameW, frameH, groundY, centerX);
      } else {
        renderFrameOnContext(sCtx, curFrame.frameData, curFrame.opacity || 1.0, frameW, frameH, groundY, centerX);
      }
      sCtx.restore();
    });
    
    sheetCanvas.toBlob(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `spritesheet_transition_${state.sourceId}_to_${state.targetId}.png`;
      a.click();
      URL.revokeObjectURL(url);
    }, 'image/png');
  }

  function renderFrameOnContext(ctx, fData, opacity, stageW, stageH, groundY, centerX) {
    if (!fData) return;
    const img = state.loadedImages[fData.rel_path];
    if (!img) return;
    ctx.save();
    ctx.globalAlpha = opacity;
    const pasteX = centerX - (fData.center_x || fData.width / 2);
    const pasteY = groundY - (fData.foot_y || fData.height);
    ctx.drawImage(img, pasteX, pasteY);
    ctx.restore();
  }

  function downloadFile(filename, text, type) {
    const blob = new Blob([text], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  // --- Event Bindings ---
  function bindEvents() {
    el.sourceSelect?.addEventListener('change', (e) => {
      state.sourceId = e.target.value;
      state.activePresetId = null;
      renderPresets();
      compileTransitionSequence();
      updateQualityDiagnostics();
      updateSideBySidePreview();
      seekTo(0);
    });
    
    el.targetSelect?.addEventListener('change', (e) => {
      state.targetId = e.target.value;
      state.activePresetId = null;
      renderPresets();
      compileTransitionSequence();
      updateQualityDiagnostics();
      updateSideBySidePreview();
      seekTo(0);
    });
    
    el.transitionTypeSelect?.addEventListener('change', (e) => {
      state.transitionType = e.target.value;
      compileTransitionSequence();
      updateQualityDiagnostics();
      updateSideBySidePreview();
      seekTo(0);
    });
    
    el.durationSlider?.addEventListener('input', (e) => {
      state.transitionDurationMs = parseInt(e.target.value, 10);
      if (el.durationVal) el.durationVal.textContent = `${state.transitionDurationMs}ms`;
      compileTransitionSequence();
      updateQualityDiagnostics();
      updateSideBySidePreview();
    });
    
    el.btnPlay?.addEventListener('click', () => {
      state.isPlaying ? pause() : play();
    });
    el.btnRestart?.addEventListener('click', restart);
    el.btnPrev?.addEventListener('click', () => stepFrame(-1));
    el.btnNext?.addEventListener('click', () => stepFrame(1));
    
    el.btnLoop?.addEventListener('click', () => {
      state.loopMode = state.loopMode === 'loop_all' ? 'once' : 'loop_all';
      el.btnLoop.classList.toggle('active', state.loopMode === 'loop_all');
    });
    
    el.btnGuides?.addEventListener('click', () => {
      state.showGuides = !state.showGuides;
      el.btnGuides.classList.toggle('active', state.showGuides);
      renderStageFrame();
    });
    
    // Playback Speed Pills
    document.querySelectorAll('[data-speed]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-speed]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.speed = parseFloat(btn.dataset.speed);
      });
    });
    
    // Zoom Pills
    document.querySelectorAll('[data-zoom]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-zoom]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.zoom = parseFloat(btn.dataset.zoom);
        if (el.canvas) {
          el.canvas.style.transform = `scale(${state.zoom})`;
        }
      });
    });
    
    // Background Toggles
    document.querySelectorAll('[data-bg]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-bg]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.bgStyle = btn.dataset.bg;
        if (el.stageContainer) {
          el.stageContainer.className = `stage-container ${state.bgStyle}`;
        }
      });
    });
    
    // Timeline scrubber drag / click
    let isScrubbing = false;
    el.timelineTrack?.addEventListener('mousedown', (e) => {
      isScrubbing = true;
      pause();
      scrubToMouse(e);
    });
    window.addEventListener('mousemove', (e) => {
      if (isScrubbing) scrubToMouse(e);
    });
    window.addEventListener('mouseup', () => {
      isScrubbing = false;
    });
    
    function scrubToMouse(e) {
      if (!el.timelineTrack) return;
      const rect = el.timelineTrack.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const pct = x / rect.width;
      seekTo(pct * state.totalDurationMs);
    }
    
    // Export Modal Controls
    el.btnOpenExport?.addEventListener('click', () => {
      if (el.exportModal) el.exportModal.classList.add('open');
    });
    el.btnCloseExport?.addEventListener('click', () => {
      if (el.exportModal) el.exportModal.classList.remove('open');
    });
    
    document.getElementById('exportJsonBtn')?.addEventListener('click', exportTransitionDefinitionJSON);
    document.getElementById('exportManifestBtn')?.addEventListener('click', exportMascotTransitionsManifest);
    document.getElementById('exportSheetBtn')?.addEventListener('click', exportTransitionSpritesheet);
  }

  // --- Bootstrap ---
  window.addEventListener('DOMContentLoaded', () => {
    initElements();
    bindEvents();
    loadAnimationsData();
  });

})();
