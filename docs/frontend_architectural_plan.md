
## 🏛️ Architectural Decision Record (ADR): Desktop Framework

### Decision: Electron for v1.0, Migrate to Tauri for v2.0

We evaluated both frameworks for our desktop client shell and aligned on using **Electron** for the initial MVP, with a scheduled migration path to **Tauri** in a future release.

#### 📊 Framework Comparison Matrix

| Metric / Feature | ⚛️ Electron (v1.0 - Chosen) | 🦀 Tauri (v2.0 - Future Upgrade) |
| :--- | :--- | :--- |
| **Developer Dependencies** | Node.js (Already installed and verified). | Rust Toolchain (Cargo) + MSVC C++ Build Tools (~5GB). |
| **Setup Time** | Near-instant (<1 minute). | ~30 minutes (requires compiler downloads & PATH setup). |
| **App Installer Size** | ~120 MB (Chromium engine bundled). | **~10 MB** (uses system's native Windows WebView2). |
| **Idle Memory Footprint** | ~50–80 MB RAM. | **~15–25 MB RAM**. |
| **Native DLL Interface** | Node.js FFI (`koffi` wrapper). | Native Rust Win32 bindings (e.g. `windows` crate). |
| **Python Child Spawning** | Node.js `child_process.spawn`. | Rust `std::process::Command` wrapper. |

#### 🔍 Rationale for Initial Selection (Electron v1.0)
1. **Zero Setup Friction:** We avoid having to download and configure heavy C++ compilers or the Rust toolchain on the host machine, ensuring we stay focused on product features.
2. **Rapid Prototyping:** Spawning Python child processes, streaming progress logs via stdout/stderr, and setting up preload IPC bridges is highly standard and rapidly editable in Javascript.
3. **Timeline Risk Mitigation:** Fits perfectly into the 28-day roadmap, ensuring native compilation issues do not block core delivery.

#### 🚀 Rationale for Migration Roadmap (Tauri v2.0)
1. **Resource Efficiency:** Floating desktop widgets should be invisible to system resources. Swapping Electron for Tauri will reduce RAM usage by ~70%, keeping the idle mascot under 20MB of RAM.
2. **Distribution Size:** Shrinking the installer from 120MB to 10MB makes download/distribution via the landing webpage significantly faster for end-users.