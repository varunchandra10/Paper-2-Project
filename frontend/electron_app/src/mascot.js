const hitbox = document.getElementById('mascot-hitbox');
const mascot = document.getElementById('mascot');

// --- Mouse Interaction and Click-Through IPC Triggers ---

// When hovering over the robot's hitbox, register mouse events (enable clicking, dragging)
hitbox.addEventListener('mouseenter', () => {
    if (window.mascotAPI) {
        window.mascotAPI.setIgnoreMouseEvents(false);
    }
});

// When leaving the hitbox, pass mouse events through transparent pixels to the desktop
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
const dragThreshold = 5; // Allow minor movement (in pixels) during standard clicks

hitbox.addEventListener('mousedown', (e) => {
    // Only drag with left click
    if (e.button === 0) {
        isDragging = true;
        dragDistance = 0;
        startX = e.screenX;
        startY = e.screenY;
        hitbox.style.cursor = 'default';
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

// --- Sprite Sheet Configuration ---
const SHEETS = {
  standing: { src: "assets/mr_nerdy_stand_sleep-removebg-preview.png", frameCount: 3 },
  sleep: { src: "assets/mr_nerdy_stand_sleep-removebg-preview.png", frameCount: 3 },
  excite: { src: "assets/mr_nerdy_stand_to_excite-removebg-preview.png", frameCount: 3 },
  angry: { src: "assets/mr_nerd_stand_to_angry-removebg-preview.png", frameCount: 3 },
  hunch: { src: "assets/mr_nerd_stand_to_hunch-removebg-preview.png", frameCount: 3 },
  working: { src: "assets/mr_nerd_stand_to_hunch-removebg-preview.png", frameCount: 3 },
  reading: { src: "assets/mr_nerdy_stand_to_excite-removebg-preview.png", frameCount: 3 },
  idle: { src: "assets/mr_nerdy_stand_sleep-removebg-preview.png", frameCount: 3 }
};

const STATE_SHEET = {
  idle: "standing",
  sleep: "sleep",
  excite: "excite",
  angry: "angry",
  hunch: "hunch",
  working: "hunch",
  reading: "excite"
};

const images = {};
let loadedCount = 0;
const keysToLoad = ['standing', 'sleep', 'excite', 'angry', 'hunch'];

const canvas = document.getElementById("stageCanvas");
const ctx = canvas ? canvas.getContext("2d") : null;

let currentMascotState = 'idle';
let isPlaying = false;
let frameDuration = 150; // smooth 150ms frame timing

function loadImages(cb) {
  keysToLoad.forEach((key) => {
    const img = new Image();
    img.onload = () => {
      images[key] = img;
      loadedCount++;
      if (loadedCount === keysToLoad.length && cb) cb();
    };
    img.src = SHEETS[key].src;
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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function drawFrameCrossFade(sheetKey, fromIndex, toIndex, duration = 130) {
  if (!ctx || !images[sheetKey]) return;
  const sheet = SHEETS[sheetKey];
  const img = images[sheetKey];
  const frameW = img.naturalWidth / sheet.frameCount;
  const frameH = img.naturalHeight;

  const scale = Math.min(canvas.width / frameW, canvas.height / frameH);
  const drawW = frameW * scale;
  const drawH = frameH * scale;
  const dx = (canvas.width - drawW) / 2;
  const dy = canvas.height - drawH;

  const steps = 6;
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

async function playSheetSequence(sheetKey, frameOrder) {
  let currentFrame = null;
  for (const f of frameOrder) {
    if (currentFrame !== null && currentFrame !== f) {
      await drawFrameCrossFade(sheetKey, currentFrame, f, 130);
    } else {
      drawFrame(sheetKey, f);
    }
    currentFrame = f;
  }
}

const zzzContainer = document.getElementById("zzz-container");

function updateZzzOverlay(state) {
  if (!zzzContainer) return;
  if (state === "sleep" || state === "sleeping") {
    zzzContainer.classList.add("active");
  } else {
    zzzContainer.classList.remove("active");
  }
}

let pendingTargetState = null;

// Hub routing state machine: all non-idle pose changes route through standing frame 0 first
async function transitionToState(targetState) {
  if (!targetState) targetState = "idle";
  if (targetState === "working") targetState = "hunch";
  if (targetState === "sleeping") targetState = "sleep";

  if (isPlaying) {
    pendingTargetState = targetState;
    return;
  }

  if (targetState === currentMascotState) {
    const sheet = STATE_SHEET[targetState] || "standing";
    const count = SHEETS[sheet].frameCount;
    drawFrame(sheet, targetState === "idle" ? 0 : count - 1);
    if (canvas) canvas.className = targetState;
    updateZzzOverlay(targetState);
    return;
  }

  isPlaying = true;
  if (canvas) canvas.className = "";
  if (targetState !== "sleep") updateZzzOverlay(targetState);

  const steps = [];

  if (currentMascotState !== "idle") {
    const sheet = STATE_SHEET[currentMascotState] || "standing";
    const count = SHEETS[sheet].frameCount;
    steps.push({ sheet, order: Array.from({ length: count }, (_, i) => count - 1 - i) });
  }

  if (targetState !== "idle") {
    const sheet = STATE_SHEET[targetState] || "standing";
    const count = SHEETS[sheet].frameCount;
    steps.push({ sheet, order: Array.from({ length: count }, (_, i) => i) });
  }

  for (const step of steps) {
    await playSheetSequence(step.sheet, step.order);
  }

  currentMascotState = targetState;
  if (canvas) canvas.className = targetState;
  updateZzzOverlay(targetState);
  isPlaying = false;

  if (pendingTargetState && pendingTargetState !== currentMascotState) {
    const nextState = pendingTargetState;
    pendingTargetState = null;
    await transitionToState(nextState);
  } else {
    pendingTargetState = null;
  }
}

loadImages(() => {
  currentMascotState = "sleep";
  const count = SHEETS["sleep"].frameCount;
  drawFrame("sleep", count - 1);
  updateZzzOverlay("sleep");
});

// --- State Listeners (Triggered from Main Process) ---
if (window.mascotAPI) {
  window.mascotAPI.onStateChange((state) => {
    transitionToState(state);
  });
}
