# Known Issues & Architectural Vulnerabilities

> **Document Status:** V2 Post-Migration Audit  
> **Original Source:** Deep Backend Engineering Audit (`DEEP_BACKEND_ENGINEERING_AUDIT.md`)  
> **V1 Freeze Commit:** `7949b9d` — September 12, 2026  
> **V2 Updated:** 2026-10-03

This document tracks all confirmed bugs, security vulnerabilities, and architectural deficiencies identified in the V1 baseline, along with their current V2 resolution status.

---

## Status Key

| Symbol | Meaning |
|---|---|
| ✅ **RESOLVED** | Issue fully fixed and covered by automated tests |
| ⚠️ **PARTIAL** | Substantively improved but not fully closed |
| ❌ **OPEN** | Not yet addressed |
| 🔜 **BACKLOG** | Planned but not yet implemented |

---

## 1. Critical Severity (Safety & Security)

### SEC-01: Direct Arbitrary Code Execution via In-Process `exec()` — ✅ RESOLVED (Phase 1)

- **Original Location:** `backend/app/services/code_verifier.py`
- **Nature:** Critical Remote Code Execution (RCE) / Host Compromise
- **V1 Behavior:** `exec(code, globals_dict, locals_dict)` ran directly inside the FastAPI uvicorn process with only superficial import checking, vulnerable to obfuscated imports, infinite loops, and OOM bombs.
- **V2 Fix (`backend/app/core/sandbox/`)**:
  - `subprocess_runner.py`: `SubprocessCodeExecutor` runs candidate code in an isolated OS subprocess with hard timeout termination, stripped environment variables (no secret exfiltration), single-threaded PyTorch bounds, and a disposable temp directory.
  - `policies.py`: `SecurityPolicy` performs AST-level deep scanning banning `os`, `sys`, `subprocess`, `socket`, `requests`, `urllib`, `eval`, `exec`, `open`, `__import__`, `__builtins__`, `__subclasses__`.
  - `base.py`: Declares `CodeExecutor` abstract base, `ExecutionLimits`, and standardized `ExecutionResult` contracts.
- **Test Coverage:** `test_sandbox_security.py` (8 tests: infinite loop timeout, secret stripping, temp cleanup, network blocking, legitimate forward pass, shape mismatch capture, AST policy bans)

---

## 2. High Severity (Data Loss, Silent Corruption & Pipeline Logic)

### BUG-01: Hardcoded Chunk Truncation to 5 Chunks — ✅ RESOLVED (Phase 3)

- **Original Location:** `backend/app/services/pdf_extractor.py` → `chunks[:5]`
- **Nature:** Catastrophic data omission — Methods, hyperparameters, experiments all discarded
- **V2 Fix:** `backend/app/graph/nodes/ingestion.py` removed artificial `chunks[:5]` slicing. Full document is now embedded and indexed across all sections.
- **Test Coverage:** `test_rag_isolation.py` (complete chunk indexing assertion)

---

### BUG-02: Pseudo-Embedding Fallback (`ord(char)`) — ✅ RESOLVED (Phase 3)

- **Original Location:** `backend/app/services/embeddings.py`
- **Nature:** Semantic corruption — ASCII character code cosine similarity = random nonsense vectors
- **V2 Fix:** `backend/app/retrieval/embeddings.py`:
  - `ord(char)` fallback completely eliminated.
  - `EmbeddingError` custom exception introduced — fails fast on unreachable embedding daemons.
  - Exponential backoff retry (up to 2 retries) added.
  - `generate_local_embeddings_batch()` for efficient batch processing.
- **Test Coverage:** `test_rag_isolation.py` (embedding error propagation assertion)

---

### BUG-03: Vector Search Cross-Paper Contamination — ✅ RESOLVED (Phase 3)

- **Original Location:** `backend/app/services/vector_db.py` — no `where` clause on queries
- **Nature:** Multi-tenant cross-contamination — Paper A retrieval pollutes Paper B analysis
- **V2 Fix:** `backend/app/retrieval/vector_db.py`:
  - `semantic_search()`, `keyword_search()`, `hybrid_search()` all enforce `paper_id` parameter constraints.
  - When `paper_id` is supplied, only `{paper_id}.json` is queried — zero cross-paper contamination.
  - `delete_paper(paper_id)` for atomic vector deletion.
  - SHA-256 content hashing for chunk deduplication during ingestion.
- **Test Coverage:** `test_rag_isolation.py` (7 tests: cross-paper isolation, deletion, dedup, standard contract)

---

### BUG-04: Parameter Hallucination Masquerading as `EXPLICIT` — ✅ RESOLVED (Phase 2)

- **Original Location:** `backend/app/agents/parameter_agent.py` — hardcoded `learning_rate = 0.0001`, `optimizer = "AdamW"` labeled `EXPLICIT`
- **Nature:** Provenance fabrication — developers deceived about paper-stated vs invented parameters
- **V2 Fix:** `backend/app/schemas/pipeline.py` + `parameter_agent.py`:
  - 5-tier `ProvenanceStatus` enum: `EXPLICIT`, `DERIVED`, `INFERRED`, `ASSUMED`, `UNKNOWN`
  - `EXPLICIT` requires verbatim text quote (`evidence` field) + `page` + `source_section`
  - Unevidenced `EXPLICIT` claims are auto-downgraded to `INFERRED`
  - Missing parameters faithfully represented as `status="UNKNOWN"`, `value=None`, `evidence_strength="NONE"`
  - `get_effective_value()` helper distinguishes paper-attested vs framework defaults
  - `code_verifier.py` Layer 2 filters out `UNKNOWN`/`None` params — not penalized, not falsely credited
- **Test Coverage:** `test_provenance_extraction.py` (7 tests)

---

### BUG-05: Premature Job Completion in PDF Upload Handler — ✅ RESOLVED (Phase 5)

- **Original Location:** `backend/app/routers/papers.py` — `analysis_jobs[paper_id] = {"status": "completed", "progress": 1.0}` set immediately after chunking
- **Nature:** Asynchronous race condition / UI deception
- **V2 Fix:** `backend/app/core/job_store.py` + `backend/app/api/v1/endpoints/papers.py`:
  - Deceptive `"completed"` spoofing removed; records `ingested_and_indexed` stage truthfully
  - SQLite `JobRecord` state machine: `queued → running → completed / failed`
  - SSE stream emits truthful `node_started`, `node_completed`, and periodic keepalive events
  - `recover_stale_jobs()` auto-recovers zombie jobs on server restart
- **Test Coverage:** `test_job_lifecycle.py` (10 tests: persistence, zombie recovery, cancel, duplicate safety)

---

## 3. Medium Severity (Reliability, Architecture & Evaluability)

### ARCH-01: Purely Linear LangGraph Topology — ✅ RESOLVED (Phase 4)

- **Original Location:** `backend/app/workflow/graph.py` — `START → arch → params → code → verifier → eval → END`
- **Nature:** No self-correction, no conditional routing, no retry on failure
- **V2 Fix:** `backend/app/graph/workflow.py`:
  - **Feasibility Refinement Loop:** `route_feasibility()` conditional edge routes unfeasible models to `parameter_adaptation_node`, re-evaluates until `FEASIBLE` or `max_feasibility_retries=2` exhausted
  - **Code Repair Loop:** `route_evaluation()` conditional edge routes failed code to `code_repair_node` for reflexion-guided patching, bounded by `max_repair_retries=2`
  - New nodes: `adaptation_node`, `specification_node`, `code_generation_node`, `evaluation_node`, `code_repair_node`
  - All nodes wrapped with `wrap_node_with_telemetry()` for real SSE event emission
- **Test Coverage:** `test_langgraph_v2.py` (12 tests), `test_v2_bounded_loops.py`

---

### ARCH-02: Ephemeral In-Memory State (`dict`) — ✅ RESOLVED (Phase 5)

- **Original Location:** `backend/app/routers/pipeline.py` → `analysis_jobs = {}`
- **Nature:** Complete data loss on crash or redeploy; multi-worker 404s
- **V2 Fix:** `backend/app/core/job_store.py`:
  - Zero-dependency SQLite (`storage/jobs.db`) with WAL mode and busy timeout
  - Full `JobRecord` schema: `job_id`, `paper_id`, `status`, `progress`, `current_stage`, `result`, `error`, `retry_count`, `cancellation_requested`, ISO-8601 timestamps
  - Indexed queries on `paper_id`, `status`, `updated_at`
  - `recover_stale_jobs()` on startup
  - `cancel_job()` + `is_cancellation_requested()` for graceful cancellation
  - `JobStoreDictWrapper` for zero-breaking-change backwards compatibility
- **Test Coverage:** `test_job_lifecycle.py` (10 tests)

---

### EVAL-01: Hardcoded Mock Values in Evaluation Suite — ⚠️ PARTIAL

- **Original Location:** `backend/app/services/eval_suite.py` — `"architecture_accuracy": 95.0` etc. as static constants
- **Nature:** Fabricated benchmark metrics — no empirical foundation
- **V2 Progress:**
  - `test_v2_eval_regression.py` and `test_v2_semantic_assertions.py` added to catch regressions.
  - `POST /evals/run-rag` endpoint added for live RAG faithfulness evaluation.
  - `GET /evals/benchmark/{paper_id}` returns stored benchmark results per paper.
  - `rag_evaluation.ipynb` added for manual faithfulness + context recall evaluation.
- **Remaining Gap:** Full Ragas-based automated faithfulness and hallucination scoring pipeline not yet fully integrated in the default run path. Some fallback score paths may still return deterministic values.
- **Backlog:** Replace remaining fallback paths with `ragas` or custom evaluator calls in `eval_suite.py`.

---

### ARCH-03 (NEW): Multi-Worker Job Distribution — 🔜 BACKLOG

- **Location:** `backend/app/core/job_store.py`
- **Nature:** SQLite WAL works for single-process; `uvicorn --workers N` with N>1 still has read-contention issues at high throughput.
- **Impact:** Low — development and demo usage is single-worker. Not production-blocking.
- **Mitigation Plan:** Replace SQLite backend with Redis-backed queue (Celery or ARQ) for true multi-worker distribution.

---

### ARCH-04 (NEW): Code Executor Runs OS Subprocess, Not Container — 🔜 BACKLOG

- **Location:** `backend/app/core/sandbox/subprocess_runner.py`
- **Nature:** `SubprocessCodeExecutor` provides process-level isolation but not OS-level container isolation. A container escape or kernel exploit could still affect the host.
- **Impact:** Low — environment variable stripping, network blocking, and timeout mitigate most real-world vectors.
- **Mitigation Plan:** Docker container execution (gVisor or restricted seccomp profile) for production deployments.

---

## 4. Summary Matrix

| ID | Category | Severity | File | V1 Status | V2 Status |
|---|---|---|---|---|---|
| **SEC-01** | Security | Critical | `code_verifier.py` | In-process `exec()` | ✅ `SubprocessCodeExecutor` + `SecurityPolicy` |
| **BUG-01** | Ingestion | High | `ingestion.py` | `chunks[:5]` | ✅ Full indexing |
| **BUG-02** | Embeddings | High | `embeddings.py` | `ord(c)` fallback | ✅ `EmbeddingError` fail-fast |
| **BUG-03** | RAG Search | High | `vector_db.py` | Cross-paper mixing | ✅ `paper_id` isolation |
| **BUG-04** | Extraction | High | `parameter_agent.py` | Fake `EXPLICIT` tags | ✅ 5-tier `ProvenanceStatus` |
| **BUG-05** | Workflow | High | `papers.py` | Premature `"completed"` | ✅ SQLite state machine |
| **ARCH-01** | Agentic | Medium | `workflow.py` | Strictly linear DAG | ✅ 2 bounded self-correcting loops |
| **ARCH-02** | Reliability | Medium | `job_store.py` | In-memory `dict` | ✅ SQLite WAL persistent store |
| **EVAL-01** | Evaluation | Medium | `eval_suite.py` | Hardcoded `95.0%` | ⚠️ Partial — live eval added, fallbacks remain |
| **ARCH-03** | Scalability | Low | `job_store.py` | N/A | 🔜 Redis queue for multi-worker |
| **ARCH-04** | Security | Low | `subprocess_runner.py` | N/A | 🔜 Docker/gVisor container isolation |
