# RUEXIS AI Platform V2 — Current Architecture Reference

> **Document Type:** V2 Live Architecture  
> **Version:** `2.0.0` (from `backend/app/core/config.py`)  
> **Source of Truth:** Active source code in `backend/app/`  
> **Last Updated:** 2026-10-03

---

## 1. REST API Surface (`app/api/v1/endpoints/`)

Prefix for all routes: `/api/v1`

### Auth (`auth.py`)

| Method | Route | Description |
|---|---|---|
| `POST` | `/auth/local-login` | Developer local auth (no password, just username + email) |
| `GET` | `/auth/check-ollama` | Checks if local Ollama instance is reachable |
| `POST` | `/auth/verify-key` | Validates a cloud API key (Gemini / OpenAI / Groq etc.) |
| `POST` | `/auth/setup-wizard` | Saves full onboarding wizard profile (API keys, Ollama, avatar) |
| `POST` | `/auth/reset-session` | Resets the session to re-trigger onboarding wizard |
| `GET` | `/profile`, `/user/profile` | Returns user profile from `storage/user_profile.json` |
| `PUT` | `/profile`, `/user/profile` | Updates user profile |
| `POST` | `/user/profile` | Creates or updates user profile |

### Papers (`papers.py`)

| Method | Route | Description |
|---|---|---|
| `POST` | `/upload`, `/papers/upload`, `/papers`, `/history/upload` | Multipart PDF/DOCX upload, triggers async extraction pipeline |
| `GET` | `/papers` | Lists all uploaded papers with metadata, scores, and status |
| `DELETE` | `/papers/{paper_id}` | Deletes paper PDF, JSON, vectors, and knowledge graph |
| `GET` | `/papers/{paper_id}`, `/history/{paper_id}` | Retrieves full extracted canonical paper JSON |
| `GET` | `/papers/{paper_id}/pdf` | Serves the raw PDF binary for in-browser viewing |
| `GET` | `/papers/{paper_id}/report`, `/papers/{paper_id}/markdown` | Returns synthesized Markdown blueprint report |
| `GET` | `/papers/{paper_id}/codebase` | Returns full generated multi-file codebase (ZIP or dict) |
| `POST` | `/papers/{paper_id}/synthesize`, `/history/{paper_id}/generate_code` | Triggers standalone code synthesis for a completed paper |
| `GET` | `/papers/{paper_id}/task`, `/history/{paper_id}/task` | Returns task checklist for paper implementation |
| `GET` | `/papers/{paper_id}/walkthrough`, `/history/{paper_id}/walkthrough` | Returns verification walkthrough Markdown |
| `GET` | `/papers/{paper_id}/knowledge_graph` (+ aliases) | Returns entity-relation graph as node-link JSON |
| `GET` | `/papers/{paper_id}/knowledge_graph/validate` | Runs KG consistency checks and returns validation report |
| `GET` | `/papers/{paper_id}/knowledge_graph/trace/{entity_name}` | Returns entity lineage and dependency trace |
| `GET` | `/papers/{paper_id}/manifest` | Returns run execution manifest for a completed job |
| `GET` | `/papers/quota`, `/quota` | Returns per-provider daily quota consumption |

### Pipeline (`pipeline.py`)

| Method | Route | Description |
|---|---|---|
| `GET` | `/pipeline/jobs/{run_id}/events` (+ aliases) | **SSE stream** emitting `node_started`, `node_completed`, `refinement`, `retry`, `pipeline_completed`, `pipeline_failed` |
| `POST` | `/pipeline/analyze`, `/analyze` | Triggers full LangGraph V2 pipeline for an uploaded paper |
| `POST` | `/history/{paper_id}/trigger_analysis` | Legacy alias for triggering analysis |
| `GET` | `/pipeline/jobs/{job_id}` (+ aliases) | Polls SQLite job status: `queued → running → completed / failed` |
| `POST` | `/pipeline/jobs/{job_id}/cancel`, `/analyze/{job_id}/cancel` | Cancels a running pipeline job |
| `POST` | `/papers/{paper_id}/approve_parameters` (+ aliases) | Overwrites extracted hyperparameters with user-approved values |
| `GET` | `/pipeline/jobs/{run_id}/manifest` (+ aliases) | Returns full execution ledger for a completed run |
| `GET` | `/manifest/{run_id}/explain` (+ alias) | Returns human-readable explanation of the manifest |
| `GET` | `/manifests`, `/pipeline/manifests` | Lists all stored run manifests |

### Chat (`chat.py`)

| Method | Route | Description |
|---|---|---|
| `GET` | `/conversations`, `/chat/conversations` | Lists all conversation threads for `user_id` |
| `GET` | `/conversations/active` | Returns the most recently active conversation |
| `POST` | `/conversations/active` | Sets a conversation as active |
| `POST` | `/conversations`, `/chat/conversations` | Creates a new conversation thread |
| `POST` | `/conversations/{id}/chat` | Sends a message; runs ReAct agent loop (sync) |
| `POST` | `/conversations/{id}/chat/stream` | SSE streaming of ReAct agent thoughts and answer |
| `GET` | `/conversations/{id}`, `/conversations/{id}/messages` | Retrieves messages in a thread |
| `PATCH` | `/conversations/{id}` | Renames a conversation thread |
| `DELETE` | `/conversations/{id}` | Deletes a conversation and its history |
| `GET` | `/memory` | Returns user episodic memory facts |
| `POST` | `/memory` | Adds a new user memory fact |

### Models (`models.py`)

| Method | Route | Description |
|---|---|---|
| `GET` | `/models`, `/models/` | Returns available Ollama local models + cloud options |
| `GET` | `/models/limits` | Returns per-provider sliding-window quota consumption |
| `GET` | `/models/dual-engine` | Returns dual-engine candidate metadata |
| `GET` | `/models/status` | Returns active provider health and connectivity status |

### Hardware (`hardware.py`)

| Method | Route | Description |
|---|---|---|
| `GET` | `/hardware/metrics` | Returns live CPU %, RAM %, CUDA VRAM usage, GPU temp (psutil + torch) |

### Telemetry & Evals (`telemetry.py`)

| Method | Route | Description |
|---|---|---|
| `GET` | `/papers/{paper_id}/traces` (+ aliases), `/telemetry/traces` | Returns `AgentTracer` execution step traces |
| `GET` | `/evals/benchmark/{paper_id}` | Returns stored RAG benchmark results for a paper |
| `POST` | `/evals/run-rag`, `/evals/benchmark` | Runs live RAG evaluation (faithfulness, hallucination) |
| `GET` | `/evals/baseline` | Returns evaluation baseline summary |

---

## 2. LangGraph V2 Topology (`app/graph/`)

### State Definition (`app/graph/state.py`)

```python
class PipelineState(TypedDict, total=False):
    job_id: str
    pdf_path: str
    paper_id: str
    constraints: dict
    model_name: str
    loop_count: int
    raw_sections: dict
    metadata: PaperMetadata
    paper_doc: PaperDocument
    component_graph: dict
    extracted_parameters: ExtractedParameters
    feasibility_report: FeasibilityReport
    feasibility_loop_count: int
    max_feasibility_retries: int        # default = 2
    build_sequence: BuildSequence
    specification: dict
    generate_code_requested: bool
    sample_code: str
    generated_code: Dict[str, str]
    verification_result: dict
    code_repair_loop_count: int
    max_repair_retries: int              # default = 2
    parameters_approved: bool
    report: dict
    history_trace: List[dict]
    execution_bounds: dict
    status: str
```

### Graph Topology (`app/graph/workflow.py`)

```text
[START]
   ↓
[ingestion_node]         ← Extraction pipeline (PDF parse, VLM, chunking, embedding, KG)
   ↓
[extraction_node]        ← Parameter extraction with 5-tier provenance
   ↓
[feasibility_node]       ← Hardware feasibility assessment (VRAM, batch size etc.)
   ↓ (conditional: route_feasibility)
   ├─ FEASIBLE ──────────────────────────────────────────────→ [sequencing_node]
   ├─ NOT FEASIBLE, retries < max_feasibility_retries=2 ──→ [adaptation_node]
   │      ↓ (adaptation_node loops back to feasibility_node)
   └─ NOT FEASIBLE, retries exhausted ───────────────────→ [sequencing_node]
   
[sequencing_node]        ← DAG build sequence with validated topological sort
   ↓
[specification_node]     ← Modular architecture specification synthesis
   ↓
[code_generation_node]   ← Dual-engine PyTorch code synthesis (Gemini + HF Qwen Coder)
   ↓
[evaluation_node]        ← 3-layer verification (AST, grounding score, subprocess forward pass)
   ↓ (conditional: route_evaluation)
   ├─ PASSED ─────────────────────────────────────────→ [END]
   ├─ FAILED, repairs < max_repair_retries=2 ─────→ [code_repair_node]
   │      ↓ (repair loops back to evaluation_node)
   └─ FAILED, repairs exhausted ──────────────────→ [END]
```

- **Cycles:** 2 bounded self-correcting loops (feasibility + code repair)
- **Conditional Routing:** 2 conditional edges (`route_feasibility`, `route_evaluation`)
- **Max iterations:** Feasibility ≤ 2, Code repair ≤ 2
- **All nodes:** Wrapped with `wrap_node_with_telemetry()` emitting real SSE events

---

## 3. Extraction Pipeline (`app/extraction/`)

```text
[PDF / DOCX Upload]
   ↓
[pdf_parser.py → parse_pdf_document()]
   ↓
[router.py → route_and_extract()]

  Phase 1: pdf_inspector.py
    - Validate PDF integrity, detect scanned ratio, generate paper_id slug

  Phase 2A (scanned PDF): docling_parser.py
    - OCR route via Docling for image-only pages → early return

  Phase 3 (native text PDF): block_extractor.py + section_detector.py
    - Deterministic PyMuPDF text extraction: 0 API tokens
    - Produces: blocks, sections, raw_full_text

  Phase 4: element_cropper.py
    - Detect & crop figures, tables, equations for VLM processing

  Phase 5A (quota available): vlm_processor.py
    - Gemini VLM targeted calls (up to 6 figures, 6 tables, 8 equations)
    - Self-healing: re-crop at 250 DPI + 1 retry on malformed output

  Phase 5B (quota exhausted): Skip VLM, text-only fallback

  Phase 6: merger.py → merge_extractions()
    - Merge text extraction + VLM analysis → Canonical PaperDocument
   ↓
[Canonical PaperDocument]
   ↓
  ├─ chunker.py → All chunks indexed (no artificial [:5] slicing)
  │      ↓
  │  vector_db.py → RAG embeddings stored in storage/rag_embeddings/{paper_id}.json
  │                  (strict paper_id isolation, SHA-256 deduplication)
  ↓
  └─ knowledge_graph.py → 7-tier entity-relation graph
         ↓
     storage/knowledge_graphs/{paper_id}.json
```

---

## 4. Code Generation & Verification (`app/core/`)

```text
[Extracted Parameters + Component Graph]
   ↓
[dual_code_engine.py → generate_dual_candidates_sync()]
   ├── Candidate A: Google Gemini Flash API (httpx.AsyncClient)
   └── Candidate B: Hugging Face Qwen 2.5 Coder 32B API
   ↓
[code_verifier.py → 12-Rung Verification Ladder]
   ├── Layer 1 (AST/Security): ast.parse + SecurityPolicy (blocks os, sys, subprocess, eval, exec, open)
   ├── Layer 2 (Grounding): Regex scan for hyperparameter literals & PyTorch/nn symbols
   │     (UNKNOWN/None parameters are filtered out — not penalized, not falsely credited)
   └── Layer 3 (Execution): SubprocessCodeExecutor (isolated subprocess, timeout, no env secrets, no network)
   ↓
[Tournament Winner Selection] (Highest weighted score)
   ↓
[Reflexion Auto-Repair via code_repair_node] (Up to 2 retries via LangGraph loop)
   ↓
[validate_cross_file_imports()] (Scans train.py imports against generated model exports)
```

---

## 5. Storage Layout

```text
backend/
├── storage/
│   ├── papers/                  ← Uploaded raw PDFs
│   ├── rag_embeddings/          ← Per-paper vector JSON (paper_id isolated)
│   ├── conversations/           ← Chat thread JSON files
│   ├── codes/                   ← Generated codebase outputs
│   ├── history/                 ← Legacy history alias
│   ├── user_profile.json        ← Developer profile + API keys
│   └── jobs.db                  ← SQLite persistent job store (WAL mode)
└── reports/
    ├── extracted_json/           ← Canonical PaperDocument JSON per paper
    ├── knowledge_graphs/         ← KG node-link JSON per paper
    ├── manifests/                ← Run execution ledger JSON per job
    ├── traces/                   ← AgentTracer step traces
    ├── benchmarks/               ← RAG eval benchmark results
    ├── evaluation/               ← Evaluation suite outputs
    ├── audit/                    ← Audit & cost optimization reports
    ├── optimization/             ← Cost optimizer outputs
    └── performance/              ← Concurrency & performance test outputs
```

---

## 6. New Core Infrastructure (V2 Additions)

| Module | Location | Description |
|---|---|---|
| `job_store.py` | `app/core/` | SQLite persistent job store (WAL, `recover_stale_jobs()`, cancellation) |
| `events.py` | `app/core/` | SSE event emitters (`emit_node_start`, `emit_node_complete`, `emit_refinement`, etc.) |
| `manifest.py` | `app/core/` | Run execution ledger builder (node timings, outputs, status per step) |
| `dag_validator.py` | `app/core/` | Kahn's algorithm topological sort + 3-color DFS cycle detector |
| `sandbox/` | `app/core/` | `SubprocessCodeExecutor`, `SecurityPolicy` AST scanner, `ExecutionLimits` |
| `cost_optimizer.py` | `app/core/` | Per-provider cost tracking and model selection optimization |
| `quota_tracker.py` | `app/core/` | Sliding-window RPM/TPM quota enforcement per cloud provider |
| `limits_dashboard.py` | `app/core/` | Real-time quota consumption dashboard (HTML + JSON) |
| `element_cropper.py` | `app/extraction/` | Figure/table/equation detection and DPI-scaled crop for VLM |
| `vlm_processor.py` | `app/extraction/` | Gemini VLM targeted element analysis with self-healing retry |
| `semantic_analyzer.py` | `app/extraction/` | Semantic section classification and entity labeling |
