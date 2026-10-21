# V2 Backend Engineering Changelog

All notable changes to the RUEXIS AI Platform backend architecture, pipelines, agents, and execution environments will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-10-03 — V2 GA Release

### Summary
All 6 planned V2 phases are now implemented. The backend has been fully migrated from V1 (linear DAG, in-process exec, in-memory dict state, fake metrics) to V2 (cyclic self-correcting LangGraph, sandboxed subprocess execution, SQLite WAL job store, 5-tier provenance, real-time SSE telemetry, VLM-assisted extraction, and run execution manifests).

### New V2 Infrastructure Added Since Phase 6
- **Run Execution Manifest** (`backend/app/core/manifest.py`):
  - Tracks per-node entry/exit times, status, and outputs for every pipeline run.
  - Exposed via `GET /pipeline/jobs/{run_id}/manifest` and `GET /manifest/{run_id}/explain`.
- **SSE Event System** (`backend/app/core/events.py`):
  - Canonical event emitters: `emit_node_start`, `emit_node_complete`, `emit_refinement`, `emit_retry`, `emit_node_error`.
  - All graph nodes wrapped with `wrap_node_with_telemetry()` in `workflow.py`.
  - Frontend receives real ordered events (not timer-based fake progress).
- **VLM-Assisted Extraction** (`backend/app/extraction/vlm_processor.py`, `element_cropper.py`):
  - Gemini VLM processes figures (≤6), tables (≤6), and equations (≤8) per paper.
  - Quota-gated via `daily_quota_manager.can_use_vlm()`.
  - Self-healing: detects malformed table/equation output, re-crops at 250 DPI, retries once.
- **Cost Optimizer** (`backend/app/core/cost_optimizer.py`):
  - Tracks per-provider API cost, recommends optimal model routing based on budget and quality.
- **Storage Reorganization**:
  - Artifact outputs centralized under `backend/reports/` (extracted_json, knowledge_graphs, manifests, traces, benchmarks, evaluation, audit, optimization, performance).
  - `storage/rag_based/` renamed to `storage/rag_embeddings/`.
- **Extended Test Suite** (35 test files total):
  - Added: `test_event_observability.py`, `test_run_manifest.py`, `test_knowledge_graph.py`, `test_verification_ladder.py`, `test_adaptive_extraction.py`, `test_real_pdf_hardening.py`, `test_cost_optimization.py`, `test_concurrency_performance.py`, `test_v2_concurrency.py`, `test_v2_failure_injection.py`, `test_v2_malformed_inputs.py`, `test_phase12_reliability.py`, `test_v2_eval_regression.py`, `test_v2_semantic_assertions.py`, `test_v2_bounded_loops.py`.
- **Setup Wizard & Auth Improvements** (`backend/app/api/v1/endpoints/auth.py`):
  - `POST /auth/setup-wizard`: full onboarding wizard save (API keys, Ollama config, avatar).
  - `POST /auth/verify-key`: validates cloud API keys before saving.
  - `GET /auth/check-ollama`: connectivity probe for local Ollama instance.
  - `POST /auth/reset-session`: re-triggers onboarding flow.
- **Paper API Extensions** (`backend/app/api/v1/endpoints/papers.py`):
  - `GET /papers/{paper_id}/pdf`: serves raw PDF for in-browser viewing.
  - `GET /papers/{paper_id}/codebase`: returns generated multi-file codebase.
  - `POST /papers/{paper_id}/synthesize`: standalone code synthesis trigger.
  - `GET /papers/{paper_id}/knowledge_graph/validate`: KG consistency check.
  - `GET /papers/{paper_id}/knowledge_graph/trace/{entity}`: entity lineage trace.
- **Knowledge Graph Hardening** (`backend/app/retrieval/knowledge_graph.py`):
  - `validate()` endpoint checks KG referential integrity, isolated entity detection, and tier coverage.
  - `trace()` returns entity dependency lineage path.

---

## [Unreleased] - Remaining Backlog

### Planned
- Full EVAL-01 resolution: replace all remaining hardcoded fallback score paths with Ragas-based faithfulness and context recall computation.
- Docker containerization for SubprocessCodeExecutor (currently OS subprocess only).
- Multi-worker safe job distribution (Redis-backed queue for `uvicorn --workers N`).
- Streaming code generation output (token-by-token SSE during synthesis).


## [0.8.0-phase6] - 2026-09-15

### Added
- **Deterministic Graph / DAG Validator Engine** (`backend/app/core/dag_validator.py`):
  - Created standalone graph validation protocol eliminating LLM authority over execution plan correctness.
  - Implemented Kahn's algorithm for cycle detection with deterministic tie-breaking (lexicographical sorting of ready nodes) to guarantee repeatable execution orders regardless of non-deterministic LLM listing order.
  - Added 3-color DFS cycle tracer (`WHITE`, `GRAY`, `BLACK`) to extract exact directed cycle paths (e.g. `A -> B -> C -> A`) for diagnostic reporting.
  - Implemented structured machine-readable error codes (`DAGErrorCode`):
    - `EMPTY_PLAN`: Zero-step execution plan.
    - `INVALID_NODE_ID`: Empty or illegal component name.
    - `DUPLICATE_NODE`: Multiple steps sharing the same identifier.
    - `MISSING_DEPENDENCY`: Dependency referencing an undefined component.
    - `SELF_DEPENDENCY`: Step declaring dependency on itself.
    - `CYCLE_DETECTED`: Circular dependency detected.
    - `ORPHAN_NODE`: Completely disconnected components in multi-step plans.
  - Added `format_error_feedback()` method to formulate machine-readable diagnostic feedback for bounded agent repair.
- **Sequencing Agent Bounded Repair Loop** (`backend/app/agents/sequencing_agent.py`):
  - Validates generated steps with `DAGValidator.validate()`.
  - On failure, feeds machine-readable error feedback back into the LLM up to 2 times.
  - Re-indexes steps strictly according to deterministic topological order.
  - Falls back to a pre-verified baseline DAG if repair attempts are exhausted.
- **Sequencing Node Validation Integration** (`backend/app/graph/nodes/sequencing.py`):
  - Validates the generated build sequence and logs DAG metrics and topological execution order into `state["history_trace"]`.
- **Automated DAG Validation Test Suite** (`backend/tests/test_dag_validation.py`):
  - 13 comprehensive unit and integration tests covering topological sort, deterministic tie-breaking, direct/indirect cycles, self-dependencies, duplicate nodes, missing dependencies, orphan nodes, invalid IDs, empty plans, and sequencing agent repair & fallback.

---

## [0.7.0-phase5] - 2026-09-15

### Added
- **LangGraph V2 Orchestration & Self-Correcting Reflection Loops** (`backend/app/graph/workflow.py`):
  - Upgraded linear pipeline DAG into a cyclic, bounded agentic graph with conditional routing and automated self-correction.
  - **Feasibility Refinement Loop:** `route_feasibility` conditionally routes unfeasible models (`FEASIBLE_WITH_MODIFICATION` / `NOT_FEASIBLE`) to `parameter_adaptation_node` to mathematically re-scale batch size and mixed precision settings, re-evaluating hardware feasibility until compliant or bounded by `max_feasibility_retries = 2`.
  - **Code Evaluation & Repair Loop:** `route_evaluation` inspects 3-layer verification outputs (`layer1_syntax`, `layer2_grounding`, `layer3_execution`); on failure, routes to `code_repair_node` to patch syntax/runtime errors via error-guided reflexion, bounded by `max_repair_retries = 2`.
- **Modular V2 Pipeline Graph Nodes**:
  - `backend/app/graph/nodes/adaptation.py`: Adapts hyperparameters (batch size, precision) with `status="DERIVED"` and `extraction_method="feasibility_adaptation"`.
  - `backend/app/graph/nodes/specification.py`: Synthesizes modular architecture specifications from build sequences.
  - `backend/app/graph/nodes/code_generation.py`: Synthesizes candidate PyTorch code for target components.
  - `backend/app/graph/nodes/evaluation.py`: Runs 3-layer AST syntax, grounding score, and sandboxed subprocess forward pass.
  - `backend/app/graph/nodes/repair.py`: Applies reflexion prompts or heuristic patches to repair failing model code.
- **Explicit V2 Pipeline State & Bounds** (`backend/app/graph/state.py`):
  - Declared typed state fields including `feasibility_loop_count`, `max_feasibility_retries`, `code_repair_loop_count`, `max_repair_retries`, `history_trace`, and `verification_result`.
- **Automated LangGraph V2 Test Suite** (`backend/tests/test_langgraph_v2.py`):
  - 12 comprehensive unit and integration tests verifying conditional routing, batch size adaptation, bounded exits on max retries, heuristic code repair, valid PyTorch execution, end-to-end feasibility self-correction cycles, and code repair reflection cycles.

---

## [0.6.0-phase4] - 2026-09-15

### Added
- **SQLite Persistent Job Store** (`backend/app/core/job_store.py`):
  - Zero-dependency built-in SQLite persistence engine (`storage/jobs.db`) configured with Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) and busy timeout for high-concurrency read/write operations.
  - Complete `JobRecord` schema with canonical `job_id`, `paper_id`, `status`, `progress`, `current_stage`, `result`, `error`, `retry_count`, `cancellation_requested`, and ISO-8601 timestamps (`created_at`, `started_at`, `completed_at`, `updated_at`).
  - Indexed queries across `paper_id`, `status`, and `updated_at`.
  - Built-in `recover_stale_jobs()` method that auto-recovers zombie/interrupted jobs (marked `queued`, `processing`, or `running` during crash/restart) into `failed` state with truthful explanatory errors.
  - Full cancellation semantics (`cancel_job`, `is_cancellation_requested`) to cleanly halt long-running background tasks.
  - Backwards-compatible `JobStoreDictWrapper` implementing `collections.abc.MutableMapping` to support legacy dictionary access seamlessly without breaking existing callers.
- **Server Startup Job Recovery Hook** (`backend/main.py`):
  - Added FastAPI startup event hook calling `recover_stale_jobs()` to ensure server restarts never leave zombie jobs hanging on client connections.
- **Cancellation API Endpoint** (`backend/app/api/v1/endpoints/pipeline.py`):
  - Added `POST /api/v1/analyze/{job_id}/cancel` enabling graceful user and client cancellation.
- **Automated Lifecycle Test Suite** (`backend/tests/test_job_lifecycle.py`):
  - 10 automated tests covering restart persistence, zombie job recovery, duplicate submission idempotency, cancellation semantics, truthful SSE streams, and dictionary wrapper compatibility.

### Changed
- **Pipeline Task & Analysis Endpoints** (`backend/app/api/v1/endpoints/pipeline.py`):
  - Replaced transient in-memory `analysis_jobs = {}` dictionary with persistent SQLite `job_store`.
  - Added duplicate submission safety in `trigger_analysis`: active jobs for the same paper are detected and reused instead of clobbering state or spawning duplicate workers.
  - Integrated cancellation checkpoints into `run_pipeline_task` to prevent wasted compute when jobs are cancelled.
  - Completely overhauled `stream_analysis_events`:
    - Eliminated fake `COMPLETED` events on timeout or missing jobs.
    - Emits truthful stages, progress events, and periodic keepalive pings.
    - Emits `STILL_RUNNING` if polling stream limit is reached while background task continues.
- **Paper Ingestion Stage Truthfulness** (`backend/app/api/v1/endpoints/papers.py`):
  - Removed deceptive `analysis_jobs[paper_id] = {"status": "completed", "progress": 100}` spoofing on raw PDF upload; records explicit `ingested_and_indexed` stage instead.

---

## [0.5.0-phase3] - 2026-09-15

### Added
- **5-Tier Provenance Status Architecture** (`backend/app/schemas/pipeline.py` & `backend/app/schemas/pipeline_schemas.py`):
  - Declared `ProvenanceStatus` enum: `EXPLICIT`, `DERIVED`, `INFERRED`, `ASSUMED`, `UNKNOWN`.
  - Refactored `ParameterDetails` and `ProjectParameter` schemas to default to `UNKNOWN` with `value=None` and `confidence=0.0`.
  - Added fields: `evidence` (exact verbatim text quote), `page`, `source_section`, `evidence_strength` (`STRONG`, `MODERATE`, `WEAK`, `NONE`), and `extraction_method`.
  - Added `get_effective_value(field_name, fallback_default)` helper to `ExtractedParameters` to distinguish paper-attested facts from framework defaults.
- **Anti-Hallucination Extraction Engine** (`backend/app/agents/parameter_agent.py`):
  - Completely removed hardcoded fake defaults (`0.0001`, `16`, `AdamW`, `CrossEntropyLoss`, `Swin-T`) that were previously mislabeled as `EXPLICIT`.
  - Mandated verbatim quotes for any `EXPLICIT` claim; automatically downgrades unevidenced explicit claims to `INFERRED`.
  - Missing parameters are faithfully represented as `status="UNKNOWN"`, `value=None`, and `evidence_strength="NONE"`.
- **Downstream Provenance Propagation**:
  - `backend/app/agents/code_gen_agent.py`: Checks parameter provenance before generation and informs models when parameters are `UNKNOWN` so framework defaults are used transparently with descriptive comments.
  - `backend/app/core/code_verifier.py`: Filtered out `UNKNOWN` / `None` parameters in Layer 2 hyperparameter grounding so code is neither unfairly penalized nor falsely credited for omitted values.
- **Verification Tests** (`backend/tests/test_provenance_extraction.py`):
  - 7 automated tests validating explicit quote attachment, honest `UNKNOWN` representation for absent parameters, derived parameter calculation tracking, anti-hallucination downgrading, fallback error integrity, and verifier filtering.

---

## [0.4.0-phase2] - 2026-09-15

### Added
- **Strict Per-Paper Data Isolation** (`backend/app/retrieval/vector_db.py`):
  - Updated `semantic_search`, `keyword_search`, and `hybrid_search` to enforce `paper_id` parameter constraints.
  - When `paper_id` is supplied, retrieval exclusively queries `{paper_id}.json`, guaranteeing zero cross-paper retrieval contamination.
  - Added `delete_paper(paper_id)` for atomic vector deletion and cache management.
  - Added chunk deduplication during ingestion using SHA-256 content hashing.
  - Added standardized RAG retrieval contract (`paper_id`, `chunk_id`, `text`, `content`, `section`, `subsection`, `page`, `score`, `similarity_score` / `rrf_score`).
- **Robust Embedding Architecture** (`backend/app/retrieval/embeddings.py`):
  - Completely eliminated `ord(char)` pseudo-embedding fallback calculations.
  - Introduced `EmbeddingError` custom exception to fail fast on unreachable embedding daemons instead of quietly corrupting vector space.
  - Added exponential backoff retry logic (up to 2 retries) and batch processing (`generate_local_embeddings_batch`).
  - Added embedding model metadata tracking (`get_embedding_metadata`).
- **Complete Ingestion Pipeline** (`backend/app/graph/nodes/ingestion.py`):
  - Removed `chunks[:5]` artificial slicing limit. Now embeds and indexes all chunks across all sections of uploaded research papers.
- **Verification Tests** (`backend/tests/test_rag_isolation.py`):
  - 7 automated tests validating cross-paper isolation, complete chunk indexing, deduplication, atomic paper deletion, embedding error propagation, standard RAG contract adherence, and vector search tool isolation.

### Changed
- Refactored `backend/app/tools/vector_search_tool.py`, `backend/app/agents/parameter_agent.py`, and `backend/app/agents/decomposition_agent.py` to pass `paper_id` into vector queries and eliminate cross-paper fallbacks.

---

## [0.3.0-phase1] - 2026-09-14

### Added
- **Code Execution Abstraction & Sandbox Architecture** (`backend/app/core/sandbox/`):
  - `base.py`: Declared `CodeExecutor` abstract base class, `ExecutionLimits`, and standardized `ExecutionResult` contracts.
  - `policies.py`: AST static security scanner `SecurityPolicy` identifying banned modules (`os`, `sys`, `subprocess`, `socket`, `requests`, `urllib`), dangerous calls (`eval`, `exec`, `open`, `__import__`), and sensitive attribute accesses (`__builtins__`, `__subclasses__`).
  - `subprocess_runner.py`: Implemented `SubprocessCodeExecutor` running candidate PyTorch code inside isolated OS subprocesses with disposable temporary sandbox directories, stripped environment variables (preventing secret exfiltration), blocked network sockets, single-threaded PyTorch bounds, and hard timeout termination.
- **Verification Tests** (`backend/tests/test_sandbox_security.py`):
  - 8 automated tests validating infinite loop termination via timeout, secret environment variable stripping, temporary directory cleanup, non-model file bypass, legitimate model forward pass verification, runtime shape mismatch error capture, and AST security policy bans.

### Changed
- **Eliminated In-Process `exec()`**:
  - `backend/app/core/code_verifier.py`: Completely removed in-process `exec(compiled_code, exec_globals)` from the FastAPI server process. Forward pass testing now delegates directly to `SubprocessCodeExecutor`.
  - Updated AST safety checks to delegate to `SecurityPolicy.analyze()`.

---

## [0.2.0-phase0] - 2026-09-12

### Added
- **Phase 0 Deliverables**:
  - `docs/v2/baseline.md`: Complete snapshot of current repository state, git commit hash (`7949b9d`), file inventory (15 backend files, 1,353 lines of code), test suite coverage, and existing metrics.
  - `docs/v2/architecture-current.md`: Detailed documentation of the V1 architecture, REST API routes, linear LangGraph DAG, RAG flow, extraction schemas, and in-process code verification mechanism.
  - `docs/v2/known-issues.md`: Detailed categorization of 8 confirmed bugs and security vulnerabilities from the deep backend engineering audit.
  - `docs/v2/changelog.md`: Initialized the project migration changelog.
- **Audit Reports**:
  - Comprehensive Deep Backend Engineering Audit in `DEEP_BACKEND_ENGINEERING_AUDIT.md` and `docs/backend_docs/deep_backend_engineering_audit.md`.
  - Phase-wise enhancement plan in `PHASE_WISE_PLAN_PAPER_2_PROJECT_V2.md`.

### Changed
- Freezing backend code changes until Phase 1 begins. Zero production source files altered in Phase 0.

---

## [0.1.0] - 2026-09-12 (V1 Baseline)

### Added
- Initial FastAPI backend for paper-to-project synthesis.
- Linear LangGraph workflow connecting architecture, parameter extraction, code generation, verification, and evaluation.
- Basic PDF extraction via PyMuPDF.
- ChromaDB vector store integration with OpenAI embeddings.
- In-process code verification using Python `exec()`.
- Initial unit test suite under `backend/tests/` (7 test files, 15 unit tests).
