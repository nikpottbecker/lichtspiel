const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('cinema', {
  getEnvironment: () => ipcRenderer.invoke('cinema:environment'),
  chooseMpv: () => ipcRenderer.invoke('cinema:choose-mpv'),
  importMedia: () => ipcRenderer.invoke('cinema:import'),
  checkShow: (show) => ipcRenderer.invoke('cinema:preflight', show),
  getAudioDevices: () => ipcRenderer.invoke('cinema:audio-devices'),
  startShow: (show) => ipcRenderer.invoke('cinema:start', show),
  pauseShow: () => ipcRenderer.invoke('cinema:pause'),
  resumeShow: () => ipcRenderer.invoke('cinema:resume'),
  stopShow: () => ipcRenderer.invoke('cinema:stop'),
  nextCue: () => ipcRenderer.invoke('cinema:next'),
  blackout: () => ipcRenderer.invoke('cinema:blackout'),
  saveProject: (project) => ipcRenderer.invoke('cinema:save', project),
  loadProject: () => ipcRenderer.invoke('cinema:load'),
  scheduleShow: (show) => ipcRenderer.invoke('cinema:schedule', show),
  getLighting: () => ipcRenderer.invoke('cinema:lighting-get'),
  saveLighting: (input) => ipcRenderer.invoke('cinema:lighting-save', input),
  testLightingConnection: () => ipcRenderer.invoke('cinema:lighting-test'),
  previewLighting: (event) => ipcRenderer.invoke('cinema:lighting-preview', event),
  applyLighting: (event) => ipcRenderer.invoke('cinema:lighting-apply', event),
  onLighting: (callback) => {
    const listener = (_event, notice) => callback(notice);
    ipcRenderer.on('cinema:lighting', listener);
    return () => ipcRenderer.removeListener('cinema:lighting', listener);
  },
  onPlayback: (callback) => {
    const listener = (_event, state) => callback(state);
    ipcRenderer.on('cinema:playback', listener);
    return () => ipcRenderer.removeListener('cinema:playback', listener);
  },
});
