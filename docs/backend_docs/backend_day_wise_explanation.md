# 📄 Backend Architecture — Phase-wise & Day-wise Technical Explanation

> **System Component:** Synthexis AI Platform Current Multi-Agent Backend  
> **LLM Engine:** 100% Local Ollama (`qwen2.5-coder:1.5b`) — Zero Cloud Dependency / 0 API Calls  
> **Storage Engine:** Local Flat-File JSON Cache (`rag_embeddings/`) & NetworkX Knowledge Graph (`knowledge_graphs/`)  
> **Verification Certificate:** **100% PASS** Across All 12 Phases on 48 Research Paper Corpus (332 PyTorch Files Synthesized, 100% AST Pass Rate)  
> **Master Project Plan Cross-Reference:** [`docs/backend_docs/Paper-2-Project_plan.md`](./Paper-2-Project_plan.md)  

---

### **Phase 1 — Scientific Ingestion & Tri-Parser Pipeline (Days 1 – 2)**

#### **Day 1: Backend Foundation & Tri-Parser Ingestion Engine**
* **What it does:** Establishes the modular backend package structure and configures local-first settings, routing LLM traffic directly to local Ollama runtime.
* **🔑 Important Elements:**
  * **Modular Package Layout**: Separates codebase cleanly into `app/core/`, `app/schemas/`, `app/extraction/`, `app/retrieval/`, `app/agents/`, `app/api/`.
  * **Local Settings & API Policy (`app/core/config.py`)**: Defines `DEFAULT_MODEL = "qwen2.5-coder:1.5b"` at `http://localhost:11434`. Free cloud APIs (Groq, OpenRouter) are intentionally disabled due to the exhaustion/extinction of free tier API keys (`HTTP 429 Rate Limit Exceeded`). All pipeline processing and test suite runs execute 100% locally to guarantee zero API dependencies and zero rate-limit failures.
  * **Tri-Parser Failover Chain**: Integrates PyMuPDF (fast coordinate layout extraction), GROBID (XML TEI academic parsing at `localhost:8070`), and Docling (layout markdown / OCR).

#### **Day 2: Canonical Paper Representation (`PaperDocument`)**
* **What it does:** Validates and saves extracted paper structures into a unified canonical JSON schema (`paper_10.json`) under `docs/new_backend_documents/e_2_e_reports/extracted_json/`.
* **🔑 Important Elements:**
  * **Pydantic Model Conformance**: Validates metadata, section hierarchies, tables, figures, and equations against the `PaperDocument` schema.
  * **Clean ID Normalization**: Implements standardized paper ID generators (`paper_1`, `paper_10`) stripping brackets `"[10]"` to ensure uniform disk file matching.

---

### **Phase 2 — Extraction Quality Validation (Day 3)**

#### **Day 3: Quality Validator Engine (`validate_paper_document`)**
* **What it does:** Runs deterministic quality validation rules over canonical paper JSON files, verifying document integrity before agent reasoning.
* **🔑 Important Elements:**
  * **Completeness Score Calculation**: Evaluates completeness across titles, abstracts, section trees, tables, and equations.
  * **Attribute Access Safety**: Prevents runtime errors by validating that `subsections`, `tables`, and `equations` fields are non-null lists.
  * **Verification Scorecard**: Returns `QA_PASS` status across all 48 test papers.

---

### **Phase 3 — Local RAG Vector DB & Knowledge Graph (Day 4)**

#### **Day 4: Flat-File Vector DB & NetworkX Knowledge Graph**
* **What it does:** Slices canonical papers into semantic text chunks and builds a local flat-file vector DB and NetworkX Knowledge Graph without external database servers.
* **🔑 Important Elements:**
  * **Semantic Chunker (`chunk_paper_document`)**: Slices text by paragraph boundaries while preserving tables, figures, and equations as unfragmented units.
  * **Local Embedding Generation (`generate_local_embedding`)**: Produces dense float vector embeddings locally.
  * **Flat-File Cache (`PaperVectorDB`)**: Stores chunks and raw vector floats directly into `docs/new_backend_documents/e_2_e_reports/rag_embeddings/paper_10.json`.
  * **NetworkX Knowledge Graph (`PaperKnowledgeGraph`)**: Constructs visual graph topologies (`knowledge_graphs/paper_10_kg.json`) mapping encoders, fusion layers, decoders, and loss functions.

---

### **Phase 4 — Paper Understanding & Hyperparameter Agents (Day 5)**

#### **Day 5: Agent 1 (Decomposition) & Agent 2 (Parameter Agent)**
* **What it does:** Executes Agent 1 to infer component graphs and Agent 2 to extract training hyperparameters.
* **🔑 Important Elements:**
  * **Agent 1 — Method Decomposition**: Analyzes method sections to infer a `ComponentGraph` (encoders, attention layers, fusion modules, decoders, losses).
  * **Agent 2 — Parameter Agent**: Extracts 11 critical hyperparameters (`learning_rate`, `batch_size`, `optimizer`, `weight_decay`, `backbone`) with provenance annotations (`EXPLICIT`, `INFERRED`, `ASSUMED`).
  * **100% Local Inference**: Runs structured Pydantic decoding via local Ollama (`qwen2.5-coder:1.5b`).

---

### **Phase 5 — CUDA VRAM Feasibility & Gap Resolution (Day 6)**

#### **Day 6: Agent 3 (CUDA VRAM Feasibility) & Agent 4 (Gap Resolver)**
* **What it does:** Profiles system GPU hardware against model memory requirements and resolves missing parameter gaps.
* **🔑 Important Elements:**
  * **Agent 3 — CUDA VRAM Feasibility Engine**: Queries host system hardware (`get_hardware_metrics`: Windows AMD64, 16 CPU cores, 23.6 GB RAM, `NVIDIA GeForce RTX 5050` CUDA GPU with 8.0 GB VRAM). Calculates memory footprint (e.g., 1.5 GB vs 8.0 GB available) and output verdicts (`FEASIBLE`, `FEASIBLE_WITH_MODIFICATION`).
  * **Agent 4 — Parameter Gap Resolution Agent**: Identifies missing parameters (`MISSING`, `AMBIGUOUS`) and applies fallback scaling heuristics (e.g. reducing batch size, adding gradient accumulation).

---

### **Phase 6 — Build Sequencing, Specification & Executive Report (Day 7)**

#### **Day 7: Agent 5 (Sequencer), Agent 6 (Tech Spec) & Agent 7 (Report Agent)**
* **What it does:** Constructs milestone build DAGs, technical specifications, and executive markdown proposals.
* **🔑 Important Elements:**
  * **Agent 5 — Build Sequencing**: Generates a 6-step Directed Acyclic Graph (DAG) build sequence (`BuildSequence`) where cheap validation steps precede compute-heavy training.
  * **Agent 6 — Technical Specification Blueprint**: Generates an engineering specification (`ProjectSpecification`) detailing architecture specs, data loaders, loss functions, and scaled hyperparameters.
  * **Agent 7 — Adaptation Report Agent**: Synthesizes specifications and feasibility verdicts into a portfolio-grade markdown proposal report per paper.

---

### **Phase 7 — PyTorch Code Generation Agent (Day 8)**

#### **Day 8: Agent 8 — PyTorch Codebase Package Synthesizer**
* **What it does:** Synthesizes an 8-file modular PyTorch codebase package for every research paper.
* **🔑 Important Elements:**
  * **8 Modular PyTorch Source Files**:
    1. `config.py`: Hyperparameters and configuration dataclasses.
    2. `dataset.py`: PyTorch `Dataset` & `DataLoader` implementations.
    3. `models/encoder.py`: Feature extraction backbone architecture.
    4. `models/fusion.py`: Multi-modal / temporal fusion layers.
    5. `models/decoder.py`: Task prediction decoder head.
    6. `losses.py`: Loss functions (Cross-Entropy, Focal, Dice).
    7. `train.py`: Training loop with optimizer and learning rate scheduler.
    8. `evaluate.py`: Evaluation metrics and validation loop.
  * **Disk Codebase Persistence**: Saves synthesized PyTorch source files directly to `docs/new_backend_documents/e_2_e_reports/phase_8_codes/paper{id}/codes/`. Synthesized 332 Python source files across 48 paper repositories.

---

### **Phase 8 — Code Verification & Conversational ReACT Memory (Days 9 – 10)**

#### **Day 9: Phase 9 — AST Code Verification & Syntax Auditing**
* **What it does:** Runs Python's native AST parser (`ast.parse`) across all 332 synthesized PyTorch code files on disk to verify 100% syntactic correctness (0.29 s execution time).

#### **Day 10: Phase 10 — Multi-Turn ReACT Chat & Memory Engine**
* **What it does:** Multi-turn conversational ReACT Agent (`ChatAgent`) grounded in RAG chunks with local database chat history persistence (`ChatDatabase`).

---

### **Phase 9 — Model Router & Hardware Telemetry (Days 11 – 14)**

#### **Day 11: Phase 11 — Model Router Throughput & Latency Benchmarking**
* **What it does:** Benchmarks dynamic prompt routing throughput (`ModelRouter`) on local Ollama (`qwen2.5-coder:1.5b`), tracking prompt latency.

#### **Day 12: Phase 12 — FastAPI Hardware Telemetry Endpoint**
* **What it does:** Exposes telemetry endpoints (`get_hardware_metrics`) auditing system hardware (Windows AMD64, 16 CPU cores, 23.6 GB RAM, RTX 5050 CUDA GPU).

#### **Day 13: End-to-End Test Suite Automation (`end_to_end_backend_testing.ipynb`)**
* **What it does:** Automates and verifies all 12 notebook phases across the 48 research paper corpus (~5.9 hours total execution time).

#### **Day 14: Golden Corpus Benchmark Verification & Report Finalization**
* **What it does:** Finalizes master scorecard metrics and compiles master test report ([`docs/backend_docs/master_e2e_backend_test_report.md`](./master_e2e_backend_test_report.md)).

---

## 🚀 Master E2E Backend Testing Framework (`end_to_end_backend_testing.ipynb`)

The complete 12-phase backend pipeline is automated and verified via **`backend/tests/end_to_end_backend_testing.ipynb`**.

### **⚙️ E2E Test Suite Orchestration (All 12 Notebook Phases)**

| Phase # | Phase Title | Target Component / Agent | Test Corpus | Status | Execution Time | Benchmark Result |
|---|---|---|---|---|---|---|
| **Phase 1** | Scientific Paper Extraction | Ingestion Engine (PyMuPDF + GROBID + Docling) | 48 PDFs | **PASS** | 1,679.59 s | 48/48 3-Tier IEEE Titles & Section Trees |
| **Phase 2** | Canonical Representation | Canonical Schema Validator | 48 JSONs | **PASS** | 0.37 s | 48/48 Schema Conformance (`PaperDocument`) |
| **Phase 3** | Extraction Quality Validation | Validator Engine (`validate_paper_document`) | 48 Papers | **PASS** | 6.33 s | 48/48 QA_PASS (Completeness Scores Calculated) |
| **Phase 4** | Local RAG Vector DB & KG | Hybrid Vector Retriever & NetworkX Engine | 48 Papers | **PASS** | 4.88 s | 3 RAG Chunks & 15+ KG Nodes per Paper |
| **Phase 5** | Paper Understanding | Agent 1 (Decomp) & Agent 2 (Parameter) | 48 Papers | **PASS** | 8,284.86 s | ComponentGraph & Hyperparameters Extracted |
| **Phase 6** | Feasibility & Gap Resolution | Agent 3 (VRAM Profiler) & Agent 4 (Gap Resolver) | 48 Papers | **PASS** | 465.54 s | Real-Time GPU VRAM & Parameter Gap Auditing |
| **Phase 7** | Build Sequencing & Spec | Agent 5 (Sequencer), Agent 6 (Spec), Agent 7 (Report) | 48 Papers | **PASS** | 1,578.33 s | 6-Milestone DAGs & Technical Specifications |
| **Phase 8** | PyTorch Code Generation | Agent 8 (Codebase Package Synthesizer) | 48 Papers | **PASS** | 7,588.83 s | 332 PyTorch Source Files Synthesized across 48 Repos |
| **Phase 9** | Code Verification & AST Check | AST Syntax Validator (`ast.parse`) | 332 Files | **PASS** | 0.29 s | 100% AST Syntax Validity across 332 Files |
| **Phase 10** | Multi-Turn Chat & ReACT Memory | Conversational Agent (`ChatAgent` + Memory) | 48 Papers | **PASS** | 1,631.38 s | Multi-Turn Context-Aware Q&A Responses |
| **Phase 11** | Model Router Throughput | Dynamic Router (`ModelRouter`) | 3 Prompts | **PASS** | 13.87 s | 100% Local Ollama Latency Benchmarks |
| **Phase 12** | FastAPI Hardware Telemetry | Telemetry Endpoint (`get_hardware_metrics`) | System | **PASS** | 0.09 s | Windows, 16 CPU Cores, RTX 5050 CUDA GPU VRAM |

*Consolidated master test results are saved to [`docs/backend_docs/master_e2e_backend_test_report.md`](./master_e2e_backend_test_report.md).*
