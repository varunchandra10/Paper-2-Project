const { app, BrowserWindow, screen, ipcMain, globalShortcut, dialog } = require('electron');
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

// --- Window Creation & DPI/Multi-Monitor Management ---
let currentDisplayId = null;
let currentScaleFactor = 1.0;

function positionMascotDefault(nearestDisplay) {
    if (!mascotWindow) return;

    const scaleFactor = nearestDisplay.scaleFactor || 1.0;
    const { width: screenWidth, height: screenHeight, x: displayX, y: displayY } = nearestDisplay.bounds;

    currentDisplayId = nearestDisplay.id;
    currentScaleFactor = scaleFactor;

    const mascotWidth = Math.round(120 * scaleFactor);
    const mascotHeight = Math.round(144 * scaleFactor);

    // Initial position on monitor: Bottom-Right
    let posX = displayX + screenWidth - mascotWidth - Math.round(20 * scaleFactor);
    let posY = displayY + screenHeight - mascotHeight - Math.round(60 * scaleFactor);

    const taskbar = getTaskbarPosition();
    const primaryDisplay = screen.getPrimaryDisplay();

    // Win32 API taskbar checks apply to primary display
    if (taskbar && nearestDisplay.id === primaryDisplay.id) {
        if (taskbar.edge === 2) {
            posX = taskbar.left - mascotWidth - Math.round(10 * scaleFactor);
            posY = displayY + screenHeight - mascotHeight - Math.round(20 * scaleFactor);
        } else {
            posX = displayX + screenWidth - mascotWidth - Math.round(20 * scaleFactor);
            if (taskbar.edge === 3) {
                posY = taskbar.top - mascotHeight;
            } else {
                posY = displayY + screenHeight - mascotHeight - Math.round(20 * scaleFactor);
            }
        }
    } else {
        // Fallback or secondary display using workArea (excludes native taskbars)
        const workArea = nearestDisplay.workArea;
        posX = workArea.x + workArea.width - mascotWidth - Math.round(10 * scaleFactor);
        posY = workArea.y + workArea.height - mascotHeight;
    }

    mascotWindow.setBounds({
        x: posX,
        y: posY,
        width: mascotWidth,
        height: mascotHeight
    });
}

function handleMonitorChange(nearestDisplay) {
    if (!mascotWindow) return;

    const scaleFactor = nearestDisplay.scaleFactor || 1.0;

    // Check if we've already scaled/positioned for this display and scale
    if (nearestDisplay.id === currentDisplayId && scaleFactor === currentScaleFactor) {
        return;
    }

    currentDisplayId = nearestDisplay.id;
    currentScaleFactor = scaleFactor;

    const mascotWidth = Math.round(120 * scaleFactor);
    const mascotHeight = Math.round(144 * scaleFactor);
    const bounds = mascotWindow.getBounds();

    // Resize window to match the new monitor DPI scale while keeping its custom drag coordinates
    mascotWindow.setBounds({
        x: bounds.x,
        y: bounds.y,
        width: mascotWidth,
        height: mascotHeight
    });
}

// --- Global IPC Listeners (Single Registration) ---
ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
        win.setIgnoreMouseEvents(ignore, options);
    }
});

ipcMain.on('drag-window', (event, delta) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
        const bounds = win.getBounds();
        const targetWidth = Math.round(120 * currentScaleFactor);
        const targetHeight = Math.round(144 * currentScaleFactor);
        
        // Move window but strictly lock dimensions to target size
        win.setBounds({
            x: bounds.x + delta.deltaX,
            y: bounds.y + delta.deltaY,
            width: targetWidth,
            height: targetHeight
        });
    }
});

ipcMain.on('drag-end', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
        const bounds = win.getBounds();
        console.log(`[Drag End] Final bounds: [${bounds.x}, ${bounds.y}, ${bounds.width}, ${bounds.height}]`);
        const centerPoint = {
            x: bounds.x + bounds.width / 2,
            y: bounds.y + bounds.height / 2
        };
        const activeDisplay = screen.getDisplayNearestPoint(centerPoint);
        handleMonitorChange(activeDisplay);
    }
});

ipcMain.on('toggle-panel', () => {
    togglePanel();
});

ipcMain.on('upload-pdf', (event, { filePath, type }) => {
    try {
        if (!filePath || typeof filePath !== 'string') {
            throw new Error("Invalid or empty file path received.");
        }
        const uploadsDir = path.join(__dirname, 'uploads');
        if (!fs.existsSync(uploadsDir)) {
            fs.mkdirSync(uploadsDir, { recursive: true });
        }

        const filename = path.basename(filePath);
        const destPath = path.join(uploadsDir, filename);

        // Copy file locally to uploads folder
        fs.copyFileSync(filePath, destPath);

        event.reply('upload-status', { success: true, filename, type });
    } catch (err) {
        console.error("File upload/copy error:", err);
        event.reply('upload-status', { success: false, error: err.message, type });
    }
});

ipcMain.on('open-file-selector', (event, type) => {
    const isDocx = (type === 'docx');
    const dialogFilters = isDocx 
        ? [ { name: 'Word Documents', extensions: ['docx', 'doc'] } ]
        : [ { name: 'PDF Papers', extensions: ['pdf'] } ];

    dialog.showOpenDialog({
        properties: ['openFile'],
        filters: dialogFilters
    }).then(result => {
        if (!result.canceled && result.filePaths.length > 0) {
            const filePath = result.filePaths[0];
            const filename = path.basename(filePath);

            try {
                const uploadsDir = path.join(__dirname, 'uploads');
                if (!fs.existsSync(uploadsDir)) {
                    fs.mkdirSync(uploadsDir, { recursive: true });
                }

                const destPath = path.join(uploadsDir, filename);
                fs.copyFileSync(filePath, destPath);

                event.reply('upload-status', { success: true, filename, type });
            } catch (err) {
                event.reply('upload-status', { success: false, error: err.message, type });
            }
        }
    }).catch(err => {
        console.error("File dialog error:", err);
        event.reply('upload-status', { success: false, error: err.message, type });
    });
});

// --- Sidebar Control Panel Window ---
let panelWindow = null;

function getPanelPosition(scaleFactor, workArea) {
    const panelWidth = Math.round(340 * scaleFactor);
    const panelHeight = Math.round(480 * scaleFactor);

    if (mascotWindow) {
        try {
            const mascotBounds = mascotWindow.getBounds();
            // Center the panel horizontally relative to the mascot
            let posX = mascotBounds.x + Math.round((mascotBounds.width - panelWidth) / 2);
            // Clamp horizontal bounds within the screen workArea
            posX = Math.min(posX, workArea.x + workArea.width - panelWidth - Math.round(10 * scaleFactor));
            posX = Math.max(posX, workArea.x + Math.round(10 * scaleFactor));

            // Position directly above the mascot's head (with an 8px spacing gap)
            let posY = mascotBounds.y - panelHeight - Math.round(8 * scaleFactor);
            // If it goes off the top of the monitor, push it down but keep it within bounds
            if (posY < workArea.y) {
                posY = workArea.y + Math.round(10 * scaleFactor);
            }

            return { x: posX, y: posY, width: panelWidth, height: panelHeight };
        } catch (e) {
            console.error("Failed to read mascot bounds during panel positioning:", e);
        }
    }

    // Default Fallback: Bottom-right of screen
    return {
        x: workArea.x + workArea.width - panelWidth - Math.round(10 * scaleFactor),
        y: workArea.y + workArea.height - panelHeight - Math.round(10 * scaleFactor),
        width: panelWidth,
        height: panelHeight
    };
}

function createPanelWindow() {
    const primaryDisplay = screen.getPrimaryDisplay();
    const workArea = primaryDisplay.workArea;
    const scaleFactor = primaryDisplay.scaleFactor || 1.0;

    const bounds = getPanelPosition(scaleFactor, workArea);

    panelWindow = new BrowserWindow({
        width: bounds.width,
        height: bounds.height,
        x: bounds.x,
        y: bounds.y,
        frame: false,
        resizable: false,
        alwaysOnTop: true,
        show: false, // Start hidden
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    // Make the panel standard floating level, so the mascot ('screen-saver') overlays it
    panelWindow.setAlwaysOnTop(true, 'floating');

    panelWindow.loadFile(path.join(__dirname, 'panel.html'));

    panelWindow.on('closed', () => {
        panelWindow = null;
    });
}

function togglePanel() {
    if (!panelWindow) {
        createPanelWindow();
    }

    if (panelWindow.isVisible()) {
        panelWindow.hide();
    } else {
        // Calculate fresh position relative to the mascot's current coordinates
        const primaryDisplay = screen.getPrimaryDisplay();
        const workArea = primaryDisplay.workArea;
        const scaleFactor = primaryDisplay.scaleFactor || 1.0;
        
        const bounds = getPanelPosition(scaleFactor, workArea);

        panelWindow.setBounds({
            x: bounds.x,
            y: bounds.y,
            width: bounds.width,
            height: bounds.height
        });

        panelWindow.show();
        panelWindow.focus();
    }
}

// --- Mascot Window Instantiation ---
function createMascotWindow() {
    // Spawn nearest to where the mouse cursor is located
    const cursorPoint = screen.getCursorScreenPoint();
    const nearestDisplay = screen.getDisplayNearestPoint(cursorPoint);
    const scaleFactor = nearestDisplay.scaleFactor || 1.0;

    const mascotWidth = Math.round(120 * scaleFactor);
    const mascotHeight = Math.round(144 * scaleFactor);

    mascotWindow = new BrowserWindow({
        width: mascotWidth,
        height: mascotHeight,
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        resizable: false,
        skipTaskbar: true,
        hasShadow: false,
        type: 'toolbar',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    // Initial default positioning
    positionMascotDefault(nearestDisplay);

    mascotWindow.loadFile(path.join(__dirname, 'mascot.html'));

    // Monitor display settings (resolution / DPI changes)
    const metricsListener = () => {
        if (mascotWindow) {
            const bounds = mascotWindow.getBounds();
            const centerPoint = {
                x: bounds.x + bounds.width / 2,
                y: bounds.y + bounds.height / 2
            };
            const activeDisplay = screen.getDisplayNearestPoint(centerPoint);
            currentDisplayId = null; // Force recalculation
            handleMonitorChange(activeDisplay);
        }
    };
    screen.on('display-metrics-changed', metricsListener);

    // Cleanup
    mascotWindow.on('closed', () => {
        screen.off('display-metrics-changed', metricsListener);
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

    // Register global hotkey shortcut to toggle control panel
    globalShortcut.register('CommandOrControl+Shift+P', () => {
        togglePanel();
    });

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createMascotWindow();
        }
    });
});

app.on('will-quit', () => {
    // Unregister all global shortcut hooks
    globalShortcut.unregisterAll();
});

app.on('window-all-closed', () => {
    if (activeWindowInterval) {
        clearInterval(activeWindowInterval);
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
