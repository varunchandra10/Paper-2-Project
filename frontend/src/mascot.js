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
