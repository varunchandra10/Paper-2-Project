const { app, BrowserWindow, screen, ipcMain, globalShortcut, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');

let backendProcess = null;

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
let isPanelMaximized = false;

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
        SHAppBarMessage = shell32.func("__stdcall", 'SHAppBarMessage', 'uintptr_t', ['uint32', koffi.pointer(APPBARDATA)]);
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
const MASCOT_BASE_WIDTH = 125;
const MASCOT_BASE_HEIGHT = 150;
let currentDisplayId = null;
let currentScaleFactor = 1.0;

function positionMascotDefault(nearestDisplay) {
    if (!mascotWindow || mascotWindow.isDestroyed()) return;

    const scaleFactor = nearestDisplay.scaleFactor || 1.0;
    currentDisplayId = nearestDisplay.id;
    currentScaleFactor = scaleFactor;

    const mascotWidth = Math.round(MASCOT_BASE_WIDTH * scaleFactor);
    const mascotHeight = Math.round(MASCOT_BASE_HEIGHT * scaleFactor);

    // Electron's workArea natively and accurately excludes the Windows taskbar (bottom, top, left, right)
    const workArea = nearestDisplay.workArea;
    const posX = workArea.x + workArea.width - mascotWidth - Math.round(24 * scaleFactor);
    const posY = workArea.y + workArea.height - mascotHeight;

    console.log(`[Main Process] Mascot placed at (${posX}, ${posY}) [${mascotWidth}x${mascotHeight}] on display ${nearestDisplay.id}`);

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

    const mascotWidth = Math.round(MASCOT_BASE_WIDTH * scaleFactor);
    const mascotHeight = Math.round(MASCOT_BASE_HEIGHT * scaleFactor);
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
        const targetWidth = Math.round(MASCOT_BASE_WIDTH * currentScaleFactor);
        const targetHeight = Math.round(MASCOT_BASE_HEIGHT * currentScaleFactor);
        
        // Move mascot window
        win.setBounds({
            x: bounds.x + delta.deltaX,
            y: bounds.y + delta.deltaY,
            width: targetWidth,
            height: targetHeight
        });

        // Synchronously move panel window in lockstep with fixed scaled dimensions
        if (panelWindow && !panelWindow.isDestroyed() && panelWindow.isVisible() && !isPanelMaximized) {
            const panelBounds = panelWindow.getBounds();
            const panelW = Math.round(340 * currentScaleFactor);
            const panelH = Math.round(480 * currentScaleFactor);
            panelWindow.setBounds({
                x: panelBounds.x + delta.deltaX,
                y: panelBounds.y + delta.deltaY,
                width: panelW,
                height: panelH
            });
        }
    }
});

ipcMain.on('drag-end', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
        const bounds = win.getBounds();
        const centerPoint = {
            x: bounds.x + bounds.width / 2,
            y: bounds.y + bounds.height / 2
        };
        const activeDisplay = screen.getDisplayNearestPoint(centerPoint);
        handleMonitorChange(activeDisplay);

        // Recalculate precise alignment snap above mascot head on drag end
        if (panelWindow && !panelWindow.isDestroyed() && panelWindow.isVisible()) {
            const scaleFactor = activeDisplay.scaleFactor || 1.0;
            const workArea = activeDisplay.workArea;
            const freshPanelBounds = getPanelPosition(scaleFactor, workArea);
            panelWindow.setBounds(freshPanelBounds);
        }
    }
});

ipcMain.on('toggle-panel', () => {
    togglePanel();
});

ipcMain.on('toggle-maximize', () => {
    toggleMaximize();
});

ipcMain.on('set-mascot-state', (event, state) => {
    sendMascotState(state);
});

let currentMascotSkin = 'mr_nerdy';

ipcMain.on('set-mascot-skin', (event, skinId) => {
    const normalized = (skinId || 'mr_nerdy').replace('-', '_');
    currentMascotSkin = normalized;
    if (mascotWindow && !mascotWindow.isDestroyed()) {
        mascotWindow.webContents.send('mascot-skin-change', normalized);
    }
});

ipcMain.handle('get-mascot-skin', () => {
    return currentMascotSkin;
});

ipcMain.on('user-activity', () => {
    if (mascotWindow && !mascotWindow.isDestroyed()) {
        mascotWindow.webContents.send('user-activity');
    }
});


let hasWavedAtStartup = false;

function sendMascotState(state) {
    const isPanelOpen = panelWindow && !panelWindow.isDestroyed() && panelWindow.isVisible();
    // When the sidebar panel is closed, keep mascot in sleeping pose unless active research or work is occurring
    let effectiveState = state;
    if (!isPanelOpen && state === 'idle') {
        effectiveState = 'sleeping';
    }
    if (mascotWindow && !mascotWindow.isDestroyed()) {
        mascotWindow.webContents.send('state-change', effectiveState);
    }
}

function startBackendServer() {
    const projectRoot = path.join(__dirname, '../../../');
    let appPath = path.join(projectRoot, 'backend/main.py');
    let cwdPath = path.join(projectRoot, 'backend');
    if (!fs.existsSync(appPath)) {
        appPath = path.join(projectRoot, 'backend/app.py');
    }

    let pythonExecutable = 'python';
    const venvPythonPath = path.join(projectRoot, '.venv/Scripts/python.exe');
    if (fs.existsSync(venvPythonPath)) {
        pythonExecutable = venvPythonPath;
    }

    console.log(`[Main Process] Spawning backend server using: ${pythonExecutable} at: ${appPath}`);

    backendProcess = spawn(pythonExecutable, [appPath], {
        cwd: cwdPath,
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    backendProcess.stdout.on('data', (data) => {
        console.log(`[Backend Server Stdout] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
        console.error(`[Backend Server Stderr] ${data.toString().trim()}`);
    });

    backendProcess.on('close', (code) => {
        console.log(`[Backend Server] Subprocess exited with code ${code}`);
    });
}

function postAnalyze(filePath, modelName, callback) {
    const postData = JSON.stringify({
        filePath: filePath,
        modelName: modelName
    });

    const options = {
        hostname: '127.0.0.1',
        port: 8000,
        path: '/analyze',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData)
        }
    };

    const req = http.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => body += chunk);
        res.on('end', () => {
            try {
                const parsed = JSON.parse(body);
                if (res.statusCode >= 400) {
                    callback(new Error(parsed.detail || `Server returned error status ${res.statusCode}`));
                } else {
                    callback(null, parsed.run_id);
                }
            } catch (e) {
                callback(new Error(`Failed to parse response: ${body}`));
            }
        });
    });

    req.on('error', (e) => {
        callback(e);
    });

    req.write(postData);
    req.end();
}

function postAnalyzeWithRetry(filePath, modelName, callback, retries = 5) {
    postAnalyze(filePath, modelName, (err, runId) => {
        if (err) {
            if ((err.code === 'ECONNREFUSED' || err.code === 'ECONNRESET') && retries > 0) {
                console.log(`[Main Process] Connection to backend refused/reset. Retrying in 1.5s... (${retries} left)`);
                setTimeout(() => {
                    postAnalyzeWithRetry(filePath, modelName, callback, retries - 1);
                }, 1500);
            } else {
                callback(err);
            }
        } else {
            callback(null, runId);
        }
    });
}

function listenToStream(runId, onLog, onMascotState, onCompleted, onFailed) {
    const req = http.get(`http://127.0.0.1:8000/stream/${runId}`, (res) => {
        let currentEvent = '';
        let buffer = '';
        
        res.on('data', (chunk) => {
            buffer += chunk.toString();
            const lines = buffer.split('\n');
            // Keep the last partial line in the buffer
            buffer = lines.pop();

            for (let line of lines) {
                line = line.trim();
                if (!line) continue;
                
                if (line.startsWith('event:')) {
                    currentEvent = line.replace('event:', '').trim();
                } else if (line.startsWith('data:')) {
                    const dataStr = line.replace('data:', '').trim();
                    if (currentEvent === 'log') {
                        onLog(dataStr);
                    } else if (currentEvent === 'mascot-state') {
                        onMascotState(dataStr);
                    } else if (currentEvent === 'completed') {
                        try {
                            const parsed = JSON.parse(dataStr);
                            onCompleted(parsed.report);
                        } catch (e) {
                            onCompleted(dataStr);
                        }
                    } else if (currentEvent === 'failed') {
                        try {
                            const parsed = JSON.parse(dataStr);
                            onFailed(parsed.error);
                        } catch (e) {
                            onFailed(dataStr);
                        }
                    }
                }
            }
        });
        
        res.on('end', () => {
            console.log(`[Main Process] SSE Stream finished for run ${runId}`);
        });
    });

    req.on('error', (e) => {
        console.error(`[Main Process] SSE Stream HTTP error:`, e);
        onFailed(e.message);
    });
}

function runPipelineOrchestrator(filename, destPath, type, modelName) {
    if (!panelWindow) return;

    panelWindow.webContents.send('pipeline-log', { text: `[System] Dispatching analysis job to FastAPI server...` });
    sendMascotState('hunch');

    const targetModel = modelName || 'llama-3.3-70b-versatile';

    postAnalyzeWithRetry(destPath, targetModel, (err, runId) => {
        if (err) {
            console.error(`[Main Process] Failed to trigger pipeline analysis:`, err);
            sendMascotState('sleeping');
            panelWindow.webContents.send('pipeline-completed', { 
                success: false, 
                error: `Backend connection error: ${err.message}` 
            });
            return;
        }

        panelWindow.webContents.send('pipeline-log', { text: `[System] Job successfully scheduled (Run ID: ${runId}). Streaming logs...` });

        listenToStream(
            runId,
            (logText) => {
                panelWindow.webContents.send('pipeline-log', { text: logText });
            },
            (mascotState) => {
                sendMascotState(mascotState);
            },
            (reportContent) => {
                sendMascotState('excited');
                setTimeout(() => {
                    sendMascotState('idle');
                }, 3500);
                panelWindow.webContents.send('pipeline-completed', {
                    success: true,
                    filename,
                    type,
                    reportContent
                });
            },
            (errorMessage) => {
                sendMascotState('sleeping');
                panelWindow.webContents.send('pipeline-completed', {
                    success: false,
                    error: errorMessage
                });
            }
        );
    });
}

ipcMain.on('upload-pdf', (event, { filePath, type, modelName }) => {
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

        sendMascotState('reading');
        event.reply('upload-status', { success: true, filename, type, filePath: destPath });
        runPipelineOrchestrator(filename, destPath, type, modelName);
    } catch (err) {
        console.error("File upload/copy error:", err);
        event.reply('upload-status', { success: false, error: err.message, type });
    }
});

// Stage-only file selector: opens dialog, copies file, sends back staged info WITHOUT running the pipeline.
// Pipeline only fires when the user explicitly sends a message (via trigger-upload).
ipcMain.on('open-file-selector', (event, type, modelName) => {
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

                // Only stage — do NOT trigger pipeline yet
                sendMascotState('catching');
                event.reply('file-staged', { success: true, filename, type, filePath: destPath, modelName });
            } catch (err) {
                event.reply('file-staged', { success: false, error: err.message, type });
            }
        }
    }).catch(err => {
        console.error("File dialog error:", err);
        event.reply('file-staged', { success: false, error: err.message, type });
    });
});

// trigger-upload: called when the user actually sends (hits Send). Fires the pipeline.
ipcMain.on('trigger-upload', (event, { filename, filePath, type, modelName }) => {
    try {
        sendMascotState('hunch');
        event.reply('upload-status', { success: true, filename, type, filePath });
        runPipelineOrchestrator(filename, filePath, type, modelName);
    } catch (err) {
        console.error("Trigger upload error:", err);
        event.reply('upload-status', { success: false, error: err.message, type });
    }
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

            // Position panel bottom directly above the mascot's head with a snug ~8px gap (offsetting transparent canvas padding)
            let posY = mascotBounds.y - panelHeight + Math.round(18 * scaleFactor);
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

    let distHtmlPath = path.join(__dirname, '../../renderer/dist/index.html');
    if (!fs.existsSync(distHtmlPath)) {
        distHtmlPath = path.join(__dirname, '../../new_renderer/dist/index.html');
    }
    if (app.isPackaged) {
        panelWindow.loadFile(distHtmlPath);
    } else {
        // In development, prefer Vite dev server for hot reloading, falling back to dist bundle if dev server is down
        panelWindow.loadURL('http://localhost:5173').catch(() => {
            if (fs.existsSync(distHtmlPath)) {
                panelWindow.loadFile(distHtmlPath);
            }
        });
    }

    panelWindow.on('hide', () => {
        sendMascotState('sleeping');
    });

    panelWindow.on('closed', () => {
        panelWindow = null;
        sendMascotState('sleeping');
    });
}

function togglePanel() {
    if (!panelWindow) {
        createPanelWindow();
    }

    if (panelWindow.isVisible()) {
        if (isPanelMaximized) {
            isPanelMaximized = false;
            panelWindow.setResizable(false);
            panelWindow.setMinimumSize(100, 100);
            if (mascotWindow && !mascotWindow.isDestroyed()) {
                mascotWindow.show();
            }
            panelWindow.webContents.send('maximize-change', false);
        }
        panelWindow.hide();
        sendMascotState('sleeping');
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

        if (mascotWindow && !mascotWindow.isDestroyed()) {
            mascotWindow.show();
        }

        panelWindow.show();
        panelWindow.focus();
        // Whenever panel is opened, mascot stands and says "hii"
        sendMascotState('wave-intro');
    }
}

function toggleMaximize() {
    if (!panelWindow || panelWindow.isDestroyed()) return;

    if (isPanelMaximized) {
        // Restore to docked narrow view
        isPanelMaximized = false;
        panelWindow.unmaximize();
        panelWindow.setResizable(false);
        panelWindow.setMinimumSize(100, 100);

        const activeDisplay = screen.getDisplayNearestPoint(panelWindow.getBounds());
        const scaleFactor = activeDisplay.scaleFactor || 1.0;
        const workArea = activeDisplay.workArea;

        const dockedBounds = getPanelPosition(scaleFactor, workArea);
        panelWindow.setBounds(dockedBounds);

        if (mascotWindow && !mascotWindow.isDestroyed()) {
            mascotWindow.show();
        }
        sendMascotState('idle');
        panelWindow.webContents.send('maximize-change', false);
    } else {
        // Maximize to full screen
        isPanelMaximized = true;
        if (mascotWindow && !mascotWindow.isDestroyed()) {
            mascotWindow.hide();
        }

        panelWindow.setResizable(true);
        panelWindow.setMinimumSize(800, 600);
        panelWindow.maximize();

        panelWindow.webContents.send('maximize-change', true);
    }
}

// --- Mascot Window Instantiation ---
function createMascotWindow() {
    // Spawn nearest to where the mouse cursor is located
    const cursorPoint = screen.getCursorScreenPoint();
    const nearestDisplay = screen.getDisplayNearestPoint(cursorPoint);
    const scaleFactor = nearestDisplay.scaleFactor || 1.0;

    const mascotWidth = Math.round(MASCOT_BASE_WIDTH * scaleFactor);
    const mascotHeight = Math.round(MASCOT_BASE_HEIGHT * scaleFactor);

    mascotWindow = new BrowserWindow({
        width: mascotWidth,
        height: mascotHeight,
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

    mascotWindow.setAlwaysOnTop(true, 'screen-saver');
    mascotWindow.setVisibleOnAllWorkspaces(true);

    // Initial default positioning
    positionMascotDefault(nearestDisplay);

    mascotWindow.loadFile(path.join(__dirname, 'mascot.html'));

    mascotWindow.once('ready-to-show', () => {
        mascotWindow.show();
    });

    mascotWindow.webContents.on('did-finish-load', () => {
        mascotWindow.webContents.send('mascot-skin-change', currentMascotSkin);
    });

    mascotWindow.webContents.on('console-message', (event, level, message) => {
        console.log(`[Mascot Window Console] ${message}`);
    });

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
                    sendMascotState('reading');
                } else {
                    sendMascotState('idle');
                }
            }
        } catch (err) {
            // Ignore polling errors for OS protected windows
        }
    }, 2000);
}

// --- Lifecycle Event Listeners ---
app.whenReady().then(() => {
    startBackendServer();
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

    // Kill python backend server
    if (backendProcess) {
        console.log("[Main Process] Killing FastAPI backend server process...");
        backendProcess.kill();
    }
});

app.on('window-all-closed', () => {
    if (activeWindowInterval) {
        clearInterval(activeWindowInterval);
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
