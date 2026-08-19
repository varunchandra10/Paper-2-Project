const { app, BrowserWindow, screen, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

// Attempt to load native modules
let koffi = null;
let activeWin = null;
try {
    koffi = require('koffi');
} catch (e) {
    console.warn("Koffi native module not loaded; using screen fallback boundaries.", e);
}

// Global window references
let mascotWindow = null;
let activeWindowInterval = null;

// --- Win32 Taskbar Detection via Koffi ---
let SHAppBarMessage = null;
let APPBARDATA = null;

if (koffi) {
    try {
        const shell32 = koffi.load('shell32.dll');
        const RECT = koffi.struct('RECT', {
            left: 'long',
            top: 'long',
            right: 'long',
            bottom: 'long'
        });
        APPBARDATA = koffi.struct('APPBARDATA', {
            cbSize: 'uint32',
            hWnd: 'void *',
            uCallbackMessage: 'uint32',
            uEdge: 'uint32',
            rc: RECT,
            lParam: 'intptr_t'
        });
        SHAppBarMessage = shell32.stdcall('SHAppBarMessage', 'uintptr_t', ['uint32', koffi.pointer(APPBARDATA)]);
    } catch (e) {
        console.error("Failed to map shell32.dll appbar bindings:", e);
    }
}

function getTaskbarPosition() {
    if (SHAppBarMessage && APPBARDATA) {
        try {
            const abd = {};
            abd.cbSize = koffi.sizeof(APPBARDATA);
            abd.hWnd = null;
            abd.uCallbackMessage = 0;
            abd.uEdge = 0;
            abd.rc = { left: 0, top: 0, right: 0, bottom: 0 };
            abd.lParam = 0;

            const ABM_GETTASKBARPOS = 5;
            const result = SHAppBarMessage(ABM_GETTASKBARPOS, abd);
            if (result) {
                return {
                    left: abd.rc.left,
                    top: abd.rc.top,
                    right: abd.rc.right,
                    bottom: abd.rc.bottom,
                    edge: abd.uEdge // 0: Left, 1: Top, 2: Right, 3: Bottom
                };
            }
        } catch (err) {
            console.error("Win32 taskbar message call failed:", err);
        }
    }
    return null;
}

// --- Window Creation ---
function createMascotWindow() {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width: screenWidth, height: screenHeight } = primaryDisplay.size;
    const workArea = primaryDisplay.workArea;
    const scaleFactor = primaryDisplay.scaleFactor || 1.0;

    // Default dimensions for the mascot (DPI aware)
    const mascotWidth = Math.round(150 * scaleFactor);
    const mascotHeight = Math.round(180 * scaleFactor);

    // Initial positioning: Default to bottom-right
    let posX = screenWidth - mascotWidth - Math.round(20 * scaleFactor);
    let posY = screenHeight - mascotHeight - Math.round(60 * scaleFactor);

    // Dynamic positioning using Win32 API
    const taskbar = getTaskbarPosition();
    if (taskbar) {
        // If taskbar is on the right side, position just to the left of it
        if (taskbar.edge === 2) {
            posX = taskbar.left - mascotWidth - Math.round(10 * scaleFactor);
            posY = screenHeight - mascotHeight - Math.round(20 * scaleFactor);
        } else {
            // Taskbar is at bottom, top, or left. Mascot stays on the right side of the screen.
            posX = screenWidth - mascotWidth - Math.round(20 * scaleFactor);
            if (taskbar.edge === 3) {
                // Bottom taskbar
                posY = taskbar.top - mascotHeight;
            } else {
                // Top or Left taskbar
                posY = screenHeight - mascotHeight - Math.round(20 * scaleFactor);
            }
        }
    } else {
        // Fallback using cross-platform workArea
        posX = workArea.x + workArea.width - mascotWidth - Math.round(10 * scaleFactor);
        posY = workArea.y + workArea.height - mascotHeight;
    }

    mascotWindow = new BrowserWindow({
        width: mascotWidth,
        height: mascotHeight,
        x: posX,
        y: posY,
        type: 'toolbar', // Prevents showing window control menus on taskbar
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        resizable: false,
        skipTaskbar: true,
        hasShadow: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    mascotWindow.loadFile(path.join(__dirname, 'mascot.html'));

    // Handle mouse pass-through regions programmatically
    ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
        const win = BrowserWindow.fromWebContents(event.sender);
        if (win) {
            win.setIgnoreMouseEvents(ignore, options);
        }
    });

    // Cleanup
    mascotWindow.on('closed', () => {
        mascotWindow = null;
    });
}

// --- Active Window Tracking ---
async function startActiveWindowPolling() {
    // Dynamic import to support ESM-only active-win in CommonJS
    try {
        const activeWinModule = await import('active-win');
        activeWin = activeWinModule.default;
    } catch (e) {
        console.warn("Could not import active-win ESM module.", e);
    }

    if (!activeWin) return;

    activeWindowInterval = setInterval(async () => {
        try {
            const winDetails = await activeWin();
            if (winDetails && mascotWindow) {
                const title = (winDetails.title || "").toLowerCase();
                const ownerName = (winDetails.owner ? winDetails.owner.name : "").toLowerCase();

                // Match keywords indicating paper reading or research process
                const isPaper = 
                    title.includes(".pdf") || 
                    title.includes("arxiv") || 
                    title.includes("transformer") || 
                    title.includes("convolutional") || 
                    ownerName.includes("acrobat") || 
                    ownerName.includes("chrome") && title.includes("paper");

                if (isPaper) {
                    mascotWindow.webContents.send('state-change', 'reading');
                } else {
                    mascotWindow.webContents.send('state-change', 'idle');
                }
            }
        } catch (err) {
            // Ignore polling errors for OS protected windows
        }
    }, 2000);
}

// --- Lifecycle Event Listeners ---
app.whenReady().then(() => {
    createMascotWindow();
    startActiveWindowPolling();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createMascotWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (activeWindowInterval) {
        clearInterval(activeWindowInterval);
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
