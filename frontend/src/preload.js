const { contextBridge, ipcRenderer, webUtils } = require('electron');

// Expose secure API channels to the mascot renderer
contextBridge.exposeInMainWorld('mascotAPI', {
    getPathForFile: (file) => {
        return webUtils ? webUtils.getPathForFile(file) : file.path;
    },
    setIgnoreMouseEvents: (ignore, options) => {
        ipcRenderer.send('set-ignore-mouse-events', ignore, options);
    },
    dragWindow: (delta) => {
        ipcRenderer.send('drag-window', delta);
    },
    dragEnd: () => {
        ipcRenderer.send('drag-end');
    },
    togglePanel: () => {
        ipcRenderer.send('toggle-panel');
    },
    uploadPDF: (filePath, type) => {
        ipcRenderer.send('upload-pdf', { filePath, type });
    },
    openFileSelector: (type) => {
        ipcRenderer.send('open-file-selector', type);
    },
    onUploadStatus: (callback) => {
        ipcRenderer.on('upload-status', (event, status) => callback(status));
    },
    onFileSelected: (callback) => {
        ipcRenderer.on('selected-file', (event, data) => callback(data));
    },
    onStateChange: (callback) => {
        ipcRenderer.on('state-change', (event, state) => callback(state));
    }
});
