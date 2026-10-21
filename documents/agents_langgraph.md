# Agents & LangGraph Orchestration — RUEXIS AI

> Covers `backend/app/graph/` (StateGraph), `backend/app/graph/nodes/` (9 node wrappers),  
> and `backend/app/agents/` (11 standalone agent functions + ChatAgent).

---

## 1. Two Separate Execution Paths

There are **two completely independent agent systems** in this backend. They don't share a runtime:

```mermaid
flowchart LR
    subgraph A["Pipeline Mode\n(POST /pipeline/run)"]
        L["LangGraph StateGraph\n9 nodes · 2 self-correcting loops"]
    end

    subgraph B["Chat Mode\n(POST /chat/message)"]
        R["ReACT ChatAgent\nMulti-turn · Max 3 tool turns"]
    end

    PDF([Uploaded PDF]) --> A
    Query([User Query]) --> B
    A --> Code([Generated PyTorch Code])
    B --> Answer([Research Answer / Code])
```

---

## 2. LangGraph Pipeline — Full Topology

```mermaid
stateDiagram-v2
    [*] --> ingestion_node
    ingestion_node --> extraction_node
    extraction_node --> feasibility_node

    feasibility_node --> adaptation_node : INFEASIBLE\n+ retries left
    adaptation_node --> feasibility_node : re-evaluate

    feasibility_node --> sequencing_node : FEASIBLE\nor retries exhausted

    sequencing_node --> specification_node
    specification_node --> code_generation_node
    code_generation_node --> evaluation_node

    evaluation_node --> code_repair_node : FAILED\n+ retries left
    code_repair_node --> evaluation_node : re-evaluate

    evaluation_node --> [*] : PASSED\nor retries exhausted
```

**Bounded loops:**
- Feasibility refinement: `max_feasibility_retries = 2`
- Code repair: `max_repair_retries = 2`

---

## 3. Telemetry Wrapper — Every Node

Every single node is wrapped by `wrap_node_with_telemetry()` before being registered in the graph. This is transparent to the node code itself.

```mermaid
flowchart TD
    Call([Node called by LangGraph]) --> E1["emit NODE_STARTED event\n+ timestamp to SQLite"]
    E1 --> Exec["Execute actual node function\n(ingestion / extraction / etc)"]
    Exec -->|Success| E2["emit NODE_COMPLETED event\n+ duration_ms"]
    Exec -->|Exception| E3["emit NODE_ERROR event\n+ duration_ms\nRe-raise exception"]
    E2 --> Domain{Domain event\nneeded?}
    Domain -->|adaptation_node| RE["emit REFINEMENT\n(loop count, reason)"]
    Domain -->|code_repair_node| RY["emit RETRY\n(loop count, error summary)"]
    Domain -->|evaluation_node failed| ER["emit NODE_ERROR\n(layer1/layer3 detail)"]
    Domain -->|other| Done([Return result to graph])
    RE & RY & ER --> Done
```

Events are consumed by the `GET /pipeline/jobs/{run_id}/events` **SSE stream** on the frontend.

---

## 4. Node-by-Node Breakdown

### 4.1 `ingestion_node` → `ingestion_agent.py`

```mermaid
flowchart TD
    A([pdf_path from state]) --> SZ{File size\n0B or >50MB?}
    SZ -->|Yes| ERR([Raise ValueError])
    SZ -->|No| H[compute_file_sha256]
    H --> C{cost_optimizer\ncache hit?}
    C -->|Yes| RET([Return cached paper_doc\nSkip all parsing])
    C -->|No| P1[parse_pdf_document\nExtraction pipeline]
    P1 --> P2[chunk_paper_document]
    P2 --> P3[generate_local_embeddings_batch]
    P3 --> P4[PaperVectorDB.insert_paper_document]
    P4 --> P5[run_ingestion_agent\n3-tier title · authors · abstract · sections]
    P5 --> P6[cost_optimizer.cache_paper_ingestion\nSave for future reuse]
    P6 --> Out([State: paper_doc · raw_sections · metadata])
```

> **Cache hit** saves ~1250ms and thousands of embedding tokens for unchanged PDFs.

---

### 4.2 `extraction_node` → `parameter_agent` + `decomposition_agent`

```mermaid
flowchart LR
    In([paper_doc · raw_sections]) --> PA["run_parameter_agent()\nQueries RAG + LLM\nExtracts hyperparameters\nwith provenance labels"]
    In --> DA["run_decomposition_agent()\nBuilds component_graph\nfrom raw sections"]
    PA --> Out([extracted_parameters])
    DA --> Out2([component_graph])
```

**Provenance levels for each extracted parameter:**

| Label | Meaning |
|---|---|
| `EXPLICIT` | Verbatim in paper text |
| `DERIVED` | Calculated from explicit values |
| `INFERRED` | Deduced from conventions |
| `ASSUMED` | ML default, paper silent |
| `UNKNOWN` | Not found (value = null) |

---

### 4.3 `feasibility_node` → `feasibility_agent.py`

```mermaid
flowchart TD
    In([component_graph · constraints · params]) --> FA["run_feasibility_agent()\nMathematical VRAM estimation\nEstimated vs Available VRAM"]
    FA --> S{overall_status}
    S --> F1[FEASIBLE]
    S --> F2[FEASIBLE_WITH_MODIFICATION]
    S --> F3[NOT_FEASIBLE]
    F1 & F2 & F3 --> HT[Append to history_trace]
    HT --> Out([feasibility_report])
```

> Caches result if `loop_count == 0` and no forced recompute.

---

### 4.4 `adaptation_node` — Rule Engine (no LLM)

```mermaid
flowchart TD
    In([feasibility_report · extracted_parameters]) --> S{overall_status}
    S -->|NOT_FEASIBLE| BS1["new_bs = current_bs ÷ 4"]
    S -->|FEASIBLE_WITH_MODIFICATION| BS2["new_bs = current_bs ÷ 2"]
    BS1 & BS2 --> UP["Update params.batch_size\nstatus = DERIVED\nevidence = adaptation rationale"]
    UP --> INC[feasibility_loop_count += 1]
    INC --> Out([updated params · incremented loop count])
```

> Pure deterministic rule engine — no LLM call needed.

---

### 4.5 `sequencing_node` → `sequencing_agent` + `report_agent` + DAG validation

```mermaid
flowchart TD
    In([component_graph · feasibility_report]) --> SA["run_sequencing_agent()\nOrders components by dependency"]
    SA --> BS[build_sequence\n.steps list]
    BS --> DAG["DAGValidator.validate(steps)\nCycle detection · orphan check\nTopological sort"]
    DAG -->|invalid| WARN["[WARN] Log DAG issues\n(non-blocking)"]
    DAG -->|valid| RA
    WARN --> RA["run_report_agent()\nSynthesizes build summary"]
    RA --> Out([build_sequence · report · history_trace])
```

---

### 4.6 `specification_node` — Deterministic (no LLM)

```mermaid
flowchart LR
    In([build_sequence · params · component_graph]) --> SP["Iterate build_sequence.steps\nBuild modules_spec list\n(module_name · description\n dependencies · estimated_loc)"]
    SP --> Out(["specification dict\ntarget_framework: PyTorch\nmodules: [...]\nparameters: {...}"])
```

---

### 4.7 `code_generation_node` → `code_gen_agent.py`

```mermaid
flowchart TD
    In([specification · params · component_graph]) --> SC{sample_code\nalready in state?}
    SC -->|Yes pre-set| Skip([Reuse existing code])
    SC -->|No| CGA["run_code_gen_agent()\nDual-Engine: Gemini + HF Qwen\nAST validation on both outputs\nBest result selected"]
    CGA --> Out([sample_code · history_trace])
```

---

### 4.8 `evaluation_node` → `code_verifier.py`

```mermaid
flowchart TD
    In([sample_code · extracted_parameters]) --> CV["code_verifier.evaluate_candidate()"]
    CV --> L1["Layer 1 — AST\nSyntax parse · stub detection\nSecurity primitives check"]
    CV --> L2["Layer 2 — Grounding\nHyperparameter compliance score\n(0.0 – 1.0)"]
    CV --> L3["Layer 3 — Execution\nSandboxed forward pass\nOutput shape check"]
    L1 & L2 & L3 --> R{All layers\nPASSED?}
    R -->|Yes| PASS([status: PASSED\nparameters_approved: True])
    R -->|No| FAIL([status: FAILED\nerror message captured])
```

---

### 4.9 `code_repair_node` — Reflexion Loop

```mermaid
flowchart TD
    In([sample_code · verification_result.error]) --> H1{Missing super().__init__\nin nn.Module?}
    H1 -->|Yes| FX["Heuristic fix:\nInject super().__init__()"]
    H1 -->|No| LLM["Reflexion repair via ModelRouter\nbuild_reflexion_repair_prompt()\ntemperature = 0.2"]
    LLM -->|Repair OK| EC["extract_python_code()\nClean markdown fences"]
    LLM -->|LLM fails| ANN["Annotate original code\n# [REPAIR ATTEMPT N FAILED]"]
    FX & EC & ANN --> INC[code_repair_loop_count += 1]
    INC --> Out([repaired sample_code])
```

---

## 5. PipelineState — Shared Data Bus

```mermaid
classDiagram
    class PipelineState {
        job_id: str
        paper_id: str
        pdf_path: str
        model_name: str
        constraints: dict
        raw_sections: dict
        paper_doc: PaperDocument
        component_graph: dict
        extracted_parameters: ExtractedParameters
        feasibility_report: FeasibilityReport
        feasibility_loop_count: int
        max_feasibility_retries: int
        build_sequence: BuildSequence
        specification: dict
        sample_code: str
        generated_code: dict
        verification_result: dict
        code_repair_loop_count: int
        max_repair_retries: int
        parameters_approved: bool
        report: dict
        history_trace: List~dict~
        execution_bounds: dict
        status: str
    }
```

Every node reads from and writes back to this single typed dict — no global state, no side channels.

---

## 6. ChatAgent — ReACT Multi-Turn Loop

```mermaid
flowchart TD
    Q([User Query]) --> CI{Code request\n+ Gemini/HF available?}

    CI -->|Yes| DE["DualCodeEngine\nGemini + HF Qwen parallel\nAST-validated"]
    DE --> SAVE([Save + Return])

    CI -->|No| CTX["build_context_prompt()\nHistory + hyperparams\n+ episodic memory"]
    CTX --> T1["Turn 1: ModelRouter.generate()\nparse THOUGHT / ACTION / OBSERVATION"]
    T1 --> AC{ACTION\ndetected?}

    AC -->|Yes + turn < 3| TL["tool_inst.execute(query, paper_id)\nAppend OBSERVATION to prompt"]
    TL --> T2["Turn 2: ModelRouter.generate()"]
    T2 --> AC2{ACTION\ndetected?}
    AC2 -->|Yes + turn < 3| TL2["Execute tool again"]
    TL2 --> T3["Turn 3: Final generate()"]
    AC2 -->|No| ANS

    T3 --> ANS{ANSWER:\nin response?}
    ANS -->|No| SYN["Synthesis pass:\nForce final ANSWER"]
    SYN --> FIN
    ANS -->|Yes| FIN["clean_react_content()\nSave to DB + episodic memory"]
    AC -->|No| FIN

    FIN --> TIT{Title\ngenerated?}
    TIT -->|No / placeholder| GT["generate_smart_title()\nOne-time only, never overwritten"]
    TIT -->|Already set| RET2([Return response])
    GT --> RET2
```

---

## 7. Tool Registry

```mermaid
flowchart LR
    subgraph Registry["tools/__init__.py — get_all_tools()"]
        T1["VectorSearchTool\nvector_search · search_paper\nsearch_chunks · paper_search"]
        T2["CanonicalDocumentTool\ncanonical_document · get_sections\nget_tables · get_equations · get_abstract"]
        T3["HyperparameterTool\nget_hyperparameters\napproved_parameters · get_params"]
        T4["KnowledgeGraphTool\nquery_knowledge_graph\ngraph_search · knowledge_graph"]
        T5["EpisodicMemoryTool\nquery_episodic_memory\nepisodic_memory"]
        T6["ArxivSearchTool\nsearch_arxiv · arxiv_search"]
        T7["ScholarSearchTool\nsearch_scholar · scholar_search"]
    end

    ChatAgent --> Registry
```

Each tool name has multiple **aliases** so the LLM can call it by any reasonable variation without failing.

---

## 8. Agent-to-Node Mapping

```mermaid
flowchart LR
    subgraph Nodes["LangGraph Nodes"]
        N1[ingestion_node]
        N2[extraction_node]
        N3[feasibility_node]
        N4[adaptation_node]
        N5[sequencing_node]
        N6[specification_node]
        N7[code_generation_node]
        N8[evaluation_node]
        N9[code_repair_node]
    end

    subgraph Agents["Standalone Agents / Services"]
        A1[ingestion_agent]
        A2[parameter_agent]
        A3[decomposition_agent]
        A4[feasibility_agent]
        A5["Rule engine\n(no LLM)"]
        A6[sequencing_agent]
        A7[report_agent]
        A8["specification_node\n(deterministic)"]
        A9[code_gen_agent\nDualCodeEngine]
        A10[code_verifier\n3-layer ladder]
        A11[ModelRouter\n+ reflexion prompt]
    end

    N1 --> A1
    N2 --> A2 & A3
    N3 --> A4
    N4 --> A5
    N5 --> A6 & A7
    N6 --> A8
    N7 --> A9
    N8 --> A10
    N9 --> A11
```

---

## 9. File Reference

| File | Role |
|---|---|
| `graph/workflow.py` | StateGraph build, telemetry wrapping, route functions |
| `graph/state.py` | `PipelineState` TypedDict |
| `graph/nodes/ingestion.py` | File validation, SHA-256 cache, parse + embed |
| `graph/nodes/extraction.py` | Delegates to `parameter_agent` + `decomposition_agent` |
| `graph/nodes/feasibility.py` | Delegates to `feasibility_agent`, history append |
| `graph/nodes/adaptation.py` | Rule-based batch size scaling, loop counter |
| `graph/nodes/sequencing.py` | DAG sequencing + validation + report synthesis |
| `graph/nodes/specification.py` | Deterministic spec dict from build sequence |
| `graph/nodes/code_generation.py` | Delegates to `code_gen_agent` / dual engine |
| `graph/nodes/evaluation.py` | Delegates to `code_verifier` 3-layer ladder |
| `graph/nodes/repair.py` | Heuristic fix → Reflexion LLM repair |
| `agents/chat_agent.py` | ReACT loop, dual-engine intercept, title generation |
| `agents/ingestion_agent.py` | 3-tier title/author/abstract/section extraction |
| `agents/parameter_agent.py` | Provenance-aware hyperparameter extraction |
| `agents/decomposition_agent.py` | Component graph building |
| `agents/feasibility_agent.py` | VRAM feasibility math |
| `agents/sequencing_agent.py` | Dependency-ordered build plan |
| `agents/report_agent.py` | Final report synthesis |
| `agents/code_gen_agent.py` | Dual-engine code synthesis invocation |
| `core/code_verifier.py` | 3-layer / 12-rung verification ladder |
| `core/dual_code_engine.py` | Gemini + HF Qwen parallel code engine |
| `core/dag_validator.py` | Topological sort, cycle detection |
| `core/events.py` | Typed event emitters + progress map + mascot map |
