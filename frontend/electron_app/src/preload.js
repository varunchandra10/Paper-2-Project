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
    uploadPDF: (filePath, type, modelName) => {
        ipcRenderer.send('upload-pdf', { filePath, type, modelName });
    },
    openFileSelector: (type, modelName) => {
        ipcRenderer.send('open-file-selector', type, modelName);
    },
    triggerUpload: (filename, filePath, type, modelName) => {
        ipcRenderer.send('trigger-upload', { filename, filePath, type, modelName });
    },
    onUploadStatus: (callback) => {
        ipcRenderer.on('upload-status', (event, status) => callback(status));
    },
    onFileStaged: (callback) => {
        ipcRenderer.on('file-staged', (event, data) => callback(data));
    },
    onFileSelected: (callback) => {
        ipcRenderer.on('selected-file', (event, data) => callback(data));
    },
    onStateChange: (callback) => {
        ipcRenderer.on('state-change', (event, state) => callback(state));
    },
    onPipelineLog: (callback) => {
        ipcRenderer.on('pipeline-log', (event, log) => callback(log));
    },
    onPipelineCompleted: (callback) => {
        ipcRenderer.on('pipeline-completed', (event, status) => callback(status));
    },
    toggleMaximize: () => {
        ipcRenderer.send('toggle-maximize');
    },
    onMaximizeChange: (callback) => {
        ipcRenderer.on('maximize-change', (event, isMaximized) => callback(isMaximized));
    }
});
