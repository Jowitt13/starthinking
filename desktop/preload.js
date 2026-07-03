const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("StartThinkingDesktop", {
  chooseFiles: () => ipcRenderer.invoke("materials:choose-files"),
  extractFiles: (payload) => ipcRenderer.invoke("materials:extract-files", payload),
  generateStudySet: (payload) => ipcRenderer.invoke("ai:generate-study-set", payload),
  checkServices: (payload) => ipcRenderer.invoke("services:check", payload),
  openExternal: (url) => ipcRenderer.invoke("shell:open-external", url),
});
