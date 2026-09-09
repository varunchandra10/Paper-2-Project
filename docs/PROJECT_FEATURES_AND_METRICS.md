# 🚀 RUEXIS AI — Comprehensive Project Features & Benchmark Metrics

> **Project Classification:** Local-First Agentic Desktop Literature-to-PyTorch Platform  
> **Source Assessment:** Features extracted directly from codebase implementation files (`backend/app/`, `frontend/electron_app/`, `frontend/renderer/`).  
> **Key Metrics:** Empirically measured from PoC benchmark test suites (`docs/backend_docs/master_e2e_backend_test_report.md`, `master_scorecard.json`).

---

## 📊 1. Verified Empirical Metrics (From `docs/`)

These benchmark numbers represent verified test executions across peer-reviewed computer vision and deep learning scientific papers:

| Metric | Measured Value | Significance / Context |
|---|---|---|
| **Benchmarked Research Papers** | **48 Papers** (`[1].pdf` → `[48].pdf`) | Complete end-to-end ingestion and synthesis across 48 diverse scientific architectures. |
| **Synthesized PyTorch Code Files** | **332 Python Files** | Full multi-file packages (`config.py`, `dataset.py`, `models/`, `losses.py`, `train.py`, `evaluate.py`). |
| **AST Syntax Conformance Rate** | **100% PASS (332 / 332 Files)** | Verified via Python's `ast.parse` syntax engine with **0 syntax errors**. |
| **Architectural Test Phases** | **12 / 12 Phases PASS (100%)** | Verified from ingestion to RAG, multi-agent reasoning, code synthesis, chat, and telemetry. |
| **Continuous Agent Execution Time** | **21,254.36 s (~5.9 Hours)** | Uninterrupted autonomous agent reasoning across the 48-paper corpus. |
| **Cloud Independence / Local Mode** | **100% Offline Capable** | Tested with local Ollama (`qwen2.5-coder:1.5b`), completely eliminating cloud rate limits (`HTTP 429`). |
| **Hardware Telemetry Profiling** | **16 Cores, 23.6 GB RAM, RTX 5050** | Verified live telemetry and CUDA VRAM profiling on real host hardware. |

---

## 🛠️ 2. Core Features Extracted from Project Codebase

### A. Tri-Engine Multi-Modal Paper Ingestion (`backend/app/extraction/`)
- **PyMuPDF Coordinate Extraction (`pymupdf_parser.py`)**: High-speed coordinate-aware text and bounding box extraction preserving physical PDF geometry.
- **GROBID TEI XML Parsing (`grobid_parser.py`, `grobid_client.py`)**: Academic schema parsing resolving IEEE/ACM paper titles, author affiliations, abstracts, structured section trees, and bibliographies.
- **Docling Layout Analysis (`docling_parser.py`)**: Deep layout segmentation, reading-order reconstruction, and complex table structure parsing.
- **Section Hierarchy Detection (`section_detector.py`)**: Automatic identification and classification of canonical scientific sections (Abstract, Introduction, Related Work, Methodology, Experiments, Discussion, Conclusion).
- **Multi-Parser Reconciliation Engine (`merger.py`)**: Intelligent conflict resolution aligning text blocks, mathematical equations, and tables across different parsers into a unified `CanonicalPaperDocument`.
- **Quality & Completeness Auditing (`validator.py`)**: Automated scoring computing layout completeness, catching empty sections, and enforcing structural integrity.

---

### B. Specialized 8-Agent Autonomous Reasoning Mesh (`backend/app/agents/`)
1. **Decomposition Agent (`decomposition_agent.py`)**: Dissects raw academic methodology into a modular component dependency graph (`ComponentGraph`).
2. **Hyperparameter Extraction Agent (`parameter_agent.py`)**: Scans text and tables to discover training parameters (`learning_rate`, `batch_size`, `optimizer`, `weight_decay`, `backbone`, `epochs`).
3. **Hardware Feasibility & VRAM Profiler (`feasibility_agent.py`)**: Calculates tensor memory footprints and audits feasibility against local GPU VRAM limits.
4. **Gap Resolution Agent (`gap_agent.py`)**: Discovers unstated hyperparameter defaults, missing architectural details, and ambiguity gaps in the original paper.
5. **Build Sequencing Agent (`sequencing_agent.py`)**: Constructs Directed Acyclic Graph (DAG) build milestones and dependency execution sequences.
6. **Technical Specification Agent (`specification_agent.py`)**: Drafts rigorous implementation blueprints with input/output tensor shapes and layer configurations.
7. **Executive Proposal Agent (`report_agent.py`)**: Generates structured Markdown proposal reports complete with LaTeX mathematical formulations.
8. **Codebase Package Synthesizer (`code_gen_agent.py`)**: Synthesizes clean, modular 8-file PyTorch packages ready for local training and evaluation.

---

### C. 3-Layer Virtual Code Verification Gate (`backend/app/core/code_verifier.py`)
- **Layer 1 — AST Syntax Parsing**: Validates every generated `.py` file through Python's `ast.parse` to guarantee zero syntax or indentation errors.
- **Layer 2 — Dangerous Import Sandboxing**: Scans and blocks malicious modules or unsafe system calls (`os.system`, `subprocess`, socket operations).
- **Layer 3 — Mock Tensor & Shape Execution**: Performs dry-run tensor shape passes through model definitions to verify dimensional compatibility across layers.

---

### D. Local Flat-File RAG & Bipartite Knowledge Graph (`backend/app/retrieval/`)
- **Semantic Section Chunking (`chunker.py`)**: Chunks text while preserving cohesive math equations and algorithm logic.
- **Local Vector Search (`vector_db.py`)**: High-performance flat-file vector indexing with cosine similarity retrieval, avoiding external cloud database dependencies.
- **NetworkX Knowledge Graph (`knowledge_graph.py`)**: Bipartite graph mapping extracted entities (*Models, Datasets, Loss Functions, Metrics, Equations*) and semantic relations (`USES`, `EVALUATES_ON`, `COMPARES_TO`, `OPTIMIZES`).

---

### E. Conversational ReACT Agent & 7 Specialized Tools (`backend/app/agents/chat_agent.py`, `backend/app/tools/`)
- **ReACT Reasoning Cycle**: Multi-turn `Thought → Action → Observation → Final Answer` loop with persistent session memory.
- **7 Domain Tools**:
  1. `canonical_document_tool`: Queries full-text sections, raw LaTeX formulas, and tables.
  2. `hyperparameter_tool`: Inspects and updates model parameters.
  3. `vector_search_tool`: Retrieves relevant semantic text chunks.
  4. `graph_search_tool`: Traverses knowledge graph entities and relationship neighborhoods.
  5. `episodic_memory_tool`: Recalls previous conversation turns.
  6. `arxiv_search_tool`: Searches arXiv preprints for citations and baseline comparisons.
  7. `scholar_search_tool`: Validates academic venues, authors, and citation indices.

---

### F. Dynamic Multi-Provider Model Mesh & Sliding Quota Tracker (`backend/app/core/`)
- **Multi-Provider Adapter Mesh (`providers/`)**: Seamless integration across local Ollama (`qwen2.5-coder`), Groq (Llama 3.3 70B, DeepSeek), HuggingFace, and OpenRouter.
- **Sliding-Window Quota Tracker (`quota_tracker.py`)**: Real-time monitoring of Requests Per Minute (RPM) and Tokens Per Minute (TPM).
- **Autonomous HTTP 429 Cascade**: Instant failover switching across providers if cloud rate limits or latency spikes occur, ensuring zero downtime.

---

### G. Native Win32 C-FFI Taskbar Docking & Desktop Mascot (`frontend/electron_app/`)
- **Win32 C-FFI Interop (`main.js`)**: C-level foreign function interface via `koffi` binding directly to Windows `shell32.dll` (`SHAppBarMessage(ABM_GETTASKBARPOS)`) to track the exact screen coordinates of `Shell_TrayWnd`.
- **Dual-Window Lockstep Synchronization**: Simultaneous coordination between a frameless transparent mascot overlay (`mascotWindow`) and a floating React panel (`panelWindow`).
- **Dynamic Mouse Pass-Through**: Automatic switching between interactive clicking and background click-through (`setIgnoreMouseEvents`).
- **13-State Finite State Machine (`mascot.js`)**: Real-time canvas animation reflecting backend pipeline progress across 13 distinct mascot emotional states.
- **4 Selectable Character Avatars**: Full multi-character skin system (`mr_nerdy`, `ms_nerdy`, `mr_nerd`, `ms_nerd`).

---

### H. React 19 Desktop Analysis Workbench (`frontend/renderer/`)
- **Interactive Parameter Form (`ParameterConfigForm.tsx`)**: Allows researchers to inspect and adjust extracted hyperparameters before code generation.
- **DAG Milestone Progress Tracker (`MilestoneTracker.tsx`)**: Visualizes multi-stage pipeline milestones and agent execution status in real time.
- **Executive Report & Code Viewer (`ReportView.tsx`)**: Syntax-highlighted code viewer with LaTeX mathematical formula rendering and copy/download options.
- **Visual ReACT Accordion (`ReActStepsAccordion.tsx`)**: Transparent view into the agent's internal reasoning steps and tool execution results.
- **Hardware & Model Quota Dashboard (`UserProfile.tsx`, `ModelLimitsSection.tsx`)**: Live meters displaying local GPU VRAM, CPU utilization, and provider quota limits.
