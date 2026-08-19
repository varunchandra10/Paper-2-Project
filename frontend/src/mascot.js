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
        hitbox.style.cursor = 'grabbing';
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
        hitbox.style.cursor = 'grab';
        if (window.mascotAPI) {
            window.mascotAPI.dragEnd();
            
            // If mouse movement was negligible, treat it as a click and toggle the panel
            if (dragDistance < dragThreshold) {
                window.mascotAPI.togglePanel();
            }
        }
    }
});

// --- State Listeners (Triggered from Main Process) ---
if (window.mascotAPI) {
    window.mascotAPI.onStateChange((state) => {
        // Reset classes
        mascot.className = 'mascot-character';

        // Apply new animation state class
        switch (state) {
            case 'sleeping':
                mascot.classList.add('sleeping');
                break;
            case 'reading':
                mascot.classList.add('reading');
                break;
            case 'working':
                mascot.classList.add('working');
                break;
            case 'idle':
            default:
                mascot.classList.add('idle');
                break;
        }
    });
}
