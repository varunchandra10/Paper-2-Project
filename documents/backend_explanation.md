# Backend Codebase — Deep Technical Explanation

> **Project**: Paper-2-Project (RUEXIS AI Platform v2.0.0)
> **Architecture**: LangGraph V2 StateGraph Pipeline + FastAPI REST backend
> **All paths** are relative to the project root: `Paper-2-Project/`

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Directory Structure Map](#2-directory-structure-map)
3. [Entry Point](#3-entry-point)
4. [Core Layer](#4-core-layer)
5. [Graph Layer](#5-graph-layer)
6. [Agents](#6-agents)
7. [Extraction Layer](#7-extraction-layer)
8. [Retrieval Layer](#8-retrieval-layer)
9. [Tools](#9-tools)
10. [API Layer](#10-api-layer)
11. [Schemas](#11-schemas)
12. [Providers](#12-providers)
13. [Evaluation](#13-evaluation)
14. [Tests](#14-tests)
15. [Storage Layout](#15-storage-layout)
16. [End-to-End Data Flow](#16-end-to-end-data-flow)

---

## 1. System Overview

RUEXIS AI is a research-paper-to-code platform. Given a research PDF, it:

1. **Parses** the PDF using a multi-parser consensus pipeline (Docling, PyMuPDF, GROBID, Gemini).
2. **Extracts** structured parameters (learning rate, batch size, architecture, loss function, etc.) grounded to exact paper quotes.
3. **Checks hardware feasibility** — adapts parameters to available GPU VRAM.
4. **Sequences** a build order using DAG topological sort.
5. **Generates** a full PyTorch codebase using a Dual-Engine tournament (Gemini + Qwen 2.5 Coder 32B).
6. **Verifies** the code through a 12-rung verification ladder (AST to Compile to Runtime to Paper Fidelity).
7. **Auto-repairs** failed code using Reflexion-style prompting.
8. **Serves** a conversational RAG chat interface over the extracted paper content.

The entire pipeline is orchestrated by **LangGraph V2** as a bounded StateGraph with two conditional self-correcting loops.

---

## 2. Directory Structure Map

```
backend/
├── main.py                   ← FastAPI entry point
├── requirements.txt          ← Python dependencies
├── pytest.ini                ← Pytest configuration
├── storage/                  ← All runtime data (git-ignored)
│   ├── papers/               ← Uploaded PDF files
│   ├── extracted_json/       ← Canonical JSON documents
│   ├── rag_embeddings/       ← Per-paper vector embeddings
│   ├── knowledge_graphs/     ← Per-paper KG JSON
│   ├── conversations/        ← Chat session history
│   ├── manifests/            ← Run reproducibility manifests
│   ├── history/              ← Quota state, chat memory DB
│   ├── codes/                ← Generated PyTorch code archives
│   └── jobs.db               ← SQLite WAL job store
└── app/
    ├── core/                 ← Infrastructure services (19 files)
    ├── graph/                ← LangGraph pipeline nodes and workflow
    ├── agents/               ← Conversational and code-gen agents
    ├── extraction/           ← PDF parsing and consensus extraction
    ├── retrieval/            ← Embeddings, vector DB, knowledge graph
    ├── tools/                ← ReACT tools for the chat agent
    ├── api/                  ← FastAPI routers and HTTP endpoints
    ├── schemas/              ← Pydantic data models
    ├── providers/            ← LLM provider adapters
    └── evals/                ← RAG evaluation framework
tests/                        ← Full test suite (33 files)
```

---

## 3. Entry Point

**File**: `backend/main.py` | 98 lines

### Responsibilities

**Application Init**: Creates the FastAPI ASGI app (`title="RUEXIS AI Platform"`, `version="2.0.0"`).

**CORS Middleware**: Allows requests from Vite dev (`localhost:5173`), Vite preview (`localhost:4173`), local dashboard (`localhost:8000`), and Electron production (`app://.`).

**Startup Hook — Zombie Job Recovery**:
```python
@app.on_event("startup")
def on_startup():
    recovered = get_job_store().recover_stale_jobs()
```
On every boot, marks jobs stuck in `queued/processing/running` state from a previous crashed session as `FAILED`. Prevents ghost jobs from polluting job status.

**Routes**:

| Route | Response | Purpose |
|---|---|---|
| `GET /` | HTML or JSON | Browser gets limits dashboard; API client gets JSON status |
| `GET /limits-dashboard` | HTML | Live rate limits and quota visual dashboard |
| `GET /api/status` | JSON | Machine-readable health check |

---

## 4. Core Layer

**Directory**: `backend/app/core/` — the infrastructure spine.

---

### 4.1 config.py — Application Configuration

**File**: `backend/app/core/config.py` | 145 lines

The `Settings` class reads from `.env` using `python-dotenv`.

- Defines all storage directory paths: `STORAGE_DIR`, `PAPERS_DIR`, `RAG_EMBEDDINGS_DIR`, `MANIFESTS_DIR`, etc.
- Exposes API keys for Groq, OpenRouter, Gemini, HuggingFace, Tavily — each with a `has_<provider>()` validation method.
- `SECRET_KEY` property **refuses to start** with the default dummy value, forcing real key generation.
- `ensure_directories()` called at import time — all storage folders created on first run.
- `_reload_env()` hot-reloads `.env` from disk dynamically.
- Legacy providers (Cerebras, SambaNova) are commented out but preserved to show provenance.

---

### 4.2 job_store.py — Persistent Job Tracker

**File**: `backend/app/core/job_store.py` | 578 lines

`JobStore` is a thread-safe, SQLite-backed persistence layer for tracking long-running analysis jobs using **WAL (Write-Ahead Logging)** mode.

**Two SQLite tables:**

| Table | Purpose |
|---|---|
| `jobs` | One row per job. Tracks `status`, `progress`, `current_stage`, `result`, `error`, timestamps, `cancellation_requested` |
| `job_events` | Append-only ordered event log. Used by SSE to stream live progress to frontend |

**Key class**: `JobRecord` — a `@dataclass` mapping directly to a SQLite row.

**Key methods:**

| Method | Description |
|---|---|
| `create_job()` | Creates a new job record with UUID |
| `get_job()` | Looks up by `job_id` first, falls back to `paper_id` |
| `update_stage()` | Updates progress percentage and stage label atomically |
| `complete_job()` | Sets status COMPLETED, progress 100.0, stores result JSON |
| `fail_job()` | Sets status FAILED, stores error string |
| `cancel_job()` | Sets `cancellation_requested = 1`, status CANCELLED |
| `recover_stale_jobs()` | Mass-updates all stuck active jobs to FAILED on server restart |
| `record_event()` | Appends event to `job_events`. Keeps `jobs` progress in sync |
| `get_events()` | Retrieves ordered events after `since_id` (SSE catch-up without duplicates) |

`JobStoreDictWrapper` — `MutableMapping` shim for backward-compatible legacy code.
`get_job_store()` — singleton factory using double-checked locking.

---

### 4.3 events.py — Event-Driven Observability Framework

**File**: `backend/app/core/events.py` | 221 lines

Implements structured telemetry events emitted at each LangGraph node boundary.

**Event types** (`EventTypes` class): `node_started`, `node_completed`, `refinement`, `retry`, `error`, `pipeline_started`, `pipeline_completed`, `pipeline_failed`, `mascot_state`.

**`NODE_PROGRESS_MAP`** — deterministic node-derived progress percentages:
- `ingestion_node` = 15%, `extraction_node` = 30%, `feasibility_node` = 45%
- `sequencing_node` = 60%, `specification_node` = 70%
- `code_generation_node` = 85%, `evaluation_node` = 95%, `completed` = 100%

**`NODE_MASCOT_MAP`** — maps each node to a UI mascot animation state (reading > analyzing > evaluating > adapting > planning > architecting > coding > testing > ready). Drives frontend character animations.

**Convenience emitters**: `emit_node_start()`, `emit_node_complete()`, `emit_refinement()`, `emit_retry()`, `emit_node_error()` — all called by `wrap_node_with_telemetry()` in `workflow.py`.

---

### 4.4 model_router.py — Dynamic LLM Router

**File**: `backend/app/core/model_router.py` | 203 lines

`ModelRouter` is the central LLM dispatch layer for **chat and Q&A** (not code generation, which uses `DualCodeEngine`).

**Failover chain on Groq HTTP 429**:
```
Groq → Gemini 2.0 Flash → OpenRouter → HuggingFace Qwen → Graceful error message
```

Integrates with `QuotaTracker` to avoid retrying exhausted providers. Supports user-configured API keys from `user_profile.json` (takes priority over `.env`).

---

### 4.5 dual_code_engine.py — Dual-Engine Code Synthesizer

**File**: `backend/app/core/dual_code_engine.py` | 397 lines

`DualCodeEngine` runs **parallel code generation** using two specialized models and selects the best result via a tournament.

| Engine | Model | Specialty |
|---|---|---|
| Gemini | `gemini-2.5-flash` (1M context) | Deep paper math, long-context reasoning |
| HuggingFace Qwen | `Qwen2.5-Coder-32B-Instruct` | Idiomatic PyTorch, clean API style |

**Core flow**: Both engines synthesize code simultaneously (`asyncio` + `httpx`) → each candidate AST-validated and security-checked → scored on paper grounding (hyperparameter match count) → winner = highest score; loser kept as fallback.

Also implements `generate_single_engine()` for the Phase 14 Single vs. Dual Model benchmark. Dual architecture is retained by default.

`extract_python_code()` strips markdown fences from LLM output.

---

### 4.6 code_verifier.py — 12-Rung Verification Ladder

**File**: `backend/app/core/code_verifier.py` | 626 lines

`CodeVerifier` implements a **12-rung progressive verification ladder** for generated PyTorch code.

| Rungs | Category | What it checks |
|---|---|---|
| 1 | AST Syntax | Grammar valid, no hollow stubs, no `NotImplementedError` |
| 2 | Security | No `exec()`, `eval()`, `os.system()`, `subprocess`, `__import__`, network access |
| 3 | Imports | Required PyTorch imports present |
| 4 | Bytecode Compile | `compile()` succeeds — catches issues AST misses |
| 5-11 | Dynamic Execution | Subprocess sandbox: init > forward > loss > backward > optimizer step > tiny loop |
| 12 | Paper Fidelity | Extracted hyperparameters appear in generated code |

`check_banned_primitives()` walks the AST tree to detect dangerous calls. `CodeVerificationReport` (Pydantic) collects all rung results and computes overall `PASSED / FAILED`.

---

### 4.7 dag_validator.py — Build Sequence DAG Validator

**File**: `backend/app/core/dag_validator.py` | 247 lines

`DAGValidator` validates that component build sequences form a valid Directed Acyclic Graph.

**Error codes**: `EMPTY_PLAN`, `INVALID_NODE_ID`, `DUPLICATE_NODE`, `MISSING_DEPENDENCY`, `SELF_DEPENDENCY`, `CYCLE_DETECTED` (DFS with exact trace returned), `ORPHAN_NODE`.

**Output**: `DAGValidationResult` with `is_valid`, `execution_order` (topological sort), `issues[]`, `cycle_path`.

---

### 4.8 manifest.py — Reproducibility and Run Manifests

**File**: `backend/app/core/manifest.py` | 333 lines

Implements the **Phase 10 Reproducibility Framework**. Every analysis run generates an immutable `RunManifest` JSON capturing all 18 provenance fields.

| Section | Key Fields |
|---|---|
| `paper` | `paper_id`, `paper_hash` (SHA-256), `paper_version`, `file_name`, `file_size_bytes` |
| `model_info` | `model`, `model_version`, `provider`, `temperature`, `top_p`, `prompt_version` |
| `retrieval_config` | `embedding_model`, `embedding_version`, `chunk_size`, `chunk_overlap`, `retrieval_strategy`, `top_k` |
| `system` | `software_version`, `os`, `platform`, `python_version`, `torch_version`, `git_commit` |
| `hardware` | `cpu`, `cpu_cores`, `total_ram_gb`, `gpu_available`, `gpu_device`, `gpu_vram_total_gb` |

**Key functions**: `compute_file_sha256()`, `get_git_commit()`, `inspect_hardware()` (via `psutil` + `torch.cuda`), `generate_run_manifest()`, `save_manifest()` (atomic write: temp file + `os.replace`), `explain_run()` (human-readable explanation of why a run produced its result).

Saved to `backend/storage/manifests/{run_id}.json`.

---

### 4.9 quota_tracker.py — Dynamic Rate Limit Tracker

**File**: `backend/app/core/quota_tracker.py` | 643 lines

`QuotaTracker` tracks rolling-window API quotas for all LLM providers dynamically (not hardcoded). Fetches live quota data from provider APIs, persists state to `storage/history/model_quotas.json`, and exposes `is_provider_available()` for model router failover decisions.

---

### 4.10 cost_optimizer.py — Cost and Resource Optimization

**File**: `backend/app/core/cost_optimizer.py` | 355 lines

`CostAndResourceOptimizer` measures and reduces token spend and latency.

| Feature | Mechanism |
|---|---|
| Token accounting | Character-based heuristic (4 chars ≈ 1 token) |
| Cost estimation | Tokens x `MODEL_PRICING` table (USD per million tokens) |
| Prompt cache | SHA-256(prompt) → stored result (instant on cache hit) |
| Paper ingestion cache | SHA-256(PDF) → skip parse/embed if already processed |
| Embedding cache | SHA-256(chunk text) → stored vector without re-embedding |
| Duplicate call detection | Tracks call signatures; flags repeated identical invocations |
| Latency tracking | Records ms per pipeline stage via `record_latency()` |

Pricing: Local/Ollama ($0), Groq ($0.59/$0.79 per M tokens), Gemini ($0.15/$0.60), HuggingFace ($0.20/$0.20), OpenRouter ($0.15/$0.60).

---

### 4.11 limits_dashboard.py — Live HTML Dashboard

**File**: `backend/app/core/limits_dashboard.py` | ~19KB

Generates a self-contained HTML page (`/limits-dashboard`) showing real-time quota consumption for all LLM providers. Server-side rendered, no external dependencies. Features animated progress bars, provider cards, and auto-refresh.

---

### 4.12 prompts.py — Centralized Prompt Library

**File**: `backend/app/core/prompts.py` | ~31KB

Contains **all** LLM prompts used throughout the system. No prompt strings appear anywhere else in the codebase — all agents and nodes import from this single file.

Key prompts: `CODE_SYNTHESIS_SYSTEM_PROMPT`, `build_code_synthesis_user_prompt()`, `build_codegen_agent_prompt()`, `build_reflexion_repair_prompt()`, and per-stage extraction prompts.

---

### 4.13 constants.py — Global Constants

**File**: `backend/app/core/constants.py` | 3.7KB

All magic values: provider API endpoint URLs, default model identifiers, default hyperparameter fallbacks (`DEFAULT_HYPERPARAMETERS`), default pipeline file names (`DEFAULT_PIPELINE_FILES`), initial quota limits per provider.

---

### 4.14 security.py — JWT Authentication Utilities

**File**: `backend/app/core/security.py` | 511 bytes

`create_access_token()` signs a payload with `SECRET_KEY` using HS256.

---

### 4.15 tracer.py — Execution Trace Logger

**File**: `backend/app/core/tracer.py` | 3.2KB

`PipelineTracer` records structured traces of node executions to `storage/traces/`. Traces include node name, inputs/outputs summary, duration, status.

---

### 4.16 history_logger.py — History Logger

**File**: `backend/app/core/history_logger.py` | 845 bytes

Appends `history_trace` entries to `PipelineState`. All pipeline nodes call this to maintain a human-readable audit trail inside the state dict, returned to the API caller as part of the analysis result.

---

### 4.17 database.py — Chat Memory and Paper Database

**File**: `backend/app/core/database.py` | 7.6KB

`ChatDatabase` is the high-level facade over the JSON flat-file storage system. Coordinates `StorageEngine`, `ChatRepo`, `PaperRepo`, `EpisodicRepo`, and `ProfileRepo`.

Key operations: `get_paper_by_hash()` (deduplication check on upload), `get_standalone_user_profile()` (loads user settings), `set_active_conversation_id()`.

---

### 4.18 core/db/ — Repository Pattern

**Directory**: `backend/app/core/db/`

| File | Purpose |
|---|---|
| `storage_engine.py` | Thread-safe JSON flat-file engine. `RLock` + atomic `tempfile + os.replace` writes |
| `chat_repo.py` | CRUD for conversations and message history |
| `paper_repo.py` | CRUD for paper metadata (hash, filename, title, conversation_id) |
| `episodic_repo.py` | CRUD for episodic memory (injected into chat prompts) |
| `profile_repo.py` | CRUD for user profile (API keys, Ollama link, hardware preferences) |

`StorageEngine` is the lowest layer: all reads thread-safe, all writes crash-safe (temp file → atomic rename using `os.replace`).

---

### 4.19 core/sandbox/ — Code Execution Sandbox

**Directory**: `backend/app/core/sandbox/`

| File | Purpose |
|---|---|
| `base.py` | Abstract `CodeExecutor` base class. Defines `ExecutionLimits` (timeout, memory, CPU) and `ExecutionResult` |
| `policies.py` | `SandboxPolicy` — defines allowed/blocked syscalls, network access, filesystem paths |
| `subprocess_runner.py` | **Primary sandbox**: Isolated OS subprocess, strict resource limits, stripped environment, blocked network sockets |

`subprocess_runner.py` harness logic:
1. Writes generated code to temp dir as `candidate_model.py`
2. Injects `HARNESS_TEMPLATE` that limits PyTorch threads to 1, monkey-patches `socket.*` to block network access, dynamically imports the candidate module, and executes 6 dynamic rungs (init > forward > loss > backward > optimizer step > tiny loop)
3. Runs harness in subprocess with timeout enforcement
4. Parses JSON result from subprocess stdout
5. Cleans up temp dir regardless of outcome

---

## 5. Graph Layer

**Directory**: `backend/app/graph/`

---

### 5.1 state.py — Pipeline State Definition

**File**: `backend/app/graph/state.py` | 35 lines

`PipelineState` (`TypedDict`) is the shared mutable state flowing through every LangGraph node.

Key fields: `job_id`, `pdf_path`, `paper_id`, `constraints`, `model_name`, `raw_sections`, `metadata`, `paper_doc`, `component_graph`, `extracted_parameters`, `feasibility_report`, `feasibility_loop_count`, `max_feasibility_retries`, `build_sequence`, `specification`, `generate_code_requested`, `generated_code`, `verification_result`, `code_repair_loop_count`, `max_repair_retries`, `report`, `history_trace`, `execution_bounds`, `status`.

---

### 5.2 workflow.py — LangGraph Pipeline Builder

**File**: `backend/app/graph/workflow.py` | 177 lines

Defines and compiles the complete LangGraph V2 StateGraph.

**Pipeline topology**:
```
START
  > ingestion_node       (PDF parse, chunk, embed, KG build)
  > extraction_node      (LLM parameter extraction with evidence quotes)
  > feasibility_node     (Hardware constraint check)
  [CONDITIONAL]
  ├─ FEASIBLE           → sequencing_node
  └─ INFEASIBLE+retries → adaptation_node → feasibility_node (loop ≤ 2)
  > sequencing_node      (DAG topological sort)
  > specification_node   (Architecture specification per component)
  > code_generation_node (Dual-engine code synthesis)
  > evaluation_node      (12-rung verification)
  [CONDITIONAL]
  ├─ PASSED             → END
  └─ FAILED+retries     → code_repair_node → evaluation_node (loop ≤ 2)
  > END
```

`wrap_node_with_telemetry()` — higher-order function wrapping every node: emits `node_start` before, `node_complete` after, and domain-specific events for adaptation/repair/error.

`route_feasibility()` and `route_evaluation()` — conditional routers enforcing bounded loop exit (never infinite).

`app_workflow = build_pipeline_workflow()` — compiled workflow singleton imported by the pipeline API endpoint.

---

### 5.3 graph/nodes/ — Pipeline Node Implementations

**Directory**: `backend/app/graph/nodes/`

| File | Node | What it does |
|---|---|---|
| `ingestion.py` | `ingestion_node` | Parses PDF, chunks text, generates embeddings, builds KG. SHA-256 cache check to skip re-ingestion |
| `extraction.py` | `parameter_extraction_node` | Calls `ParameterAgent` to extract hyperparameters with evidence quotes |
| `feasibility.py` | `feasibility_node` | Calls `FeasibilityAgent` to check GPU VRAM / RAM / CPU feasibility |
| `adaptation.py` | `parameter_adaptation_node` | Reduces batch size, enables gradient checkpointing, etc. to fit hardware |
| `sequencing.py` | `sequencing_node` | Calls `SequencingAgent` + `DAGValidator` to produce valid build order |
| `specification.py` | `specification_node` | Calls `SpecificationAgent` for per-component architecture contracts |
| `code_generation.py` | `code_generation_node` | Calls `CodeGenAgent` with `DualCodeEngine` tournament |
| `evaluation.py` | `evaluation_node` | Runs `CodeVerifier` 12-rung ladder on generated code |
| `repair.py` | `code_repair_node` | Re-prompts `CodeGenAgent` with Reflexion repair prompt using verification errors |
| `verification.py` | `verification_node` | Utility: runs verification on a code block; used by evaluation and repair nodes |

---

## 6. Agents

**Directory**: `backend/app/agents/`

---

### 6.1 ingestion_agent.py

**File**: `backend/app/agents/ingestion_agent.py` | 12.6KB

Orchestrates the full PDF ingestion pipeline: calls `parse_pdf_document()` (multi-parser consensus), chunks extracted text, generates embeddings via `generate_local_embedding()`, inserts into `PaperVectorDB`, builds `PaperKnowledgeGraph`, saves canonical JSON to `storage/extracted_json/`.

---

### 6.2 parameter_agent.py — Parameter Extraction Agent

**File**: `backend/app/agents/parameter_agent.py` | 8.8KB

Uses an LLM to extract structured experimental parameters. Each parameter carries `value`, `evidence_quote` (exact paper quote, strict provenance enforcement), `source_section`, and `status` (`EXPLICIT` / `INFERRED` / `DEFAULT`). Returns `ExtractedParameters` Pydantic model.

---

### 6.3 feasibility_agent.py

**File**: `backend/app/agents/feasibility_agent.py` | 5.2KB

Checks whether extracted parameters (model size, batch size, precision) can run on available hardware using LLM reasoning + hardware probe data. Returns `FeasibilityReport` with per-parameter verdicts and `overall_status`.

---

### 6.4 decomposition_agent.py

**File**: `backend/app/agents/decomposition_agent.py` | 8.0KB

Decomposes the ML system into logical components (e.g., `DataLoader`, `Encoder`, `Decoder`, `TrainingLoop`, `Optimizer`). Returns `ComponentGraph` dict.

---

### 6.5 sequencing_agent.py

**File**: `backend/app/agents/sequencing_agent.py` | 7.6KB

Produces a component build sequence. Integrates `DAGValidator` to ensure no circular dependencies. Returns `BuildSequence` with topologically-sorted component order.

---

### 6.6 specification_agent.py

**File**: `backend/app/agents/specification_agent.py` | 4.4KB

Generates architecture specifications per component (interface contract: inputs, outputs, hyperparameters, dependencies). Provides context for code generation.

---

### 6.7 gap_agent.py

**File**: `backend/app/agents/gap_agent.py` | 6.7KB

Identifies research gaps, ambiguities, and underspecified values. Flags `DEFAULT` or `INFERRED` parameters as potential reproducibility risks.

---

### 6.8 code_gen_agent.py — Code Generation Agent

**File**: `backend/app/agents/code_gen_agent.py` | 20.9KB

Orchestrates the `DualCodeEngine` tournament and post-processing:

1. Builds code-gen prompt from extracted parameters + architecture spec + paper sections
2. Runs `DualCodeEngine` — parallel Gemini + HuggingFace synthesis
3. Scores both candidates on AST validity, paper grounding, and cross-file import consistency
4. Selects winner by highest composite score
5. Reflexion repair if verification fails
6. Returns `generated_code`: `{filename: code_string}` for all pipeline files

`validate_cross_file_imports()` — whole-codebase AST scan verifying `train.py`/`evaluate.py` only import symbols actually defined in `models/*.py`.

---

### 6.9 chat_agent.py — Conversational RAG Agent

**File**: `backend/app/agents/chat_agent.py` | 25.6KB

`ChatAgent` is a multi-turn **ReACT (Reason + Act)** conversational agent.

- Multi-turn loop: think → select tool → call tool → observe → reason again → answer
- Integrates with all `backend/app/tools/` implementations
- Detects code requests and routes to `DualCodeEngine` for inline code synthesis
- Maintains conversation history via `ChatDatabase`
- Builds rich context prompts: user facts + episodic memory + chat history + tool results

**Sub-modules** in `agents/chat/`: `react_utils.py` (ReACT trace parsing, code detection), `smart_titler.py` (auto-generates conversation titles), `context_builder.py` (assembles full context prompt).

---

### 6.10 report_agent.py

**File**: `backend/app/agents/report_agent.py` | 4.9KB

Generates a final analysis report from all pipeline stages. Saves to `storage/reports/`.

---

## 7. Extraction Layer

**Directory**: `backend/app/extraction/`

Implements a **multi-parser consensus system** — four PDF parsers contribute results, merged into one high-quality canonical document.

---

### 7.1 pdf_parser.py — Parser Entry Point

**File**: `backend/app/extraction/pdf_parser.py` | 922 bytes

Thin entry point. Calls `ExtractionRouter` to select and orchestrate parsers based on `EXTRACTION_PROVIDER` env var. Returns `PaperDocument`.

---

### 7.2 router.py — Extraction Router

**File**: `backend/app/extraction/router.py` | 6.7KB

`ExtractionRouter` decides which parsers to use: GROBID (if server at `localhost:8070`), Docling (visual layout), PyMuPDF (always runs as fallback), Gemini (if API key configured). Then calls `PaperMerger` to combine all results.

---

### 7.3 merger.py — Consensus Document Merger

**File**: `backend/app/extraction/merger.py` | 18.8KB

`PaperMerger` takes outputs from up to 4 parsers and produces one `PaperDocument`.

**Consensus strategies**:
- **Tables**: Normalizes captions to `table_N` keys; unions unique tables from all parsers
- **Figures**: Same consensus approach for figure captions
- **Sections**: Longest/most complete text wins
- **Metadata**: GROBID (most accurate) → Gemini → PyMuPDF fallback
- **Equations/Algorithms/References**: Full union, deduplicated

---

### 7.4 docling_parser.py

**File**: `backend/app/extraction/docling_parser.py` | 3.7KB

IBM Docling library. Specializes in visual layout: multi-column detection, table structure, figure boundary detection.

### 7.5 pymupdf_parser.py

**File**: `backend/app/extraction/pymupdf_parser.py` | 7.6KB

PyMuPDF (fitz). Reliable text-layer extraction, page-by-page processing, font/size heuristics for section detection. Primary fallback — always available.

### 7.6 grobid_parser.py

**File**: `backend/app/extraction/grobid_parser.py` | 6.7KB

GROBID server (REST API). TEI XML parsing. Best for: authors, affiliations, references, DOIs, section headers.

### 7.7 grobid_client.py

**File**: `backend/app/extraction/grobid_client.py` | 1.9KB

Minimal HTTP client. Posts PDF binary, returns TEI XML string.

### 7.8 openrouter_parser.py — Gemini Parser

**File**: `backend/app/extraction/openrouter_parser.py` | 10.3KB

Gemini (via OpenRouter or direct API). Deep semantic extraction. Sends PDF as base64-encoded content. Best for math notation and experimental setup descriptions.

### 7.9 section_detector.py

**File**: `backend/app/extraction/section_detector.py` | 8.5KB

Heuristic section boundary detection. Uses font size ratios, bold patterns, Roman/Arabic numeral prefixes, and known academic heading patterns (`Abstract`, `Introduction`, `Method`, `Experiments`, `Conclusion`).

### 7.10 block_extractor.py

**File**: `backend/app/extraction/block_extractor.py` | 3.6KB

Extracts structural blocks (equations, algorithm boxes, table blocks) from raw text using regex patterns.

### 7.11 validator.py — Extraction Quality Validator

**File**: `backend/app/extraction/validator.py` | 11.8KB

`validate_paper_document()` runs deterministic quality checks on a `PaperDocument`, returning `ExtractionQualityReport`. Checks: title present, abstract ≥ 100 chars, ≥ 3 sections, each section content > 50 chars, at least 1 table or figure, at least 1 reference, no duplicate section IDs. Each check = `ValidationMetric` with `SUCCESS / WARNING / ERROR`.

### 7.12 pdf_inspector.py

**File**: `backend/app/extraction/pdf_inspector.py` | 2.7KB

Pre-flight check before parsing. Validates: file exists, valid PDF signature (`%PDF-`), file size within limits (not empty, not >200MB), page count sane.

### 7.13 constants.py

**File**: `backend/app/extraction/constants.py` | 2.1KB

Known academic section heading patterns, parser priority order, minimum quality thresholds.

---

## 8. Retrieval Layer

**Directory**: `backend/app/retrieval/`

---

### 8.1 chunker.py — Text Chunker

**File**: `backend/app/retrieval/chunker.py` | 2.0KB

`chunk_paper_document()` splits `PaperDocument` into fixed-size overlapping text chunks. Default: 500 chars, 50-char overlap. Each `PaperChunk`: `chunk_id`, `content`, `section_id`, `paper_id`, `page_number`.

---

### 8.2 embeddings.py — Embedding Generator

**File**: `backend/app/retrieval/embeddings.py` | 3.5KB

`generate_local_embedding()` calls Ollama API to generate vector embeddings using `nomic-embed-text` (768 dimensions). Includes **chunk-level embedding cache**: SHA-256(chunk text) → cached vector to avoid re-embedding identical chunks.

---

### 8.3 vector_db.py — Vector Database

**File**: `backend/app/retrieval/vector_db.py` | 13.4KB

`PaperVectorDB` — a **local-first, per-paper** vector database using flat-file JSON + NumPy cosine similarity.

- Each paper = own JSON file at `storage/rag_embeddings/{paper_id}.json`
- **Strict per-paper isolation** — paper A queries cannot return paper B results
- Chunk deduplication at write time via SHA-256 content hashing
- Cosine similarity computed in NumPy — no external vector database required

**Retrieval modes**: `semantic_search()` (pure cosine similarity), `hybrid_search()` (BM25 keyword score + cosine similarity via Reciprocal Rank Fusion).

`retrieve_context()` — primary RAG query function: query string → embedding → hybrid search → top-K chunks.

---

### 8.4 knowledge_graph.py — 7-Level Knowledge Graph

**File**: `backend/app/retrieval/knowledge_graph.py` | 27.4KB

`PaperKnowledgeGraph` — NetworkX directed graph implementing the **Phase 15 upgraded 7-layer hierarchy**.

**7-Level Hierarchy**:

| Level | Tier | Color | What it represents |
|---|---|---|---|
| 1 | Paper | #F59E0B | Root document node |
| 2 | Section | #6B7280 | Major paper sections |
| 3 | Concept | #8B5CF6 | Abstract ML concepts (attention, normalization) |
| 4 | Component | #3B82F6 | Concrete modules (Transformer, DataLoader) |
| 5 | Parameter | #10B981 | Hyperparameters (lr=0.001, batch_size=32) |
| 6 | Dependency | #F97316 | Library/framework dependencies (PyTorch, CUDA) |
| 7 | Implementation | #EC4899 | Generated code file mappings |

**5 Core Capabilities**:

| Capability | Method | Description |
|---|---|---|
| Dependency Reasoning | `get_dependency_order()` | Topological sort for safe build ordering |
| Evidence Tracing | `trace_evidence()` | Traces any node back to source paper section and quote |
| Architecture Visualization | `get_visualization_data()` | Tier-colored node/edge data for React Flow / D3 |
| Consistency Checking | `validate_consistency()` | Detects orphans, missing parents, ungrounded parameters |
| Component Relationships | `get_component_relationships()` | Bidirectional traversal + shortest-path queries |

Persisted as `storage/knowledge_graphs/{paper_id}_graph.json` using `nx.node_link_data()`. Auto-built from canonical extracted JSON on first access.

---

## 9. Tools

**Directory**: `backend/app/tools/`

Tools are callable units available to the `ChatAgent`'s ReACT loop. `get_all_tools()` in `__init__.py` instantiates and returns all tools.

| File | Tool | What it does |
|---|---|---|
| `vector_search_tool.py` | `VectorSearchTool` | Hybrid RAG retrieval against the current paper's vector DB |
| `graph_search_tool.py` | `GraphSearchTool` | Queries 7-tier KG (dependency order, evidence trace, visualization, consistency, relationships) |
| `canonical_document_tool.py` | `CanonicalDocumentTool` | Reads extracted JSON sections, tables, figures, equations |
| `hyperparameter_tool.py` | `HyperparameterTool` | Returns extracted hyperparameters for the current paper |
| `episodic_memory_tool.py` | `EpisodicMemoryTool` | Reads/writes short-term episodic memory for multi-session context |
| `arxiv_search_tool.py` | `ArxivSearchTool` | Searches ArXiv API for related papers |
| `scholar_search_tool.py` | `ScholarSearchTool` | Searches Google Scholar (via Tavily) for citations |
| `base_tool.py` | `BaseTool` | Abstract base class: `name`, `description`, `run(input)` interface |

---

## 10. API Layer

**Directory**: `backend/app/api/`

---

### 10.1 api/v1/api_router.py — Router Aggregator

**File**: `backend/app/api/v1/api_router.py` | 606 bytes

Mounts all endpoint routers under `/api/v1/`:

| Prefix | File | Responsibility |
|---|---|---|
| `/papers` | `papers.py` | PDF upload, metadata, RAG, KG queries |
| `/pipeline` | `pipeline.py` | Analysis job trigger, status, SSE stream |
| `/chat` | `chat.py` | Conversational agent endpoints |
| `/models` | `models.py` | Model listing and selection |
| `/auth` | `auth.py` | JWT authentication |
| `/hardware` | `hardware.py` | Hardware probe and GPU status |
| `/telemetry` | `telemetry.py` | Analytics collection endpoint |

---

### 10.2 endpoints/papers.py — Paper Management

**File**: `backend/app/api/v1/endpoints/papers.py` | 25.0KB

| Endpoint | Method | Description |
|---|---|---|
| `/papers/upload` | POST | Upload PDF: parse, chunk, embed, index RAG + KG. MD5 deduplication check |
| `/papers/{paper_id}` | GET | Return canonical document JSON |
| `/papers/{paper_id}/sections` | GET | Return extracted sections |
| `/papers/{paper_id}/rag/query` | POST | Run RAG retrieval query against paper |
| `/papers/{paper_id}/knowledge-graph` | GET | Return full KG visualization data |
| `/papers/{paper_id}/knowledge-graph/validate` | GET | Run KG consistency validation |
| `/papers/{paper_id}/knowledge-graph/trace/{entity}` | GET | Trace entity evidence back to paper source |
| `/papers/{paper_id}/download` | GET | Download original PDF file |

---

### 10.3 endpoints/pipeline.py — Analysis Pipeline

**File**: `backend/app/api/v1/endpoints/pipeline.py` | 15.3KB

| Endpoint | Method | Description |
|---|---|---|
| `/pipeline/analyze` | POST | Starts full analysis job in background thread. Returns `job_id` |
| `/pipeline/jobs/{job_id}` | GET | Current job status and progress |
| `/pipeline/jobs/{job_id}/cancel` | DELETE | Cancels an active job |
| `/pipeline/jobs/{job_id}/events` | GET (SSE) | Server-Sent Events stream of real-time node events |
| `/pipeline/jobs/{job_id}/manifest` | GET | Returns the reproducibility run manifest |

The `analyze` endpoint: creates `JobStore` record → launches `app_workflow.invoke()` in `threading.Thread` → returns immediately with `job_id`. The SSE endpoint polls `job_store.get_events(since_id)` to stream new events.

---

### 10.4 endpoints/chat.py

**File**: `backend/app/api/v1/endpoints/chat.py` | 7.5KB

`POST /chat/message` — user message → agent response + tool traces.
`GET /chat/conversations` — list conversation history.
`POST /chat/conversations` — create new conversation.
`DELETE /chat/conversations/{id}` — delete conversation.

### 10.5 endpoints/models.py

**File**: `backend/app/api/v1/endpoints/models.py` | 10.6KB

`GET /models/available` — all configured cloud + local Ollama models.
`POST /models/select` — persist user's model choice to `user_profile.json`.
`GET /models/status` — per-provider quota status.

### 10.6 endpoints/auth.py

**File**: `backend/app/api/v1/endpoints/auth.py` | 3.4KB

JWT-based auth. `POST /auth/login` returns JWT token. Protected endpoints use `Depends(get_current_user)`.

### 10.7 endpoints/hardware.py

**File**: `backend/app/api/v1/endpoints/hardware.py` | 3.4KB

`GET /hardware/info` — CPU, RAM, CUDA GPU info via `psutil` + `torch.cuda`. Used by frontend and feasibility agent.

---

## 11. Schemas

**Directory**: `backend/app/schemas/`

| File | Key Models |
|---|---|
| `canonical_paper.py` | `PaperDocument`, `Section`, `Table`, `Figure`, `Equation`, `Algorithm`, `Reference`, `PageInfo`, `Provenance`, `ExtractionQualityReport`, `ValidationMetric` |
| `pipeline.py` | `ExtractedParameters`, `Parameter`, `FeasibilityReport`, `BuildSequence`, `ComponentGraph` |
| `pipeline_schemas.py` | `PaperMetadata`, `SectionInfo` — lightweight versions for pipeline state |
| `paper.py` | `PaperMetadata`, `PaperDocument` — used in retrieval layer |
| `rag_schemas.py` | `RAGQuery`, `RAGResult` — RAG endpoint request/response |
| `verification.py` | `CodeVerificationReport`, `VerificationRung`, `RungResult`, `CodeLifecycleState` |
| `chat.py` | `ChatMessage`, `ChatConversation`, `ChatResponse` |

`canonical_paper.py: PaperDocument` — the **central data model** of the entire system. Every parser, merger, agent, and API route ultimately reads from or produces this schema.

---

## 12. Providers

**Directory**: `backend/app/providers/`

Thin HTTP adapter layer. Each adapter exposes `complete(prompt, api_key, model_id) -> dict` returning `{"success": bool, "content": str, "error": str}`.

| File | Provider | Models |
|---|---|---|
| `groq_adapter.py` | Groq Cloud LPU | llama-3.3-70b-versatile, qwen-2.5-coder-32b, deepseek-r1 |
| `openrouter_adapter.py` | OpenRouter | gemini-2.5-flash:free, deepseek-r1:free |
| `hf_adapter.py` | HuggingFace Inference | Qwen2.5-Coder-32B-Instruct |
| `ollama_adapter.py` | Ollama (local) | Any locally installed model |

`groq_adapter.py` also implements `get_available_models()` for model discovery. `ollama_adapter.py` discovers models from the Ollama server at runtime.

---

## 13. Evaluation

**Directory**: `backend/app/evals/`

---

### 13.1 rag_eval.py — RAG Evaluation Framework

**File**: `backend/app/evals/rag_eval.py` | 23.4KB

Empirical, auditable RAG benchmarks (not mock scores).

| Metric | Description |
|---|---|
| Precision@K | Fraction of top-K retrieved chunks that are relevant |
| Recall@K | Fraction of all relevant chunks in top-K |
| Hit Rate@K | At least 1 relevant chunk in top-K |
| MRR | Mean Reciprocal Rank of first relevant result |
| NDCG@K | Normalized Discounted Cumulative Gain |
| Context Precision | Retrieved chunks relevant to the question |
| Context Recall | Relevant info covered by retrieved chunks |
| Faithfulness | LLM-verified: answer stays grounded in retrieved context |
| Answer Relevance | LLM-verified: answer addresses the question |
| Citation Accuracy | Answer cites correct paper sections |

Faithfulness and Answer Relevance use Ollama local inference as evaluator (avoids cloud costs).

### 13.2 eval_suite.py

**File**: `backend/app/evals/eval_suite.py` | 5.6KB

Orchestrates full evaluation runs. Loads benchmark queries from JSON, runs RAG eval on each, aggregates metrics, produces structured report.

### 13.3 evals/benchmarks/

Contains saved benchmark datasets and evaluation results for regression tracking.

---

## 14. Tests

**Directory**: `backend/tests/` — 33 test files covering every system dimension.

| Category | Key Files |
|---|---|
| Unit | `test_dag_validation.py`, `test_section_detector.py`, `test_merger.py`, `test_model_router.py` |
| Integration | `test_database.py`, `test_job_lifecycle.py`, `test_ingestion_agent.py` |
| System | `test_langgraph_v2.py`, `test_api_endpoints.py`, `test_chat_agent.py` |
| Agent | `test_code_gen_agent.py`, `test_dual_code_engine.py` |
| RAG | `test_rag_isolation.py`, `test_provenance_extraction.py` |
| Semantic Assertions | `test_v2_semantic_assertions.py` |
| Failure Injection | `test_phase12_reliability.py`, `test_v2_failure_injection.py` |
| Malformed Input | `test_v2_malformed_inputs.py` |
| Concurrency | `test_v2_concurrency.py`, `test_concurrency_performance.py` |
| Bounded Loops | `test_v2_bounded_loops.py` |
| Security | `test_sandbox_security.py` |
| Reproducibility | `test_run_manifest.py` |
| Observability | `test_event_observability.py` |
| Cost | `test_cost_optimization.py` |
| Knowledge Graph | `test_knowledge_graph.py` |
| Evaluation | `test_v2_eval_regression.py` |
| Verification | `test_verification_ladder.py` |
| E2E | `end_to_end_backend_testing.ipynb` |

**Testing philosophy**: Prefer semantic assertions over HTTP status codes:
```python
# Preferred
assert result.optimizer.status == "EXPLICIT"
assert result.optimizer.value == "0.001"

# Avoided
assert response.status_code == 200
```

---

## 15. Storage Layout

All runtime data is isolated in `backend/storage/` (git-ignored).

```
backend/storage/
├── jobs.db                   ← SQLite WAL: jobs + job_events tables
├── papers/                   ← {paper_id}.pdf — uploaded PDFs
├── extracted_json/           ← {paper_id}.json — canonical PaperDocument
├── rag_embeddings/           ← {paper_id}.json — chunks + vectors + metadata
├── knowledge_graphs/         ← {paper_id}_graph.json — NetworkX node_link_data
├── manifests/                ← {run_id}.json — run reproducibility manifests
├── codes/                    ← {paper_id}_code.zip — generated code archives
├── conversations/            ← {conversation_id}.json — chat sessions
├── history/
│   ├── chat_memory_db.json   ← Master index: users, papers, episodic runs
│   └── model_quotas.json     ← Provider quota state
├── reports/                  ← {paper_id}_report.json — analysis reports
├── traces/                   ← {job_id}_trace.json — execution traces
└── paper_cache/              ← {paper_hash}.json — SHA-256 ingestion cache
```

---

## 16. End-to-End Data Flow

```
User uploads PDF
      |
      v
POST /api/v1/papers/upload
  |- MD5 dedup check → if duplicate, return existing paper_id
  |- save PDF to backend/storage/papers/{paper_id}.pdf
  |- parse_pdf_document()     → PaperDocument (4-parser consensus)
  |- chunk_paper_document()   → [PaperChunk x N]
  |- generate_local_embedding() x N → [vector x N]
  |- PaperVectorDB.insert()   → storage/rag_embeddings/{paper_id}.json
  └- PaperKnowledgeGraph()    → storage/knowledge_graphs/{paper_id}_graph.json

      |
      v
POST /api/v1/pipeline/analyze
  |- JobStore.create_job(paper_id) → job_id
  |- thread.start(app_workflow.invoke(initial_state))
  └- return {job_id, status: "queued"}

      | (background thread)
      v
LangGraph Workflow:

  ingestion_node
    |- SHA-256 cache check → skip if paper already processed
    |- IngestionAgent.run() → PaperDocument → state
    └- emit events → job_events table

  extraction_node
    |- ParameterAgent.extract() → ExtractedParameters with evidence_quotes
    └- emit events

  feasibility_node
    |- FeasibilityAgent.check() → FeasibilityReport
    [CONDITIONAL]
    |- FEASIBLE           → sequencing_node
    └- INFEASIBLE+retries → adaptation_node (loop ≤ 2)

  adaptation_node (if triggered)
    |- Reduce batch_size, enable grad_checkpoint, lower precision
    └- → feasibility_node (re-evaluate)

  sequencing_node
    |- SequencingAgent.plan() + DAGValidator.validate()
    └- → specification_node

  specification_node
    |- SpecificationAgent.specify() per component
    └- → code_generation_node

  code_generation_node
    |- DualCodeEngine: Gemini + HuggingFace in parallel (asyncio)
    |- AST-validate and security-check both candidates
    |- Score: paper grounding + cross-file import correctness
    └- Tournament winner → generated_code dict

  evaluation_node
    |- CodeVerifier.verify_all_rungs() — 12-rung ladder
    |   |- Rungs 1-4: Static (AST, security, imports, compile)
    |   └- Rungs 5-12: Dynamic (subprocess sandbox + paper fidelity)
    [CONDITIONAL]
    |- PASSED → END
    └- FAILED+retries → code_repair_node (loop ≤ 2)

  code_repair_node (if triggered)
    |- CodeGenAgent.repair(errors) — Reflexion prompt with verification errors
    └- → evaluation_node (re-verify)

  END
    |- generate_run_manifest()  → storage/manifests/{run_id}.json
    |- JobStore.complete_job()  → status=COMPLETED, progress=100.0
    └- emit pipeline_completed event

      |
      v
Frontend polls GET /api/v1/pipeline/jobs/{job_id}/events (SSE)
  └- Streams ordered events in real-time as each node executes
```

---

*Document generated: October 2026 | Backend Version: 2.0.0 | Architecture: LangGraph V2 + FastAPI*
