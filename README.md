# 🖥️ Paper-to-Project Agent

An interactive, local-first agentic desktop application that converts research papers into feasibility-checked, staged implementation blueprints. The system is delivered through a transparent Windows desktop mascot with a docked sidebar control panel.

---

## 🔍 Overview

The **Paper-to-Project Agent** is designed to bridge the gap between academic research and practical engineering. Instead of manually translating formulas, architectures, and hyperparameters, this system automates the ingestion, method decomposition, gap-finding (hyperparameter verification), feasibility validation, and build sequencing.

### Key Features
* **Local-First AI:** Powered by `Qwen2.5-Coder-7B` via Ollama. No API keys, no cost, complete privacy.
* **Multi-Agent Orchestration:** A 6-stage LangGraph pipeline that sequentially extracts, validates, and sequences the implementation.
* **Interactive Desktop Mascot:** A transparent, DPI-aware Electron mascot that reacts to the agent's state (Sleeping, Reading, Investigating, Idle).
* **Docked Sidebar Panel:** A slide-out web interface to select research papers, view live progress streams, and browse the final implementation markdown report.

---

## 🏗️ Architecture

```
LangGraph 6-Agent Core (Local Ollama: Qwen2.5-Coder-7B)
   ├── Ingestion Agent (PyMuPDF & section parsing)
   ├── Method Decomposition Agent (Component graph)
   ├── Gap-Finding Agent (Tavily search & hyperparameter validation)
   ├── Feasibility Agent (Hardware, dataset, and timeline constraints)
   ├── Build Sequencing Agent (Dependency-ordered milestones)
   └── Adaptation Report Agent (Markdown report builder)
           │
           ▼ (FastAPI / SSE streaming bridge)
           │
Electron Desktop Application
   ├── Transparent, frameless window (Mascot rig)
   ├── Docked sidebar (Live SSE stream & markdown display)
   └── Win32 native API integration (Taskbar alignment & active-win polling)
```

---

## 🛠️ Tech Stack

* **Backend / Agents:** Python, LangGraph, FastAPI, PyMuPDF, Pydantic, Ollama (`qwen2.5-coder:7b`)
* **Frontend / Desktop App:** JavaScript, Electron, HTML, Vanilla CSS, TailwindCSS (optional, v4)
* **Native OS Integration:** `koffi` (Win32 API bindings), `active-win` (window tracking)
* **Packaging:** PyInstaller (Python backend executable), Electron Builder (NSIS Windows Installer)

---

## 📅 Project Timeline & Phases

The build plan spans 28 days across 4 clean, sequential phases:

* **Phase 1: Agentic Core (Days 1–14)** — PDF parsing, 6-stage LangGraph pipelines, local Ollama integration, and thesis-grounded validation.
* **Phase 2: Desktop UI (Days 15–21)** — Electron framework, transparent frame window setup, Win32 taskbar queries, SVG character rigging, animations, and active-window polling.
* **Phase 3: Integration & Streaming (Days 22–25)** — FastAPI bridge, Server-Sent Events (SSE) stream, and linking the mascot's animations to the agent's real-time activities.
* **Phase 4: Packaging (Days 26–28)** — Compiling Python binaries with PyInstaller, building the NSIS installer via Electron Builder, dependency health checks, and VM testing.

---

## 🚀 Getting Started (Development Setup)

*Instructions will be updated as implementation progresses.*

### Prerequisites
1. [Python 3.10+](https://www.python.org/downloads/)
2. [Node.js 18+](https://nodejs.org/)
3. [Ollama](https://ollama.com/) (installed locally)
4. [uv](https://github.com/astral-sh/uv) (fast Python package manager)

### Installation
1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/your-username/paper-to-project-agent.git
   cd paper-to-project-agent
   ```
2. Pull the local coding model:
   ```bash
   ollama pull qwen2.5-coder:7b
   ```
3. Set up the Python virtual environment and install backend dependencies:
   ```bash
   uv venv
   # On Windows:
   .venv\Scripts\activate
   # Install dependencies (to be listed in requirements.txt)
   ```
4. Set up the Electron frontend:
   ```bash
   npm install
   ```
