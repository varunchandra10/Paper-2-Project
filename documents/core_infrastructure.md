# Core Infrastructure — RUEXIS AI

> Covers: ModelRouter · Providers · Quota System · JobStore · CodeVerifier ·  
> API Surface · ChatDatabase · Storage Map

---

## 1. ModelRouter — Dispatch & Failover Chain

```mermaid
flowchart TD
    Q([Prompt + model_id]) --> ID{Which provider\ndoes model_id map to?}

    ID -->|Groq model IDs\nqwen3.8 · gpt-oss\nllama-3.3-70b etc| G

    subgraph G["Groq Path"]
        G1{API key\navailable?} -->|No| GE["⚠ Key not configured\nReturn user message"]
        G1 -->|Yes| G2["groq_adapter.complete()"]
        G2 -->|HTTP 200| GS["quota_tracker.record_usage\nReturn content"]
        G2 -->|HTTP 429| GF["Seamless Failover Chain"]
        GF --> GF1{has_gemini?}
        GF1 -->|Yes| GF2["Gemini 2.0 Flash\nvia httpx direct call\nAPI key in header only"]
        GF2 -->|200| GFS[Return · Auto-Failover label]
        GF2 -->|Fail| GF3{OpenRouter\navailable?}
        GF1 -->|No| GF3
        GF3 -->|Yes| GF4[openrouter_adapter\nfree-tier model]
        GF4 -->|OK| GFS
        GF4 -->|Fail| GF5{HuggingFace\navailable?}
        GF3 -->|No| GF5
        GF5 -->|Yes| GF6[hf_adapter\nQwen2.5-Coder-32B]
        GF6 -->|OK| GFS
        GF6 -->|Fail| GFE["⚠ Rate limit reached\nReturn switch model message"]
    end

    ID -->|OpenRouter model IDs\n:free · gemini · deepseek| O

    subgraph O["OpenRouter Path"]
        O1{API key + quota\navailable?} -->|Yes| O2["openrouter_adapter.complete()"]
        O2 -->|200| OS["record_usage · Return"]
        O2 -->|429| OE["⚠ Return rate limit message"]
        O1 -->|No| OE
    end

    ID -->|Any other / local model| L

    subgraph L["Ollama Local Path"]
        L1["ollama_adapter.complete()\nhost = user profile URL\nor settings.OLLAMA_HOST"]
        L1 -->|OK| LS["record_usage · Return"]
        L1 -->|Offline| LF1["Groq fallback attempt\nGROQ_DEFAULT_MODEL"]
        LF1 -->|OK| LS
        LF1 -->|Fail| LF2["OpenRouter fallback\nOpenRouter PDF model"]
        LF2 -->|OK| LS
        LF2 -->|Fail| OFF(["Offline Mode\nReturn placeholder"])
    end

    GS & OS & LS --> Done([Content · model_used label])
```

---

## 2. Provider Adapters

```mermaid
flowchart LR
    subgraph Adapters["providers/__init__.py — singletons"]
        GA["groq_adapter\n• complete(prompt, api_key, model_id)\n• Extracts rate-limit headers\n  into quota_tracker on each call\n• Models: Qwen3.8-27B · GPT-OSS-120B"]
        OA["openrouter_adapter\n• complete(prompt, api_key, model_id)\n• Free-tier: Gemini Flash · DeepSeek R1\n• Header: HTTP-Referer required"]
        HA["hf_adapter\n• complete(prompt, api_key)\n• Serverless Inference Router\n• Model: Qwen2.5-Coder-32B-Instruct"]
        OL["ollama_adapter\n• complete(prompt, model_id, host)\n• get_available_models(hosts)\n• 100% offline · 0 tokens"]
    end

    MR[ModelRouter] --> GA & OA & HA & OL
    DE[DualCodeEngine] --> GA2[Gemini direct\nhttpx POST] & HA
```

---

## 3. Dual-Layer Quota System

```mermaid
flowchart TD
    subgraph QT["QuotaTracker — LLM Provider Limits"]
        direction TB
        QT1["Reads live rate-limit headers\nfrom each API response\n(x-ratelimit-remaining, etc.)"]
        QT2["Providers tracked:\nGroq · OpenRouter · Gemini · HuggingFace · Local"]
        QT3["is_provider_available(provider)\nrecord_usage(provider, model)\nget_limits_summary()"]
        QT4["Persisted to:\nstorage/history/model_quotas.json"]
    end

    subgraph DQ["DailyQuotaManager — VLM Extraction Budget"]
        direction TB
        DQ1["max_papers_per_day: 50\nmax_vlm_requests_per_day: 200"]
        DQ2["can_use_vlm() → bool\nrecord_vlm_request(paper_id, type, in, out)\nrecord_paper_completion(paper_id, used_vlm)"]
        DQ3["Rolls over at midnight UTC"]
        DQ4["Persisted to:\nstorage/history/daily_extraction_quota.json"]
    end

    MR[ModelRouter] -->|read| QT
    Router[extraction/router.py] -->|check gate| DQ
    LimitsDash["/limits-dashboard UI\nGET /api/v1/models/limits"] -->|reads| QT & DQ
```

---

## 4. SQLite JobStore — State Machine

```mermaid
stateDiagram-v2
    [*] --> QUEUED : create_job()

    QUEUED --> PROCESSING : pipeline starts
    PROCESSING --> RUNNING : LangGraph executing

    RUNNING --> COMPLETED : all nodes passed
    RUNNING --> FAILED : unhandled exception
    RUNNING --> CANCELLED : cancellation_requested = True

    QUEUED --> FAILED : startup crash
    PROCESSING --> FAILED : startup crash

    FAILED --> FAILED : recover_stale_jobs()\non next server startup
    COMPLETED --> [*]
    CANCELLED --> [*]

    note right of RUNNING
        Progress updated per node
        Events appended to job_events table
        SSE stream reads job_events
    end note
```

**SQLite schema (WAL mode, 2 tables):**

```mermaid
erDiagram
    JOBS {
        TEXT job_id PK
        TEXT paper_id
        TEXT status
        REAL progress
        TEXT current_stage
        TEXT result
        TEXT error
        INTEGER retry_count
        TEXT created_at
        TEXT started_at
        TEXT completed_at
        TEXT updated_at
        INTEGER cancellation_requested
    }

    JOB_EVENTS {
        INTEGER id PK
        TEXT job_id FK
        TEXT paper_id
        TEXT event_type
        TEXT node_name
        TEXT status
        REAL progress
        TEXT timestamp
        TEXT metadata
    }

    JOBS ||--o{ JOB_EVENTS : "has"
```

---

## 5. CodeVerifier — 12-Rung Ladder

```mermaid
flowchart TD
    Start([Generated Code]) --> R1

    subgraph Static["Layer 1 — Static Gates (Rungs 1–4)"]
        R1["Rung 1 · AST_VALIDATION\nParse Python grammar\nReject hollow stubs\nNotImplementedError ban"]
        R1 -->|FAIL| EarlyExit1([FAILED · repair_feedback])
        R1 -->|PASS| R2

        R2["Rung 2 · SECURITY_ANALYSIS\nBanned primitives check\nexec · eval · os.system\nsubprocess · __import__"]
        R2 -->|FAIL| EarlyExit2([FAILED · security violation])
        R2 -->|PASS| R3

        R3["Rung 3 · IMPORT_VALIDATION\nScan all import statements\nCount declared modules\n(non-blocking rung)"]
        R3 --> R4

        R4["Rung 4 · BYTECODE_COMPILATION\ncompile(code, 'exec')\nCatch SyntaxError before runtime"]
        R4 -->|FAIL| EarlyExit4([FAILED · compile error])
        R4 -->|PASS| DYN
    end

    subgraph Dynamic["Layer 2 — Dynamic Gates (Rungs 5–11)\nSubprocess isolated sandbox"]
        DYN["SubprocessCodeExecutor\nexecute_verification_ladder()"]
        DYN --> R5["Rung 5 · MODEL_INITIALIZATION\nInstantiate nn.Module class"]
        R5 -->|FAIL| DE5([FAILED])
        R5 -->|PASS| R6

        R6["Rung 6 · FORWARD_PASS\nRun model.forward(dummy_input)\nCapture output tensor shape"]
        R6 -->|FAIL| DE6([FAILED · shape mismatch])
        R6 -->|PASS| R7

        R7["Rung 7 · LOSS_CALCULATION\nCompute loss on forward output"]
        R7 --> R8

        R8["Rung 8 · BACKWARD_PASS\nloss.backward()"]
        R8 --> R9

        R9["Rung 9 · OPTIMIZER_STEP\nAdam / SGD optimizer.step()"]
        R9 --> R10

        R10["Rung 10 · GRADIENT_FLOW\nVerify .grad populated"]
        R10 --> R11

        R11["Rung 11 · MINI_TRAINING_LOOP\nRun 3-step micro-loop"]
        R11 --> R12
    end

    subgraph Fidelity["Layer 3 — Paper Fidelity (Rung 12)"]
        R12["Rung 12 · PAPER_GROUNDING\nHyperparameter fidelity score (50 pts)\n  → value/name match via regex\nArchitecture fidelity score (50 pts)\n  → nn.Module · forward() · layer types\n  → tensor ops · activations\nTotal: 0.0 – 100.0"]
    end

    R12 --> OUT([CodeVerificationReport\nstatus: PASSED / FAILED\nlayer1_syntax · layer2_grounding\nlayer3_execution · output_shape])
```

---

## 6. API Endpoint Surface Map

```mermaid
flowchart LR
    subgraph Root["FastAPI root (main.py)"]
        R0["GET /  →  HTML dashboard or JSON\nGET /limits-dashboard  →  HTML\nGET /api/status  →  health JSON"]
    end

    subgraph Auth["/api/v1/auth"]
        A1["POST /auth/register\nPOST /auth/login\nGET  /auth/profile\nPUT  /auth/profile\nPOST /auth/profile/api-keys\nPOST /auth/profile/ollama-link"]
    end

    subgraph Papers["/api/v1/papers"]
        P1["POST /papers/upload  · upload PDF\nGET  /papers  · list all\nGET  /papers/{id}  · metadata\nGET  /papers/{id}/pdf  · stream PDF\nGET  /papers/{id}/canonical  · full doc\nDELETE /papers/{id}"]
    end

    subgraph Pipeline["/api/v1/pipeline"]
        PL1["POST /pipeline/run  · start job\nGET  /pipeline/jobs/{id}  · status\nGET  /pipeline/jobs/{id}/events  · SSE\nPOST /pipeline/jobs/{id}/cancel\nPOST /pipeline/approve  · approve params\nGET  /pipeline/stream/{id}  · alias SSE"]
    end

    subgraph Chat["/api/v1/conversations"]
        C1["GET  /conversations  · list all\nPOST /conversations  · create\nGET  /conversations/active  · current\nPOST /conversations/active  · set active\nPOST /conversations/{id}/chat  · message\nGET  /conversations/{id}/stream  · SSE chat\nDELETE /conversations/{id}\nPOST /conversations/{id}/facts  · user facts"]
    end

    subgraph Models["/api/v1/models"]
        M1["GET /models  · list all providers\nGET /models/limits  · live quota JSON\nGET /models/local  · Ollama models"]
    end

    subgraph HW["/api/v1/hardware"]
        H1["GET /hardware  · GPU/CPU probe"]
    end

    subgraph Tel["/api/v1/telemetry"]
        T1["GET /telemetry/benchmarks\nGET /telemetry/costs\nGET /telemetry/extraction\nGET /telemetry/evaluation"]
    end
```

---

## 7. ChatDatabase — Flat-File Repository Architecture

```mermaid
flowchart TD
    subgraph CDB["ChatDatabase facade"]
        direction TB
        SE["StorageEngine\nThread-safe atomic JSON I/O\nRLock · load_index · save_index"]
        CR["ChatRepository\n• conversations (per-file JSON)\n• messages · attachments\n• active_conversation_id\n• title management"]
        PR["ProfileRepository\n• users (email → hash)\n• standalone user profile\n• API keys · Ollama link\n• webhook sync"]
        PAR["PaperRepository\n• paper_id → title mapping\n• MD5 hash deduplication index\n  (get_paper_by_hash)"]
        ER["EpisodicRepository\n• ReACT step memory\n• user facts\n• adaptation run history"]
    end

    SE --> CR & PR & PAR & ER

    subgraph Files["Flat-file storage"]
        F1["storage/history/chat_memory_db.json\n(index: users · hashes · episodic)"]
        F2["storage/conversations/{conv_id}.json\n(messages · title · project_id)"]
        F3["storage/history/user_profile.json\n(API keys · Ollama link · prefs)"]
    end

    CR --> F2
    SE --> F1
    PR --> F3
```

---

## 8. Storage Directory — Read/Write Map

```mermaid
flowchart TD
    subgraph Storage["storage/"]
        SP["papers/\n• {paper_id}.pdf\nWrite: upload endpoint\nRead: PDF streaming endpoint"]
        SE["rag_embeddings/\n• {paper_id}.json\n  (chunks + float vectors)\nWrite: ingestion_node · upload\nRead: VectorSearchTool"]
        SC["conversations/\n• {conv_id}.json\nWrite/Read: ChatDatabase.ChatRepository"]
        SH["history/\n• chat_memory_db.json\n• model_quotas.json\n• daily_extraction_quota.json\n• user_profile.json\nWrite/Read: DB repos · QuotaTracker"]
        SK["codes/\n• {paper_id}_model.py\nWrite: code_gen_agent\nRead: telemetry endpoint"]
        SS["jobs.db (SQLite WAL)\nWrite: JobStore all nodes\nRead: SSE stream · status endpoint"]
    end

    subgraph Reports["reports/"]
        RE["extracted_json/\n• {paper_id}.json\nWrite: upload · ingestion_node\nRead: KG auto-build · canonical endpoint"]
        RK["knowledge_graphs/\n• {paper_id}_graph.json\nWrite: PaperKnowledgeGraph.save()\nRead: KnowledgeGraphTool · load_or_create()"]
        RM["manifests/ · traces/ · benchmarks/\nevaluation/ · audit/ · optimization/\nperformance/\nWrite: manifest.py · tracer.py\n        benchmark.py · cost_optimizer.py\nRead: telemetry endpoint"]
    end
```

---

## 9. Knowledge Graph — 7-Tier Hierarchy

```mermaid
flowchart TD
    T1["Tier 1 · PAPER\n#F59E0B amber\nRoot node — one per paper"]
    T2["Tier 2 · SECTION\n#6B7280 gray\nAbstract · Introduction · Methods · Results …"]
    T3["Tier 3 · CONCEPT\n#8B5CF6 purple\nAttention · Residual · Self-Supervised …"]
    T4["Tier 4 · COMPONENT\n#3B82F6 blue\nTransformerBlock · FeedForward · Encoder …"]
    T5["Tier 5 · PARAMETER\n#10B981 green\nbatch_size=32 · lr=3e-4 · d_model=768 …"]
    T6["Tier 6 · DEPENDENCY\n#F97316 orange\nComponent → Component relationships"]
    T7["Tier 7 · IMPLEMENTATION\n#EC4899 pink\nPyTorch class/function bindings"]

    T1 --> T2 --> T3 --> T4 --> T5
    T4 --> T6
    T4 --> T7

    subgraph Capabilities
        C1["Topological sort → build order"]
        C2["Evidence tracing → Parameter → Paper"]
        C3["Arch visualization → React Flow / D3"]
        C4["Consistency checks → orphan detection · cycle check"]
        C5["Bidirectional shortest-path queries"]
    end
```

---

## 10. File Reference

| File | Role |
|---|---|
| `core/model_router.py` | Multi-provider dispatch + 3-step Groq failover chain |
| `core/quota_tracker.py` | `QuotaTracker` (LLM limits) + `DailyQuotaManager` (VLM budget) |
| `core/job_store.py` | SQLite WAL job state machine + event log + stale recovery |
| `core/events.py` | `EventTypes` constants, progress map, mascot map, emitters |
| `core/code_verifier.py` | 3-layer / 12-rung verification ladder + sandbox executor |
| `core/dual_code_engine.py` | Parallel Gemini + HF Qwen code synthesis with AST validation |
| `core/database.py` | `ChatDatabase` facade over 4 JSON flat-file repositories |
| `core/cost_optimizer.py` | SHA-256 ingestion cache, prompt cache, token budgeting |
| `core/limits_dashboard.py` | HTML quota UI + `get_limits_json_payload()` |
| `core/dag_validator.py` | Topological sort, cycle detection, orphan check |
| `core/manifest.py` | Build manifest + SHA-256 file hashing |
| `core/tracer.py` | Append-only execution trace logger |
| `core/prompts.py` | All system/user prompt templates (centralized) |
| `core/config.py` | Settings singleton, directory auto-creation, API key gates |
| `core/security.py` | JWT creation/verification |
| `api/v1/api_router.py` | Aggregates all 7 sub-routers |
| `api/v1/endpoints/papers.py` | Paper upload, dedup, canonical, PDF stream |
| `api/v1/endpoints/pipeline.py` | Job orchestration, SSE stream |
| `api/v1/endpoints/chat.py` | Conversations CRUD, message dispatch, SSE chat |
| `api/v1/endpoints/models.py` | Model listing, live limits JSON |
| `api/v1/endpoints/auth.py` | JWT auth, profile, API key management |
| `api/v1/endpoints/hardware.py` | GPU/CPU probe |
| `api/v1/endpoints/telemetry.py` | Benchmark, cost, extraction, eval reports |
| `providers/groq_adapter.py` | Groq LPU REST client + header-based quota extraction |
| `providers/openrouter_adapter.py` | OpenRouter free-tier client |
| `providers/hf_adapter.py` | HF Serverless Inference Router client |
| `providers/ollama_adapter.py` | Local Ollama client + model discovery |
| `retrieval/knowledge_graph.py` | 7-tier NetworkX DiGraph + save/load/query |
