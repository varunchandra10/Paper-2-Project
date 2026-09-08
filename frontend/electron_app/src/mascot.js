const hitbox = document.getElementById('mascot-hitbox');
const mascot = document.getElementById('mascot');
const canvas = document.getElementById('stageCanvas');
const ctx = canvas ? canvas.getContext('2d') : null;
const zzzContainer = document.getElementById('zzz-container');

// --- Mouse Interaction and Click-Through IPC Triggers ---

hitbox.addEventListener('mouseenter', () => {
    if (window.mascotAPI) {
        window.mascotAPI.setIgnoreMouseEvents(false);
    }
});

hitbox.addEventListener('mouseleave', () => {
    if (window.mascotAPI) {
        window.mascotAPI.setIgnoreMouseEvents(true, { forward: true });
    }
});

// --- Custom Borderless Window Dragging ---
let isDragging = false;
let startX = 0;
let startY = 0;
let dragDistance = 0;
const dragThreshold = 5;

hitbox.addEventListener('mousedown', (e) => {
    if (e.button === 0) {
        isDragging = true;
        dragDistance = 0;
        startX = e.screenX;
        startY = e.screenY;
        hitbox.style.cursor = 'default';
        recordUserActivity();
    }
});

window.addEventListener('mousemove', (e) => {
    if (isDragging && window.mascotAPI) {
        const deltaX = e.screenX - startX;
        const deltaY = e.screenY - startY;
        dragDistance += Math.abs(deltaX) + Math.abs(deltaY);
        startX = e.screenX;
        startY = e.screenY;
        window.mascotAPI.dragWindow({ deltaX, deltaY });
    }
});

window.addEventListener('mouseup', () => {
    if (isDragging) {
        isDragging = false;
        hitbox.style.cursor = 'default';
        if (window.mascotAPI) {
            window.mascotAPI.dragEnd();
            
            // If mouse movement was negligible, treat it as a click and toggle the panel
            if (dragDistance < dragThreshold) {
                window.mascotAPI.togglePanel();
            }
        }
    }
});

// --- Multi-Character Sprite Sheet Configurations ---
const CHARACTER_SHEETS = {
  mr_nerdy: {
    sleep: { src: "assets/mr_nerdy/mr_nerdy_sleeping.png", frameCount: 3 },
    excite: { src: "assets/mr_nerdy/mr_nerdy_excited.png", frameCount: 3 },
    angry: { src: "assets/mr_nerdy/mr_nerdy_angry.png", frameCount: 3 },
    hunch: { src: "assets/mr_nerdy/mr_nerdy_huncing.png", frameCount: 3 },
    wave: { src: "assets/mr_nerdy/mr_nerdy_waving.png", frameCount: 3 },
    blink: { src: "assets/mr_nerdy/mr_nerdy_eye_blinking.png", frameCount: 3 },
    catching: { src: "assets/mr_nerdy/mr_nerdy_document_catching.png", frameCount: 3 },
    thinking: { src: "assets/mr_nerdy/mr_nerdy_thinking.png", frameCount: 3 },
    tired: { src: "assets/mr_nerdy/mr_nerdy_tired.png", frameCount: 3 },
    having_sipping: { src: "assets/mr_nerdy/mr_nerdy_having_sipping.png", frameCount: 3 },
    confused: { src: "assets/mr_nerdy/mr_nerdy_confused.png", frameCount: 3 },
    peeking: { src: "assets/mr_nerdy/mr_nerdy_peeking.png", frameCount: 3 },
    standing: { src: "assets/mr_nerdy/mr_nerdy_standing.png", frameCount: 1 }
  },
  ms_nerdy: {
    sleep: { src: "assets/ms_nerdy/ms_nerdy_sleeping.png", frameCount: 3 },
    excite: { src: "assets/ms_nerdy/ms_nerdy_excited.png", frameCount: 3 },
    angry: { src: "assets/ms_nerdy/ms_nerdy_angry.png", frameCount: 3 },
    hunch: { src: "assets/ms_nerdy/ms_nerdy_hunching.png", frameCount: 3 },
    wave: { src: "assets/ms_nerdy/ms_nerdy_hand_waving.png", frameCount: 3 },
    blink: { src: "assets/ms_nerdy/ms_nerdy_blinking.png", frameCount: 3 },
    catching: { src: "assets/ms_nerdy/ms_nerdy_document_catching.png", frameCount: 3 },
    thinking: { src: "assets/ms_nerdy/ms_nerdy_thinking.png", frameCount: 3 },
    tired: { src: "assets/ms_nerdy/ms_nerdy_thinking.png", frameCount: 3 },
    having_sipping: { src: "assets/ms_nerdy/ms_nerdy_sipping_coffee.png", frameCount: 3 },
    confused: { src: "assets/ms_nerdy/ms_nerdy_confused.png", frameCount: 3 },
    peeking: { src: "assets/ms_nerdy/ms_nerdy_peeking.png", frameCount: 3 },
    standing: { src: "assets/ms_nerdy/ms_nerdy_standing.png", frameCount: 1 }
  },
  mr_nerd: {
    sleep: { src: "assets/mr_nerd/mr_nerd_sleeping.png", frameCount: 3 },
    excite: { src: "assets/mr_nerd/mr_nerd_excited.png", frameCount: 3 },
    angry: { src: "assets/mr_nerd/mr_nerd_angry.png", frameCount: 3 },
    hunch: { src: "assets/mr_nerd/mr_nerd_hunching.png", frameCount: 3 },
    wave: { src: "assets/mr_nerd/mr_nerd_waving.png", frameCount: 3 },
    blink: { src: "assets/mr_nerd/mr_nerd_blinking.png", frameCount: 3 },
    catching: { src: "assets/mr_nerd/mr_nerd_document_catching.png", frameCount: 3 },
    thinking: { src: "assets/mr_nerd/mr_nerd_thinking.png", frameCount: 3 },
    tired: { src: "assets/mr_nerd/mr_nerd_thinking.png", frameCount: 3 },
    having_sipping: { src: "assets/mr_nerd/mr_nerd_coffee_sipping.png", frameCount: 3 },
    confused: { src: "assets/mr_nerd/mr_nerd_confused.png", frameCount: 3 },
    peeking: { src: "assets/mr_nerd/mr_nerd_peeking.png", frameCount: 3 },
    standing: { src: "assets/mr_nerd/mr_nerd_standing.png", frameCount: 1 }
  },
  ms_nerd: {
    sleep: { src: "assets/ms_nerd/ms_nerd_sleeping.png", frameCount: 3 },
    excite: { src: "assets/ms_nerd/ms_nerd_excited.png", frameCount: 3 },
    angry: { src: "assets/ms_nerd/ms_nerd_angry.png", frameCount: 3 },
    hunch: { src: "assets/ms_nerd/ms_nerd_hunching.png", frameCount: 3 },
    wave: { src: "assets/ms_nerd/ms_nerd_hii.png", frameCount: 3 },
    blink: { src: "assets/ms_nerd/ms_nerd_eye_blinking.png", frameCount: 3 },
    catching: { src: "assets/ms_nerd/ms_nerd_document_catching.png", frameCount: 3 },
    thinking: { src: "assets/ms_nerd/ms_nerd_thinking.png", frameCount: 3 },
    tired: { src: "assets/ms_nerd/ms_nerd_thinking.png", frameCount: 3 },
    having_sipping: { src: "assets/ms_nerd/ms_nerd_coffee_sipping.png", frameCount: 3 },
    confused: { src: "assets/ms_nerd/ms_nerd_confused.png", frameCount: 3 },
    peeking: { src: "assets/ms_nerd/ms_nerd_peeking.png", frameCount: 3 },
    standing: { src: "assets/ms_nerd/ms_nerd_standing.png", frameCount: 1 }
  }
};

let activeSkin = 'mr_nerdy';
let SHEETS = { ...CHARACTER_SHEETS.mr_nerdy };


const STATE_SHEET = {
  idle: "blink",
  sleep: "sleep",
  sleeping: "sleep",
  excite: "excite",
  excited: "excite",
  angry: "angry",
  hunch: "hunch",
  working: "hunch",
  reading: "excite",
  wave: "wave",
  catching: "catching",
  thinking: "thinking",
  tired: "tired",
  having_sipping: "having_sipping",
  confused: "confused",
  peeking: "peeking",
  standing: "standing"
};

let TRANSITIONS = null;

async function loadTransitionsConfig() {
  try {
    const res = await fetch('mascot_transitions.json');
    if (res.ok) {
      TRANSITIONS = await res.json();
      console.log('[Mascot Script] Loaded transitions from mascot_transitions.json');
    }
  } catch (err) {
    console.warn('[Mascot Script] Fallback to embedded transitions.', err);
  }
}
loadTransitionsConfig();

const images = {};
let loadedCount = 0;
const keysToLoad = Object.keys(SHEETS);

let currentMascotState = 'sleep';
let isPlaying = false;
let imagesLoaded = false;
let pendingTargetState = null;
let queuedInitialState = null;

// Timers
let blinkTimeout = null;
let lastActivityTime = Date.now();
let inactivityInterval = null;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function updateZzzOverlay(state) {
  if (!zzzContainer) return;
  if (state === "sleep" || state === "sleeping") {
    zzzContainer.classList.add("active");
  } else {
    zzzContainer.classList.remove("active");
  }
}

function loadImages(cb) {
  const keysToLoad = Object.keys(SHEETS);
  let loadedCount = 0;
  imagesLoaded = false;
  console.log(`[Mascot Script] Loading ${keysToLoad.length} sprite sheets for skin '${activeSkin}'...`);
  keysToLoad.forEach((key) => {
    const img = new Image();
    img.onload = () => {
      images[key] = img;
      loadedCount++;
      console.log(`[Mascot Script] Loaded sprite '${key}' (${img.naturalWidth}x${img.naturalHeight}) [${loadedCount}/${keysToLoad.length}]`);
      if (loadedCount === keysToLoad.length) {
        imagesLoaded = true;
        if (cb) cb();
        if (queuedInitialState) {
          const next = queuedInitialState;
          queuedInitialState = null;
          transitionToState(next);
        }
      }
    };
    img.onerror = (err) => {
      console.error(`[Mascot Script] FAILED to load sprite '${key}' at: ${SHEETS[key]?.src}`, err);
      loadedCount++;
      if (loadedCount === keysToLoad.length) {
        imagesLoaded = true;
        if (cb) cb();
      }
    };
    img.src = SHEETS[key].src;
  });
}

function setSkin(skinId) {
  const normalized = (skinId || 'mr_nerdy').replace('-', '_');
  if (normalized === activeSkin && imagesLoaded) return;
  if (!CHARACTER_SHEETS[normalized]) {
    console.warn(`[Mascot Script] Unknown skin '${skinId}', fallback to mr_nerdy`);
    activeSkin = 'mr_nerdy';
  } else {
    activeSkin = normalized;
  }
  SHEETS = { ...CHARACTER_SHEETS[activeSkin] };
  console.log(`[Mascot Script] Mascot skin changed to '${activeSkin}'`);
  loadImages(() => {
    const sheetKey = STATE_SHEET[currentMascotState] || 'standing';
    drawFrame(sheetKey, 0);
  });
}

function drawFrame(sheetKey, frameIndex) {
  if (!ctx || !images[sheetKey]) return;
  const sheet = SHEETS[sheetKey];
  const img = images[sheetKey];
  const frameW = img.naturalWidth / sheet.frameCount;
  const frameH = img.naturalHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const scale = Math.min(canvas.width / frameW, canvas.height / frameH);
  const drawW = frameW * scale;
  const drawH = frameH * scale;
  const dx = (canvas.width - drawW) / 2;
  const dy = canvas.height - drawH;

  ctx.drawImage(
    img,
    frameIndex * frameW, 0, frameW, frameH,
    dx, dy, drawW, drawH
  );
}

async function drawFrameCrossFade(sheetKey, fromIndex, toIndex, duration = 0) {
  if (duration <= 0 || !ctx || !images[sheetKey]) {
    drawFrame(sheetKey, toIndex);
    return;
  }
  const sheet = SHEETS[sheetKey];
  const img = images[sheetKey];
  const frameW = img.naturalWidth / sheet.frameCount;
  const frameH = img.naturalHeight;

  const scale = Math.min(canvas.width / frameW, canvas.height / frameH);
  const drawW = frameW * scale;
  const drawH = frameH * scale;
  const dx = (canvas.width - drawW) / 2;
  const dy = canvas.height - drawH;

  const steps = 5;
  const stepMs = Math.max(12, Math.round(duration / steps));

  for (let i = 1; i <= steps; i++) {
    const alpha = i / steps;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.globalAlpha = 1 - alpha;
    ctx.drawImage(
      img,
      fromIndex * frameW, 0, frameW, frameH,
      dx, dy, drawW, drawH
    );

    ctx.globalAlpha = alpha;
    ctx.drawImage(
      img,
      toIndex * frameW, 0, frameW, frameH,
      dx, dy, drawW, drawH
    );

    ctx.globalAlpha = 1.0;
    await sleep(stepMs);
  }

  drawFrame(sheetKey, toIndex);
}

async function playSheetSequence(sheetKey, frameOrder, crossFadeDuration = 0, holdDuration = 120) {
  let currentFrame = null;
  for (const f of frameOrder) {
    if (currentFrame !== null && currentFrame !== f && crossFadeDuration > 0) {
      await drawFrameCrossFade(sheetKey, currentFrame, f, crossFadeDuration);
    } else {
      drawFrame(sheetKey, f);
    }
    if (holdDuration > 0) {
      await sleep(holdDuration);
    }
    currentFrame = f;
  }
}

// --- Idle Eye Blinking (1 or 2 blinks with 10-15s gap) ---
let isBlinkActive = false;

async function playIdleBlink() {
  if (currentMascotState !== 'idle' || isPlaying || isBlinkActive) return;
  isBlinkActive = true;

  // Randomly trigger 1 or 2 eye blinks (50% chance each)
  const isDouble = Math.random() < 0.5;
  const blinkFrames = isDouble 
    ? [0, 1, 2, 1, 0, 1, 2, 1, 0] 
    : [0, 1, 2, 1, 0];

  for (const f of blinkFrames) {
    if (currentMascotState !== 'idle' || isPlaying) break;
    drawFrame('blink', f);
    await sleep(120);
  }

  if (currentMascotState === 'idle' && !isPlaying) {
    drawFrame('blink', 0);
  }
  isBlinkActive = false;
}

function scheduleNextBlink() {
  if (blinkTimeout) {
    clearTimeout(blinkTimeout);
    blinkTimeout = null;
  }
  if (currentMascotState !== 'idle') return;

  // 10 to 15 seconds gap between each 1 or 2 eye blinks
  const delayMs = Math.floor(Math.random() * 5000) + 10000;
  blinkTimeout = setTimeout(async () => {
    if (currentMascotState === 'idle' && !isPlaying) {
      await playIdleBlink();
    }
    if (currentMascotState === 'idle') {
      scheduleNextBlink();
    }
  }, delayMs);
}

function startIdleBlinkLoop() {
  stopIdleBlinkLoop();
  scheduleNextBlink();
}

function stopIdleBlinkLoop() {
  if (blinkTimeout) {
    clearTimeout(blinkTimeout);
    blinkTimeout = null;
  }
  isBlinkActive = false;
}

const startContinuousBlinkLoop = startIdleBlinkLoop;
const stopContinuousBlinkLoop = stopIdleBlinkLoop;

// --- Inactivity Timeout Management ---
function recordUserActivity() {
  lastActivityTime = Date.now();
  // While panel is closed and mascot is asleep, do NOT leave sleep on mousemove!
  if (currentMascotState === 'sleep') return;
  if (currentMascotState === 'angry' || currentMascotState === 'tired') {
    transitionToState('idle');
  }
}

function startInactivityCheck() {
  if (inactivityInterval) clearInterval(inactivityInterval);
  inactivityInterval = setInterval(() => {
    // Only evaluate inactivity when in panel-open states (not sleeping, not actively working/thinking)
    if (currentMascotState === 'sleep' || currentMascotState === 'hunch' || currentMascotState === 'thinking') {
      lastActivityTime = Date.now();
      return;
    }
    const elapsed = Date.now() - lastActivityTime;
    if (elapsed >= 180000 && currentMascotState !== 'tired') {
      transitionToState('tired');
    } else if (elapsed >= 90000 && elapsed < 180000 && currentMascotState !== 'angry' && currentMascotState !== 'tired') {
      transitionToState('angry');
    }
  }, 2000);
}

// Wire user activity triggers
hitbox.addEventListener('mousemove', recordUserActivity);
window.addEventListener('mousemove', recordUserActivity);
window.addEventListener('keydown', recordUserActivity);

if (window.mascotAPI && window.mascotAPI.onUserActivity) {
  window.mascotAPI.onUserActivity(() => {
    recordUserActivity();
  });
}

// --- Wave Intro (Wakes up to standing, single wave 0 -> 1 -> 2 -> 1 -> 0, stays in standing) ---
async function runWaveIntro() {
  stopContinuousBlinkLoop();
  isPlaying = true;
  updateZzzOverlay('idle');

  // 1. Wake up from sleep to standing (2 -> 1 -> 0) with snappy 120ms frames
  if (currentMascotState === 'sleep') {
    drawFrame('sleep', 2);
    await sleep(120);
    drawFrame('sleep', 1);
    await sleep(120);
    drawFrame('sleep', 0);
    await sleep(120);
  }

  // 2. Single wave transition: 0 -> 1 -> 2 -> 1 -> 0 (fade 0ms, hold 120ms)
  drawFrame('wave', 0);
  await sleep(120);
  drawFrame('wave', 1);
  await sleep(120);
  drawFrame('wave', 2);
  await sleep(120);
  drawFrame('wave', 1);
  await sleep(120);
  drawFrame('wave', 0);
  await sleep(120);

  // 3. Ends in standing position and begins eye blinking loop
  currentMascotState = 'idle';
  drawFrame('blink', 0);
  isPlaying = false;

  lastActivityTime = Date.now();
  startContinuousBlinkLoop();
  startInactivityCheck();
}

// --- Action States: Catching & Excited (Starts in standing, ends in standing) ---
async function runCatching() {
  stopContinuousBlinkLoop();
  isPlaying = true;
  updateZzzOverlay('idle');

  // Settle to base standing 0 if currently in another posture
  if (currentMascotState !== 'idle') {
    const prevSheet = STATE_SHEET[currentMascotState] || 'blink';
    const count = SHEETS[prevSheet].frameCount;
    await playSheetSequence(prevSheet, Array.from({ length: count }, (_, i) => count - 1 - i), 0, 120);
  }

  // Catching sequence: 0 -> 1 -> 2, hold document caught, then 1 -> 0
  await playSheetSequence('catching', [0, 1, 2], 0, 120);
  await sleep(800);
  await playSheetSequence('catching', [2, 1, 0], 0, 120);

  currentMascotState = 'idle';
  drawFrame('blink', 0);
  isPlaying = false;

  lastActivityTime = Date.now();
  startContinuousBlinkLoop();
}

async function runExcited() {
  stopContinuousBlinkLoop();
  isPlaying = true;
  updateZzzOverlay('idle');

  if (currentMascotState !== 'idle') {
    const prevSheet = STATE_SHEET[currentMascotState] || 'blink';
    const count = SHEETS[prevSheet].frameCount;
    await playSheetSequence(prevSheet, Array.from({ length: count }, (_, i) => count - 1 - i), 0, 120);
  }

  // Excited celebration: 0 -> 1 -> 2 -> 1 -> 0
  await playSheetSequence('excite', [0, 1, 2, 1, 0], 0, 120);

  currentMascotState = 'idle';
  drawFrame('blink', 0);
  isPlaying = false;

  lastActivityTime = Date.now();
  startContinuousBlinkLoop();
}

async function playConfiguredTransition(stateName) {
  const cfg = TRANSITIONS ? TRANSITIONS[stateName] : null;
  if (!cfg || !cfg.steps || !cfg.steps.length) return false;

  stopContinuousBlinkLoop();
  isPlaying = true;

  let prevStep = null;
  for (let i = 0; i < cfg.steps.length; i++) {
    const step = cfg.steps[i];
    updateZzzOverlay(step.zzz ? 'sleep' : 'idle');

    if (step.fade > 0 && prevStep && prevStep.sheet === step.sheet && prevStep.frame !== step.frame) {
      await drawFrameCrossFade(step.sheet, prevStep.frame, step.frame, step.fade);
    } else {
      drawFrame(step.sheet, step.frame);
    }

    if (step.hold > 0) {
      await sleep(step.hold);
    }
    prevStep = step;
  }

  currentMascotState = (stateName === 'wave-intro' || stateName === 'wave') ? 'idle' : stateName;
  isPlaying = false;
  return true;
}

// --- Hub Routing State Machine ---
async function transitionToState(targetState) {
  if (!targetState) targetState = 'idle';
  if (targetState === 'sleeping') targetState = 'sleep';
  if (targetState === 'working') targetState = 'hunch';
  if (targetState === 'reading') targetState = 'excite';

  // 1. Guard against re-entering the current state (prevents stand -> sleep loops!)
  if (targetState === currentMascotState) {
    if (targetState === 'sleep') {
      drawFrame('sleep', 2);
      updateZzzOverlay('sleep');
    } else if (targetState === 'idle') {
      startContinuousBlinkLoop();
    }
    return;
  }

  // Stop previous continuous blink loop immediately upon any transition
  stopContinuousBlinkLoop();

  if (isPlaying) {
    pendingTargetState = targetState;
    return;
  }

  // 2. Waving Intro / Panel Open: Mascot stands up and says "hii"
  if (targetState === 'wave-intro') {
    await runWaveIntro();
    checkPendingState();
    return;
  }

  // 3. Bedtime / Panel Closed: Stand -> Sleep one-time clean transition (NO loop)
  if (targetState === 'sleep') {
    isPlaying = true;
    if (inactivityInterval) clearInterval(inactivityInterval);

    // If currently in a non-idle pose (and not sleep), smoothly return to base standing 0 first
    if (currentMascotState !== 'idle' && currentMascotState !== 'sleep') {
      const fromSheet = STATE_SHEET[currentMascotState] || 'blink';
      const count = SHEETS[fromSheet].frameCount;
      const returnOrder = Array.from({ length: count }, (_, i) => count - 1 - i);
      await playSheetSequence(fromSheet, returnOrder, 0, 120);
    }

    // Stand -> Sleep one-time transition (0 -> 1 -> 2)
    drawFrame('sleep', 0);
    await sleep(120);
    drawFrame('sleep', 1);
    await sleep(120);
    drawFrame('sleep', 2);

    // Stays asleep resting at frame 2 with ZZZ
    updateZzzOverlay('sleep');
    currentMascotState = 'sleep';
    isPlaying = false;
    checkPendingState();
    return;
  }

  // 4. Wake-Up directly to idle (if requested) -> stand and wave hii
  if (currentMascotState === 'sleep' && targetState === 'idle') {
    await runWaveIntro();
    checkPendingState();
    return;
  }

  // 5. Action States: Catching & Excited
  if (targetState === 'catching') {
    await runCatching();
    checkPendingState();
    return;
  }
  if (targetState === 'excited' || targetState === 'excite') {
    await runExcited();
    checkPendingState();
    return;
  }

  // 6. User Configured Transitions
  if (TRANSITIONS && TRANSITIONS[targetState]) {
    await playConfiguredTransition(targetState);
    if (targetState === 'idle') {
      lastActivityTime = Date.now();
      startContinuousBlinkLoop();
      startInactivityCheck();
    }
    checkPendingState();
    return;
  }

  // 7. Generic Pose State Transition (Advance from standing 0 to target pose)
  isPlaying = true;
  updateZzzOverlay(targetState);

  if (currentMascotState !== 'idle' && currentMascotState !== 'sleep') {
    const fromSheet = STATE_SHEET[currentMascotState] || 'blink';
    const count = SHEETS[fromSheet].frameCount;
    const returnOrder = Array.from({ length: count }, (_, i) => count - 1 - i);
    await playSheetSequence(fromSheet, returnOrder, 0, 120);
  }

  if (targetState !== 'idle') {
    const toSheet = STATE_SHEET[targetState] || 'blink';
    const count = SHEETS[toSheet].frameCount;
    const advanceOrder = Array.from({ length: count }, (_, i) => i);
    await playSheetSequence(toSheet, advanceOrder, 0, 120);
  } else {
    drawFrame('blink', 0);
  }

  currentMascotState = targetState;
  isPlaying = false;

  if (targetState === 'idle') {
    lastActivityTime = Date.now();
    startContinuousBlinkLoop();
    startInactivityCheck();
  }

  checkPendingState();
}

async function checkPendingState() {
  if (pendingTargetState && pendingTargetState !== currentMascotState) {
    const next = pendingTargetState;
    pendingTargetState = null;
    await transitionToState(next);
  } else {
    pendingTargetState = null;
  }
}

// Initial Boot
loadImages(() => {
  currentMascotState = 'sleep';
  drawFrame('sleep', 2);
  updateZzzOverlay('sleep');
});

// --- State & Skin Listeners (Triggered from Main Process via IPC) ---
if (window.mascotAPI) {
  window.mascotAPI.onStateChange((state) => {
    if (!imagesLoaded) {
      queuedInitialState = state;
      return;
    }
    transitionToState(state);
  });

  if (window.mascotAPI.onMascotSkinChange) {
    window.mascotAPI.onMascotSkinChange((skinId) => {
      setSkin(skinId);
    });
  }

  if (window.mascotAPI.getMascotSkin) {
    window.mascotAPI.getMascotSkin().then((skinId) => {
      if (skinId) setSkin(skinId);
    }).catch(() => {});
  }
}

