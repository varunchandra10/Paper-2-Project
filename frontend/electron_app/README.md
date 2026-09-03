# 🖥️ Synthexis — Electron Desktop Shell & Mascot Container

The desktop application layer for **Synthexis AI Platform**, powering frameless window overlays, Win32 taskbar docking, active PDF title detection, and native IPC channels.

---

## 🏗️ Technical Features
- **Frameless Overlay Window**: Transparent, always-on-top Electron window with click-through `setIgnoreMouseEvents` pass-through.
- **Win32 Taskbar FFI Query**: Native Win32 `SHAppBarMessage` query (`ABM_GETTASKBARPOS` via `koffi`) calculating mascot anchor coordinates.
- **Active Window Polling**: Window title polling via `active-win` detecting focused PDF viewer windows (Acrobat, Edge, Sumatra) and paper sites (arXiv, IEEE, CVPR).
- **Global Hotkey Fallback**: Press `Ctrl+Shift+P` anywhere to toggle the docked sidebar UI panel.

---

## ⚡ Quick Start
```bash
cd frontend/electron_app
npm install
npm start
```
