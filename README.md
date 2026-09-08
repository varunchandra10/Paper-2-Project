# 🌌 RUEXIS AI Platform — Autonomous Paper-to-Code Desktop Mascot

> **RUEXIS** — **R**esearch, **U**nderstand, **E**xtract, e**X**amine, **I**mplement, **S**ynthesize

<p align="center">
  <strong>Local-First Agentic Desktop Companion that Converts Scientific Research Papers into Staged PyTorch Implementations.</strong>
</p>

<p align="center">
  <!-- Core Runtimes & Frameworks -->
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/TypeScript-5.0%2B-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/Electron-30%2B-47848F?style=for-the-badge&logo=electron&logoColor=white" alt="Electron" />
  <img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
</p>

<p align="center">
  <!-- AI, Agents & Storage -->
  <img src="https://img.shields.io/badge/LangGraph-Agentic_Pipeline-FF6B6B?style=for-the-badge&logo=langchain&logoColor=white" alt="LangGraph" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-Modern_UI-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Ollama-100%25_Offline-000000?style=for-the-badge&logo=ollama&logoColor=white" alt="Local Ollama" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
</p>


---

## 🌟 What is RUEXIS AI?

**RUEXIS AI** is a **local-first, fully agentic desktop platform** that converts academic scientific literature into verified, runnable code across 6 structured stages:

| Stage | Operation | Engine / Component |
| :---: | :--- | :--- |
| **R** | **Read / Research** | Multi-engine PDF Ingestion (`Docling` + `PyMuPDF` + `Gemini OCR`) |
| **U** | **Understand** | ReACT conversational agent with 7 academic search & FAISS knowledge tools |
| **E** | **Extract** | Structured extraction of hyperparameters, datasets, loss functions & equations |
| **X** | **eXamine** | Autonomous hardware profiling & VRAM compute feasibility scoring |
| **I** | **Implement** | Parallel PyTorch synthesis via Dual Code Engine (`Qwen 2.5 Coder` + `Gemini`) |
| **S** | **Synthesize** | AST validation, milestone sequencing & animated desktop mascot status sync |

---

## 🎭 Interactive Mascot System

RUEXIS AI features a **transparent desktop mascot overlay** that sits above your taskbar, anchored to the bottom-right corner of your screen. It visually mirrors every backend agent state in real time.

### Four Characters

| ID | Character | Style |
|----|-----------|-------|
| `mr_nerdy` | Mr. Nerdy | Classic academic nerd |
| `ms_nerdy` | Ms. Nerdy | Female academic variant |
| `mr_nerd` | Mr. Nerd | Compact nerd |
| `ms_nerd` | Ms. Nerd | Compact female variant |

### 13 Animation States

| State | Trigger |
|-------|---------|
| `standing` | Default idle |
| `blink` | Random idle micro-animation |
| `wave` | App startup greeting |
| `thinking` | ReACT thought / tool execution |
| `hunch` | Chat response generating |
| `catching` | PDF file staged for upload |
| `excite` | Pipeline completed successfully |
| `tired` | Extended work session |
| `having_sipping` | Long operation in progress |
| `sleep` | Long inactivity (idle timeout) |
| `angry` | Pipeline / upload error |
| `confused` | Unexpected response |
| `peeking` | Transition from edge back to idle |

> Click the mascot to toggle the main app panel. Drag it to reposition anywhere on screen.

---

## 🏗️ Architecture Overview

RUEXIS AI connects a native desktop overlay with a local FastAPI agentic backend and cloud/local LLM providers:

```mermaid
flowchart TD
    subgraph Desktop["Desktop Shell Layer (Electron & Win32)"]
        Win32["Win32 Taskbar FFI (Koffi)"] <--> ElectronMain["Electron Main Process"]
        ElectronMain --> MascotWin["Mascot Transparent Overlay (13-State FSM)"]
        ElectronMain --> PanelWin["Panel React 19 UI (Zustand + Tailwind)"]
    end

    subgraph Backend["FastAPI Orchestration Backend (Port 8000)"]
        APIRouter["API Router & SSE Stream Manager"]
        ChatAgent["ReACT Chat Agent (7 Tools)"]
        LangGraphPipe["LangGraph 5-Node Pipeline"]
        DualCode["Dual Code Engine (Gemini + HF Qwen)"]
        PDFExtract["Multi-Engine PDF Extractor (Docling / PyMuPDF)"]
        
        APIRouter --> ChatAgent
        APIRouter --> LangGraphPipe
        LangGraphPipe --> DualCode
        APIRouter --> PDFExtract
    end

    subgraph AIProviders["Multi-Provider Model Pool"]
        Cerebras["Cerebras (Llama 3.3 70B)"]
        Groq["Groq (Llama 3.3 / DeepSeek R1)"]
        Gemini["Google Gemini (2.5 Flash / Pro)"]
        HF["HuggingFace (Qwen 2.5 Coder 32B)"]
        OpenRouter["OpenRouter (Fallback)"]
    end

    subgraph Storage["Local Storage Layer"]
        StorageData["papers/ • conversations/ • rag_embeddings/ • codes/"]
    end

    PanelWin <-->|HTTP REST & SSE Stream| APIRouter
    PanelWin <-->|IPC Channels| MascotWin
    Backend <--> AIProviders
    Backend <--> Storage
```

---

## 🤖 Inference Providers

### Chat Interface (User-Selectable)

| Provider | Models | Type |
|----------|--------|------|
| **Groq** | Qwen 3.8 27B, GPT-OSS 120B | Free cloud LPU |
| **OpenRouter** | Gemini 2.5 Flash, DeepSeek R1 | Free community tier |
| **Local Ollama** | Any installed model | 100% offline |

### Backend-Exclusive (Not in Chat UI)

| Provider | Model | Reserved For |
|----------|-------|-------------|
| **Google Gemini** | `gemini-2.5-flash` | PDF extraction + Dual Code Engine B |
| **Hugging Face** | `Qwen/Qwen2.5-Coder-32B-Instruct` | Dual Code Engine A |

### Auto-Failover

If a provider hits a rate limit (HTTP 429), the `ModelRouter` automatically retries the next configured provider. The frontend `ModelSelector` updates to tick the correct model immediately — no manual intervention needed.

---

## ⚡ Core Pipeline Architectures

### 1. ReACT Conversational Pipeline
Context-aware reasoning loop equipped with academic retrieval and knowledge graph tools:

```mermaid
flowchart LR
    UQ["User Query"] --> CR["Context Retrieval<br/>(FAISS & Graph)"]
    CR --> TH["ReACT Thought"]
    TH --> TE["Tool Execution<br/>(arXiv / Scholar)"]
    TE --> OB["Observation"]
    OB --> TS["Token Stream (SSE)"]
```

### 2. Autonomous Paper Analysis Pipeline (LangGraph)
5-stage autonomous workflow transforming raw research papers into verified code:

```mermaid
flowchart LR
    Ingest["PDF Ingestion"] --> Param["Parameter Extraction"]
    Param --> Feas["Feasibility Scoring"]
    Feas --> Seq["Milestone Sequencing"]
    Seq --> Verify["PyTorch Verification"]
```

### 3. Dual Code Synthesis Engine
Parallel code generation leveraging dual specialized models with automated AST validation:

```mermaid
flowchart LR
    Specs["Paper Specifications"] --> EngineA["Engine A: Qwen 2.5 Coder 32B<br/>(Idiomatic PyTorch)"]
    Specs --> EngineB["Engine B: Gemini 2.5 Flash<br/>(Context & Math)"]
    EngineA --> AST["AST Validation & Check"]
    EngineB --> AST
    AST --> OutCode["Verified PyTorch Code"]
```

### 4. Multi-Engine PDF Extraction
Resilient document ingestion with hierarchical parser fallback:

```mermaid
flowchart LR
    RawPDF["Raw PDF File"] --> Docling["Docling (Primary)"]
    Docling -->|Fallback| PyMuPDF["PyMuPDF Parser"]
    PyMuPDF -->|Fallback| Gemini["Gemini (Complex/Scanned)"]
    Docling --> Canonical["Canonical JSON & FAISS Index"]
    PyMuPDF --> Canonical
    Gemini --> Canonical
```

---

## 📁 Project Structure

```
Paper-2-Project/
├── backend/          # FastAPI server, LangGraph pipelines, agents & model router
├── frontend/         # Desktop application layer
│   ├── electron_app/ # Electron main process, Win32 FFI & mascot sprite engine
│   └── renderer/     # React 19 glassmorphic UI, Zustand state & SSE listener
├── docs/             # System architectures, master project plan & subsystem guides
├── website/          # Product landing page & showcase
└── README.md         # Master overview & quickstart guide
```

---

## 📖 System Documentation & Architecture Guides

| Document | Path | Description |
|---|---|---|
| **System Architecture** | [`docs/detailed_architectures.md`](./docs/detailed_architectures.md) | **7-Division modular system flow**, Mermaid sequence diagrams, FSM, and master integrated synthesis |
| **Project Master Plan** | [`docs/Paper-2-Project_plan.md`](./docs/Paper-2-Project_plan.md) | High-level roadmap, core architecture decisions, and milestone execution checklist |
| **Complete Backend Guide** | [`docs/backend_docs/complete_backend_guide.md`](./docs/backend_docs/complete_backend_guide.md) | Exhaustive backend manual (FastAPI routes, LangGraph pipeline, retrieval DB, agents) |
| **Backend Day-Wise Guide** | [`docs/backend_docs/backend_day_wise_explanation.md`](./docs/backend_docs/backend_day_wise_explanation.md) | Chronological backend development log and phase-by-phase implementation breakdown |
| **Backend Commands** | [`docs/backend_docs/backend_commands.md`](./docs/backend_docs/backend_commands.md) | Server startup, test suites, virtual environment, and verification commands |
| **Backend Test Report** | [`docs/backend_docs/master_e2e_backend_test_report.md`](./docs/backend_docs/master_e2e_backend_test_report.md) | Full end-to-end backend test verification results and route status |
| **Complete Frontend Guide** | [`docs/frontend_docs/complete_frontend_guide.md`](./docs/frontend_docs/complete_frontend_guide.md) | Exhaustive frontend manual (React 19, Zustand state stores, glassmorphic UI, Electron IPC) |
| **Frontend Day-Wise Guide** | [`docs/frontend_docs/day_wise_explanation.md`](./docs/frontend_docs/day_wise_explanation.md) | Chronological frontend development log, 13-state sprite engine, and Win32 docking |
| **Frontend Commands** | [`docs/frontend_docs/frontend_commands.md`](./docs/frontend_docs/frontend_commands.md) | Vite renderer, Electron launch, multi-terminal startup, and build commands |

---

## 📚 Component READMEs

| Component | README | Description |
|-----------|--------|-------------|
| **Backend** | [`backend/README.md`](./backend/README.md) | Full API reference, agent flows, model routing, dual code engine |
| **Renderer** | [`frontend/renderer/README.md`](./frontend/renderer/README.md) | React state slices, SSE parsing, model selector, quota dashboard |
| **Electron App** | [`frontend/electron_app/README.md`](./frontend/electron_app/README.md) | Window management, IPC channels, mascot state machine, sprite engine |

---

## 🔑 Required Environment Variables

| Variable | For |
|----------|-----|
| `SECRET_KEY` | JWT auth signing |
| `GROQ_API_KEY` | Chat (Qwen 3.8 27B, GPT-OSS 120B) |
| `OPENROUTER_API_KEY` | Chat (Gemini 2.5 Flash, DeepSeek R1) |
| `GEMINI_API_KEY` | PDF extraction + Dual Code Engine B |
| `HUGGINGFACE_API_KEY` | Dual Code Engine A (Qwen 2.5 Coder 32B) |
| `TAVILY_API_KEY` | arXiv + Scholar search tools |

All configured in `backend/.env`. See [`backend/.env.example`](./backend/.env.example) for the full template.

---

## 📜 License

This project is released under the **MIT License**.

---

## 👤 Author

**Kola Varun Chandra**

[![GitHub](https://img.shields.io/badge/GitHub-varunchandra10-181717?style=for-the-badge&logo=github)](https://github.com/varunchandra10)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Kola%20Varun%20Chandra-0A66C2?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/kola-varun-chandra-702137391)

---

## 🙏 Acknowledgements

A few UI components in this project were inspired by **[Antigravity](https://antigravity.google/)**.
