# RUEXIS AI Platform V2 — Baseline & State Report

> **Document Type:** V2 State Reference  
> **Initial Baseline Timestamp:** 2026-09-12T22:25:00+05:30 (V1 freeze)  
> **Current Update:** 2026-10-03  
> **Base Git Commit (V1 freeze):** `7949b9d`  
> **Current Version:** `2.0.0`  
> **Objective:** Full V2 state reference — directory snapshot, test inventory, and current metric baseline.

---

## 1. Version & Environment Metadata

| Attribute | V1 Baseline Value | V2 Current Value |
|---|---|---|
| **Project Name** | RUEXIS AI (Paper-2-Project) | RUEXIS AI Platform |
| **Backend Version** | `1.0.0` | `2.0.0` |
| **Python Target** | Python 3.11 / 3.14 compatible | Python 3.11 / 3.14 compatible |
| **Primary Frameworks** | FastAPI 0.141.1, LangGraph 1.2.11, Pydantic 2.13.4 | FastAPI 0.141.1, LangGraph 1.2.11+, Pydantic 2.x |
| **Operating System** | Windows 11 (Host) | Windows 11 (Host) |
| **Primary Local LLM** | Ollama `qwen2.5-coder:1.5b` | Ollama (configurable per user profile) |
| **Cloud Models** | Groq, OpenRouter Gemini, HF Coder | Gemini Flash, Groq, OpenRouter, OpenAI, Anthropic |
| **LangGraph Topology** | Linear DAG, 0 cycles | Cyclic V2 — 2 bounded self-correcting loops |
| **Code Execution** | In-process `exec()` (RCE risk) | Isolated `SubprocessCodeExecutor` (sandbox) |
| **Job Persistence** | In-memory `dict` (volatile) | SQLite WAL (`storage/jobs.db`, crash-safe) |

---

## 2. Directory Structure Snapshot (V2 Current)

```text
backend/
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── requirements_clean.txt
├── pytest.ini
├── main.py
├── app/
│   ├── __init__.py
│   ├── api/
│   │   └── v1/
│   │       ├── api_router.py
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── chat.py
│   │           ├── hardware.py
│   │           ├── models.py
│   │           ├── papers.py
│   │           ├── pipeline.py
│   │           └── telemetry.py
│   ├── agents/
│   │   ├── chat/
│   │   │   ├── context_builder.py
│   │   │   ├── react_utils.py
│   │   │   └── smart_titler.py
│   │   ├── chat_agent.py
│   │   ├── code_gen_agent.py
│   │   ├── decomposition_agent.py
│   │   ├── feasibility_agent.py
│   │   ├── gap_agent.py
│   │   ├── ingestion_agent.py
│   │   ├── parameter_agent.py
│   │   ├── report_agent.py
│   │   ├── sequencing_agent.py
│   │   └── specification_agent.py
│   ├── core/
│   │   ├── code_verifier.py            # 12-rung verification ladder (V2)
│   │   ├── config.py                   # VERSION = "2.0.0"
│   │   ├── constants.py
│   │   ├── cost_optimizer.py           # NEW V2
│   │   ├── dag_validator.py            # NEW V2 (Phase 6)
│   │   ├── database.py
│   │   ├── db/
│   │   │   ├── chat_repo.py
│   │   │   ├── episodic_repo.py
│   │   │   ├── paper_repo.py
│   │   │   ├── profile_repo.py
│   │   │   └── storage_engine.py
│   │   ├── dual_code_engine.py
│   │   ├── events.py                   # NEW V2 (SSE emitters)
│   │   ├── history_logger.py
│   │   ├── job_store.py                # NEW V2 (Phase 5 — SQLite WAL)
│   │   ├── limits_dashboard.py
│   │   ├── manifest.py                 # NEW V2 (run execution ledger)
│   │   ├── model_router.py
│   │   ├── prompts.py
│   │   ├── quota_tracker.py
│   │   ├── sandbox/
│   │   │   ├── base.py                 # NEW V2 (Phase 1)
│   │   │   ├── policies.py             # NEW V2 (SecurityPolicy AST scanner)
│   │   │   └── subprocess_runner.py    # NEW V2 (isolated subprocess executor)
│   │   ├── security.py
│   │   └── tracer.py
│   ├── evals/
│   │   └── eval_suite.py
│   ├── extraction/
│   │   ├── benchmark.py                # NEW V2
│   │   ├── block_extractor.py
│   │   ├── constants.py
│   │   ├── docling_parser.py
│   │   ├── element_cropper.py          # NEW V2 (VLM prep)
│   │   ├── grobid_client.py
│   │   ├── grobid_parser.py
│   │   ├── merger.py
│   │   ├── openrouter_parser.py
│   │   ├── pdf_inspector.py
│   │   ├── pdf_parser.py
│   │   ├── pymupdf_parser.py
│   │   ├── router.py
│   │   ├── section_detector.py
│   │   ├── semantic_analyzer.py        # NEW V2
│   │   ├── validator.py
│   │   └── vlm_processor.py           # NEW V2 (Gemini VLM)
│   ├── graph/
│   │   ├── state.py                    # V2 extended PipelineState
│   │   ├── workflow.py                 # V2 cyclic graph with 2 bounded loops
│   │   └── nodes/
│   │       ├── adaptation.py           # NEW V2
│   │       ├── code_generation.py      # NEW V2
│   │       ├── evaluation.py           # NEW V2
│   │       ├── extraction.py
│   │       ├── feasibility.py
│   │       ├── ingestion.py
│   │       ├── repair.py               # NEW V2
│   │       ├── sequencing.py
│   │       ├── specification.py        # NEW V2
│   │       └── verification.py
│   ├── providers/
│   │   ├── groq_adapter.py
│   │   ├── hf_adapter.py
│   │   ├── ollama_adapter.py
│   │   └── openrouter_adapter.py
│   ├── retrieval/
│   │   ├── chunker.py                  # V2: full indexing (no [:5] slicing)
│   │   ├── embeddings.py               # V2: no ord(char) fallback
│   │   ├── knowledge_graph.py
│   │   └── vector_db.py                # V2: paper_id isolation enforced
│   ├── schemas/
│   │   ├── canonical_paper.py
│   │   ├── chat.py
│   │   ├── paper.py
│   │   ├── pipeline.py                 # V2: 5-tier ProvenanceStatus
│   │   ├── pipeline_schemas.py
│   │   └── rag_schemas.py
│   └── tools/
│       ├── arxiv_search_tool.py
│       ├── base_tool.py
│       ├── canonical_document_tool.py
│       ├── episodic_memory_tool.py
│       ├── graph_search_tool.py
│       ├── hyperparameter_tool.py
│       ├── scholar_search_tool.py
│       └── vector_search_tool.py
├── storage/
│   ├── papers/
│   ├── rag_embeddings/                 # Renamed from rag_based/ (V2)
│   ├── conversations/
│   ├── codes/
│   ├── history/
│   ├── user_profile.json
│   └── jobs.db                         # NEW V2 (SQLite persistent job store)
├── reports/                            # NEW V2 (centralized artifact output)
│   ├── extracted_json/
│   ├── knowledge_graphs/
│   ├── manifests/
│   ├── traces/
│   ├── benchmarks/
│   ├── evaluation/
│   ├── audit/
│   ├── optimization/
│   └── performance/
└── tests/
    ├── end_to_end_backend_testing.ipynb
    ├── extraction_test.ipynb
    ├── extraction_test_2.ipynb
    ├── rag_evaluation.ipynb
    ├── test_adaptive_extraction.py
    ├── test_api_endpoints.py
    ├── test_chat_agent.py
    ├── test_code_gen_agent.py
    ├── test_concurrency_performance.py
    ├── test_cost_optimization.py
    ├── test_dag_validation.py
    ├── test_database.py
    ├── test_dual_code_engine.py
    ├── test_event_observability.py
    ├── test_ingestion_agent.py
    ├── test_job_lifecycle.py
    ├── test_knowledge_graph.py
    ├── test_langgraph_v2.py
    ├── test_limits_dashboard.py
    ├── test_merger.py
    ├── test_model_router.py
    ├── test_phase12_reliability.py
    ├── test_provenance_extraction.py
    ├── test_rag_isolation.py
    ├── test_real_pdf_hardening.py
    ├── test_run_manifest.py
    ├── test_sandbox_security.py
    ├── test_section_detector.py
    ├── test_v2_bounded_loops.py
    ├── test_v2_concurrency.py
    ├── test_v2_eval_regression.py
    ├── test_v2_failure_injection.py
    ├── test_v2_malformed_inputs.py
    ├── test_v2_semantic_assertions.py
    └── test_verification_ladder.py
```

---

## 3. Test Suite Inventory (V2 Current — 35 Files)

| Test Module | Primary Target | Phase Introduced |
|---|---|---|
| `test_database.py` | `ChatDatabase`, `StorageEngine` atomic CRUD | V1 Baseline |
| `test_merger.py` | Multi-parser table & section reconciliation | V1 Baseline |
| `test_model_router.py` | Failover logic, sliding-window quotas | V1 Baseline |
| `test_code_gen_agent.py` | AST syntax checking and cross-file imports | V1 Baseline |
| `test_section_detector.py` | Section regex detection and Roman numerals | V1 Baseline |
| `test_limits_dashboard.py` | HTML quota rendering | V1 Baseline |
| `test_api_endpoints.py` | Integration tests against FastAPI TestClient | V1 Baseline |
| `test_chat_agent.py` | ReAct turn execution and title generation | V1 Baseline |
| `test_ingestion_agent.py` | Title and abstract extraction | V1 Baseline |
| `test_dual_code_engine.py` | Gemini + HF dual-candidate synthesis | V1 Baseline |
| `test_sandbox_security.py` | Subprocess isolation, env stripping, timeout | Phase 1 |
| `test_provenance_extraction.py` | 5-tier provenance, anti-hallucination | Phase 2 |
| `test_rag_isolation.py` | Per-paper RAG isolation, full indexing | Phase 3 |
| `test_langgraph_v2.py` | V2 cyclic graph routing & bounded loops | Phase 4 (core) |
| `test_v2_bounded_loops.py` | Feasibility + repair loop bounds | Phase 4 |
| `test_job_lifecycle.py` | SQLite persistence, zombie recovery, cancel | Phase 5 |
| `test_dag_validation.py` | Kahn's sort, cycle detection, repair fallback | Phase 6 |
| `test_event_observability.py` | SSE event emission & ordering | V2 observability |
| `test_run_manifest.py` | Execution ledger generation & retrieval | V2 manifest |
| `test_knowledge_graph.py` | KG entity extraction & tier validation | V2 KG |
| `test_verification_ladder.py` | 12-rung code verifier rungs 1–12 | V2 verifier |
| `test_adaptive_extraction.py` | Adaptive PDF routing with VLM gate | V2 extraction |
| `test_real_pdf_hardening.py` | Real-world adversarial PDF edge cases | V2 hardening |
| `test_cost_optimization.py` | Cost optimizer routing decisions | V2 cost |
| `test_concurrency_performance.py` | Concurrent upload throughput | V2 perf |
| `test_v2_concurrency.py` | Concurrent pipeline run isolation | V2 perf |
| `test_v2_failure_injection.py` | Fault injection & error propagation | V2 reliability |
| `test_v2_malformed_inputs.py` | Malformed PDF / corrupted input handling | V2 reliability |
| `test_phase12_reliability.py` | Phase 1+2 combined reliability | V2 reliability |
| `test_v2_eval_regression.py` | Eval suite regression vs hardcoded scores | V2 evals |
| `test_v2_semantic_assertions.py` | Semantic correctness of extraction output | V2 evals |
| `end_to_end_backend_testing.ipynb` | 12-phase sequential pipeline run | Notebook |
| `extraction_test.ipynb` | Extraction pipeline manual testing | Notebook |
| `extraction_test_2.ipynb` | Extended extraction edge cases | Notebook |
| `rag_evaluation.ipynb` | RAG faithfulness & recall evaluation | Notebook |

---

## 4. V1 Issues vs V2 Resolution Status

| ID | V1 Issue | V2 Status |
|---|---|---|
| **SEC-01** | In-process `exec()` RCE | ✅ **FIXED** — `SubprocessCodeExecutor` + `SecurityPolicy` (Phase 1) |
| **BUG-01** | `chunks[:5]` ingestion truncation | ✅ **FIXED** — Full indexing in Phase 3 |
| **BUG-02** | `ord(char)` pseudo-embedding fallback | ✅ **FIXED** — `EmbeddingError` fail-fast + retry (Phase 3) |
| **BUG-03** | Cross-paper RAG contamination | ✅ **FIXED** — `paper_id` isolation enforced (Phase 3) |
| **BUG-04** | Hallucinated `EXPLICIT` parameters | ✅ **FIXED** — 5-tier `ProvenanceStatus` + verbatim quote requirement (Phase 2) |
| **BUG-05** | Premature `"completed"` job status | ✅ **FIXED** — SQLite state machine with truthful stages (Phase 5) |
| **ARCH-01** | Strictly linear LangGraph | ✅ **FIXED** — 2 bounded self-correcting loops (Phase 4) |
| **ARCH-02** | Ephemeral in-memory `dict` state | ✅ **FIXED** — SQLite WAL persistent `job_store` (Phase 5) |
| **EVAL-01** | Hardcoded `95.0%` mock scores | ⚠️ **PARTIAL** — Real RAG eval implemented; full regression suite in progress |
