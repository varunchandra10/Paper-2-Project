const { contextBridge, ipcRenderer } = require('electron');

// Expose secure API channels to the mascot renderer
contextBridge.exposeInMainWorld('mascotAPI', {
    setIgnoreMouseEvents: (ignore, options) => {
        ipcRenderer.send('set-ignore-mouse-events', ignore, options);
    },
    onStateChange: (callback) => {
        ipcRenderer.on('state-change', (event, state) => callback(state));
    }
});
