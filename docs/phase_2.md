# Phase 2 Documentation — Desktop UI & Landing Page (Days 15–17)

This document tracks the progress, architectural details, and validation logs for **Phase 2 (Desktop UI & Showcase Website)**.

---

## 🎯 Objectives
* Initialize a lightweight, frameless, transparent Electron desktop shell window.
* Implement Windows DPI-aware scaling and Win32 taskbar boundary checks.
* Setup mouse click pass-through mechanics so transparent pixels do not block desktop interactions.
* Support a custom vector mascot (`mascot.svg`) with dynamic CSS animation states.
* Build a responsive Next.js App Router landing page showcasing the product features and installer download CTA.

---

## 🏗️ Technical Stack & Dependencies

### Desktop Mascot Client (`frontend/`)
* **`electron` (^43.4.1):** Desktop container merging Chromium (renderer) and Node.js (filesystem/child process spawning).
* **`koffi` (^3.1.5):** Fast Foreign Function Interface (FFI) for calling Win32 DLLs (`shell32.dll` and `user32.dll`) without compiling native binary extensions.
* **`active-win` (^8.2.1):** Active foreground window process and title tracking.
* **`electron-store` (^11.0.2):** Local JSON storage for persistent mascot settings and color preferences.
* **`electron-builder` (^26.15.3):** Desktop packager to output standalone Windows NSIS installers.

### Landing Page Website (`website/`)
* **Next.js 16 (Turbopack):** Core web application router.
* **TypeScript & ESLint:** Code typing and structural enforcement.
* **Vanilla CSS Modules:** Modular CSS files for layout grids and animation styles.

---

## 📝 Completed Milestone Logs

### 📅 Days 15 & 16 — Electron Client Shell & Win32 Integration

We initialized the Node environment inside the [frontend/](../frontend/) folder and built the transparent desktop window shell:

* **Transparent Frame Rig:** Set up transparent window attributes, disabled frames/shadows, and disabled application control menu indicators inside [`frontend/src/main.js`](../frontend/src/main.js).
* **Win32 Taskbar Querying:** Configured `koffi` to load Windows shell APIs:
  ```javascript
  const shell32 = koffi.load('shell32.dll');
  // Struct mapping for RECT and APPBARDATA structures
  const result = SHAppBarMessage(ABM_GETTASKBARPOS, abd);
  ```
  This returns the exact boundary of the user's taskbar (Left, Top, Right, or Bottom edges).
* **Guaranteed Right-Alignment:** Programmed positioning algorithms to ensure the mascot is positioned on the **right side** of the screen, even if the taskbar sits on the left of the monitor.
* **Mouse Event Pass-Through:** Configured context-isolated preloads inside [`frontend/src/preload.js`](../frontend/src/preload.js) and triggers inside [`frontend/src/mascot.js`](../frontend/src/mascot.js) calling `win.setIgnoreMouseEvents`. Mouse movements are ignored on transparent empty spaces (pass-through to desktop) and captured on the character's hitbox.
* **Custom SVG Integration:** Added your custom vector character [`frontend/src/assets/mascot.svg`](../frontend/src/assets/mascot.svg) to the assets directory, replacing the default JPG sprite sheet.
* **Proportional Tuning:** Adjusted mascot window dimensions to `150px` width by `180px` height (DPI-scaled) to match the SVG aspect ratio perfectly, preventing shoe clipping.
* **Mascot CSS Animations:** Styled keyframe bobs and pulses inside [`frontend/src/mascot.css`](../frontend/src/mascot.css):
  * **Idle:** Gentle vertical translation bobbing.
  * **Sleeping:** Subtle scale breathing cycles and opacity pulses.
  * **Reading:** Focused tilt rotations.
  * **Working:** Rapid linear micro-vibrations representing typing activities.

### 📅 Day 17 — Next.js Landing Webpage

We initialized the Next.js showcase web application in [website/](../website/):

* **Landing Interface:** Created the home layout inside [`website/src/app/page.tsx`](../website/src/app/page.tsx) and custom styles inside [`website/src/app/page.module.css`](../website/src/app/page.module.css). It features a dark-slate theme, modern card grids, download buttons, and an interactive mascot carousel.
* **SEO Metadata:** Configured semantic title and meta descriptions inside [`website/src/app/layout.tsx`](../website/src/app/layout.tsx).
* **Compilation Verification:** Ran the production build system. All components compiled successfully with **zero errors** under Turbopack in **25.8 seconds**.
### 📅 Day 18 — Control Panel Ingestion & Shortcut Triggers

We implemented the core interaction and document ingestion flow inside the desktop application:

* **Global Hotkey Trigger:** Configured `globalShortcut` in the main process to register `Ctrl + Shift + P` globally. Pressing this shortcut opens/closes the sidebar panel instantly from any foreground application.
* **Mascot Overlay Layout:** Reconfigured window proportions to a compact `120x144` scale. Programmed the sidebar control panel to dynamically center itself and float exactly `8px` above the mascot's head, keeping the mascot visible at the bottom of the dashboard.
* **Drag-and-Drop Ingestion:** Created a custom `.drop-zone` handler in [`frontend/src/panel.html`](../frontend/src/panel.html) to intercept drag events. Dropping a valid PDF document registers the file's absolute path and kicks off the ingestion milestones.
* **File Dialog Selector:** Bound a click event on the drop zone to open Electron's native `dialog.showOpenDialog` file picker, filtering specifically for `.pdf` files.
* **Local Sandbox Copies:** Programmed a secure backend copy mechanism in the main process. Dropped or selected PDF files are duplicated asynchronously to the local frontend storage directory: [`frontend/src/uploads/`](../frontend/src/uploads/).
* **Milestone Progress Visualizer:** Linked the upload copy success status to update the interactive Gantt chart inside the panel, advancing the active milestone badge from *1. Ingestion* to *2. Decomposition* automatically.

---

## 📈 Verification Checklist

| Check / Test Case | Method | Expected Result | Status |
| :--- | :--- | :--- | :---: |
| **Electron Shell Boot** | `npm start` | Window launches with no taskbar block or frame shadows. | **PASS** |
| **Taskbar Docking** | Win32 API query | Mascot automatically anchors above bottom/right taskbars. | **PASS** |
| **Right-Align Lock** | Position validation | Locks mascot on right side even if taskbar is on the left. | **PASS** |
| **Click Pass-Through** | Manual mouse clicking | Clicking adjacent pixels clicks the desktop; clicking the character drags/focuses the window. | **PASS** |
| **SVG Scaling** | Aspect ratio check | Character renders clearly at compact `120x144` with no clipping. | **PASS** |
| **Global Hotkey** | Press `Ctrl+Shift+P` | Panel window slides/opens above the mascot's head immediately. | **PASS** |
| **Mascot Panel Click** | Left-click mascot | Mascot click is detected and toggles the panel open/closed. | **PASS** |
| **Floating Layout** | Z-Order Validation | Mascot floats overlays directly *on top* of the control panel. | **PASS** |
| **Drag-and-Drop Ingestion** | Drop PDF onto panel | Log prints dropped file and copies it to `src/uploads/` folder. | **PASS** |
| **File Picker browse** | Click drop-zone | Opens OS file dialog, copies selected PDF to `src/uploads/` folder. | **PASS** |
| **Next.js Compilation** | `npm run build` | Turbopack compiles successfully with zero type or CSS module errors. | **PASS** |

---

## 🏁 Current Status
* **Mascot Client:** Operational transparent floating window with compact size, loading custom SVG, and running CSS animations.
* **Sidebar Panel:** Fully functional popover panel floating above the mascot, supporting global shortcuts, click toggles, drag-and-drop PDF uploads, and local file storage.
* **Next Steps:** Proceed to **Day 20 (IPC Communication & Python Child Process Spawner)** to spin up the LangGraph pipeline when a PDF is uploaded.
