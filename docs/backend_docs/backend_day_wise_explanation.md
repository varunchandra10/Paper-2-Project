# 📄 Backend Architecture — Phase-wise Technical Explanation

> **System:** RUEXIS AI Platform v2.0  
> **LLM Engines:** Groq (Qwen 3.8 27B, GPT-OSS 120B) · OpenRouter (Gemini 2.5 Flash, DeepSeek R1) · Hugging Face (Qwen 2.5 Coder 32B) · Gemini · Local Ollama  
> **Storage:** Flat-file JSON (`storage/`) — conversations, RAG embeddings, knowledge graphs, codes  
> **Test Verification:** 100% PASS across all 12 phases on 48-paper corpus (332 PyTorch files synthesized, 100% AST pass rate)

---

## Phase 1 — Scientific Ingestion & Multi-Engine Extraction

### Day 1: Backend Foundation & Multi-Engine PDF Parser

**What it does:** Establishes the modular package structure, configures multi-provider settings, and builds the PDF extraction pipeline.

**Key elements:**

- **Modular Package Layout** — Clean separation into `app/core/`, `app/schemas/`, `app/extraction/`, `app/retrieval/`, `app/agents/`, `app/api/`, `app/providers/`, `app/graph/`, `app/tools/`
- **Multi-Provider Config (`app/core/config.py`)** — Manages API keys for Groq, OpenRouter, Gemini, HuggingFace, Ollama. Each provider has a `has_*()` availability check. Settings are hot-reloaded from `.env` on first access.
- **Multi-Engine Extraction (`app/extraction/`)** — Four-parser system:
  1. **Docling** — Primary (structure-aware, ML-native layout parsing)
  2. **PyMuPDF** — Fallback (coordinate layout, font metrics)
  3. **GROBID** — Optional (TEI XML scholarly metadata at `localhost:8070`)
  4. **OpenRouter / Gemini** — Gemini 2.5 Flash for complex scientific PDFs
  
  `merger.py` reconciles outputs into a canonical JSON with sections, equations, figures, and tables.

---

### Day 2: Canonical Paper Representation

**What it does:** Saves structured extraction output into a unified canonical JSON under `storage/extracted_json/{paper_id}.json`.

**Key elements:**

- **Pydantic Schema Conformance** — Validates metadata, section hierarchies, tables, figures, and equations
- **Paper ID Generator** — Slug-based ID from filename (`paper_attention_is_all_you`) for stable disk references
- **Deduplication** — MD5 hash check on upload prevents re-processing the same file

---

## Phase 2 — Extraction Quality Validation

### Day 3: Quality Validator Engine

**What it does:** Runs deterministic validation rules over canonical JSON files before agent reasoning begins.

**Key elements:**

- **Completeness Scoring** — Evaluates section coverage, abstract presence, equation count, figure count
- **Section Detection (`section_detector.py`)** — Pattern-based identification of Introduction, Method, Experiments, Conclusion
- **Result** — 48/48 `QA_PASS` on test corpus (6.33 s)

---

## Phase 3 — RAG Vector DB & Knowledge Graph

### Day 4: FAISS Vector Index & NetworkX Knowledge Graph

**What it does:** Chunks the canonical paper and builds per-paper FAISS vector index and NetworkX knowledge graph for retrieval.

**Key elements:**

- **Semantic Chunker (`chunker.py`)** — Overlapping paragraph-boundary chunks preserving equations and tables as atomic units
- **Embeddings (`embeddings.py`)** — Sentence-transformer dense vectors for FAISS indexing
- **FAISS Vector DB (`vector_db.py`)** — Per-paper index stored in `storage/rag_embeddings/`. Similarity search returns top-k chunks with scores.
- **Knowledge Graph (`knowledge_graph.py`)** — NetworkX graph mapping paper entities: methods, datasets, metrics, citations, hyperparameters. Saved to `storage/knowledge_graphs/{paper_id}_kg.json`.

---

## Phase 4 — LangGraph 5-Node Autonomous Pipeline

### Day 5: Pipeline Architecture & IngestionAgent + ParameterAgent

**What it does:** Builds the LangGraph `StateGraph` workflow and implements the first two nodes.

**Key elements:**

- **LangGraph Workflow (`app/graph/workflow.py`)** — Compiles a `StateGraph` with 5 sequential nodes sharing `PipelineState`
- **IngestionAgent** — Loads the canonical paper JSON into pipeline state
- **ParameterAgent** — Extracts ML hyperparameters (`learning_rate`, `batch_size`, `optimizer`, `backbone`, `weight_decay`) with source provenance (`EXPLICIT`, `INFERRED`, `ASSUMED`)

---

### Day 6: FeasibilityAgent & SequencingAgent

**What it does:** Audits hardware constraints and sequences implementation milestones.

**Key elements:**

- **FeasibilityAgent** — Queries `GET /hardware/metrics` (psutil + nvidia-smi) and scores whether the paper's model fits in available VRAM. Returns `FEASIBLE` / `FEASIBLE_WITH_MODIFICATION` / `NOT_FEASIBLE` with adaptation suggestions.
- **SequencingAgent** — Generates an ordered 6-milestone build DAG (`BuildSequence`): cheap validation steps before compute-heavy training.

---

### Day 7: CodeGenAgent & Dual Code Engine

**What it does:** Synthesizes verified PyTorch implementation code as the pipeline's final node.

**Key elements:**

- **Dual Code Engine (`app/core/dual_code_engine.py`)** — Runs two engines in parallel:
  - **Engine A** — `Qwen/Qwen2.5-Coder-32B-Instruct` via Hugging Face (idiomatic PyTorch specialist)
  - **Engine B** — `gemini-2.5-flash` via Gemini API (deep paper context + mathematical precision)
- **Merge & Validation** — Both outputs are AST-validated (`ast.parse`) + security-checked (`os.system`, `eval`, `exec` blocklisted). Best syntactically valid output is selected.
- **Code Verifier (`code_verifier.py`)** — Final verification pass on the merged output
- **Output** — Complete PyTorch codebase saved to `storage/codes/{paper_id}/`

---

## Phase 5 — ReACT Chat Agent

### Day 8: ChatAgent — Multi-Turn ReACT Inference Loop

**What it does:** Implements the primary conversational interface with tool-augmented reasoning.

**Key elements:**

- **ReACT Loop (`chat_agent.py`)** — Up to 5 reasoning turns: THOUGHT → ACTION (tool call) → OBSERVATION → repeat → Final Answer
- **Context Assembly (`context_builder.py`)** — Merges user facts, extracted hyperparameters, episodic memory, and recent chat history into the LLM prompt
- **SSE Streaming** — Streams `status`, `thought`, `action`, `observation`, `token`, `done`, `error` events to the frontend
- **Smart Titler (`smart_titler.py`)** — Generates a concise 3–5 word conversation title on first message
- **ChatDatabase** — Flat-file JSON conversation store (`storage/conversations/{id}.json`) with `get_active_conversation_id()` / `set_active_conversation_id()`

---

### Day 9: Tools Registry

**What it does:** Implements all 7 ReACT tools callable by `ChatAgent`.

| Tool | File | Purpose |
|------|------|---------|
| `arxiv_search` | `arxiv_search_tool.py` | Search arXiv by query |
| `scholar_search` | `scholar_search_tool.py` | Google Scholar via Tavily |
| `vector_search` | `vector_search_tool.py` | FAISS semantic search within paper |
| `graph_search` | `graph_search_tool.py` | Entity/relationship lookup in knowledge graph |
| `canonical_document` | `canonical_document_tool.py` | Full structured paper JSON |
| `hyperparameter_tool` | `hyperparameter_tool.py` | Extracted hyperparameters for a paper |
| `episodic_memory` | `episodic_memory_tool.py` | Past context from agent episodic memory |

---

## Phase 6 — ModelRouter & Multi-Provider Dispatch

### Day 10: ModelRouter — Provider Dispatch & Quota-Aware Failover

**What it does:** Routes inference requests to the correct provider and handles automatic failover.

**Key elements:**

- **Provider Priority** — `Groq → OpenRouter → Ollama` (configurable by `model_id` prefix)
- **Adapters** — Separate adapter modules per provider: `groq_adapter.py`, `openrouter_adapter.py`, `hf_adapter.py`, `ollama_adapter.py`
- **User API Key Support** — Reads private Groq/OpenRouter keys from `user_profile.json` (set via Profile page) as fallback to `.env` keys
- **Auto-Failover** — On HTTP 429 or error, retries next available provider; `resolve_failover_model_id()` maps the used model back to the frontend model ID
- **Quota Tracker (`quota_tracker.py`)** — Rolling 1-min / 60-min / 24-hr usage windows; feeds `GET /models/limits` for live quota dashboard

---

## Phase 7 — API Layer

### Day 11: FastAPI Endpoints

**What it does:** Exposes all backend capabilities via versioned REST + SSE endpoints under `/api/v1`.

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| `auth.py` | `/auth` | Local login/registration |
| `chat.py` | `/conversations` | CRUD + streaming chat |
| `papers.py` | `/upload`, `/history` | PDF upload, paper management, profile |
| `pipeline.py` | `/pipeline`, `/stream` | LangGraph trigger + SSE progress |
| `models.py` | `/models` | Model catalog, limits, dual-engine status |
| `hardware.py` | `/hardware` | Live CPU/GPU metrics |
| `telemetry.py` | `/telemetry` | Agent execution traces |

---

## Phase 8 — AST Verification & Code Quality

### Day 12: Code Verifier & AST Gate

**What it does:** Validates all generated PyTorch code for syntax correctness and security.

**Key elements:**

- **`ast.parse()` validation** — 100% pass rate across 332 synthesized files in v1 test corpus
- **Security blocklist** — Rejects any code containing `os.system`, `subprocess.run`, `eval`, `exec`, `__import__`
- **Code Verifier (`core/code_verifier.py`)** — Additional semantic checks beyond AST syntax

---

## Phase 9 — Hardware Telemetry

### Day 13: Hardware Metrics Endpoint

**What it does:** Exposes live system hardware information for the frontend hardware panel.

**Key elements:**

- **CPU** — `psutil` reports cores, RAM total/used/available, CPU usage %
- **GPU** — `nvidia-smi` primary (VRAM total/used/free), PyTorch CUDA fallback
- **Platform** — OS, architecture, processor name via `platform` module

---

## Phase 10 — Quota Dashboard

### Day 14: Rate Limits Dashboard & Quota Tracker

**What it does:** Tracks and visualizes API quota usage across all providers.

**Key elements:**

- **Rolling Windows** — 1-minute, 60-minute, and 24-hour request + token counts
- **Provider Coverage** — Separate counters for Groq, OpenRouter, Gemini, HuggingFace
- **HTML Dashboard** — `limits_dashboard.py` generates a styled HTML page at `GET /limits-dashboard`
- **JSON API** — `GET /models/limits` returns machine-readable quota data for the frontend quota cards

---

## 📊 E2E Test Phase Summary

| Phase | Title | Agent / Component | Corpus | Status | Time |
|-------|-------|-------------------|--------|--------|------|
| 1 | Scientific Extraction | Docling + PyMuPDF + GROBID + Gemini | 48 PDFs | **PASS** | 1,679.59 s |
| 2 | Canonical Representation | Schema Validator (`PaperDocument`) | 48 JSONs | **PASS** | 0.37 s |
| 3 | Quality Validation | `validate_paper_document` | 48 Papers | **PASS** | 6.33 s |
| 4 | RAG & Knowledge Graph | FAISS + NetworkX | 48 Papers | **PASS** | 4.88 s |
| 5 | Paper Understanding | ParameterAgent + DecompositionAgent | 48 Papers | **PASS** | 8,284.86 s |
| 6 | Feasibility & Gap | FeasibilityAgent + GapAgent | 48 Papers | **PASS** | 465.54 s |
| 7 | Sequencing & Spec | SequencingAgent + SpecificationAgent + ReportAgent | 48 Papers | **PASS** | 1,578.33 s |
| 8 | PyTorch Code Generation | CodeGenAgent + Dual Code Engine | 48 Papers | **PASS** | 7,588.83 s |
| 9 | AST Verification | `ast.parse` + code_verifier | 332 Files | **PASS** | 0.29 s |
| 10 | Multi-Turn Chat | ChatAgent + ReACT + 7 Tools | 48 Papers | **PASS** | 1,631.38 s |
| 11 | Model Router | ModelRouter + 4 provider adapters | 3 Prompts | **PASS** | 13.87 s |
| 12 | Hardware Telemetry | `get_hardware_metrics` | System | **PASS** | 0.09 s |

*Full test report: [`master_e2e_backend_test_report.md`](./master_e2e_backend_test_report.md)*
