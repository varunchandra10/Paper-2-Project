# 📖 Complete Backend Reference Guide — RUEXIS AI v2.0

This document provides a complete technical breakdown of every module in `backend/app/`, organized into three sections:

1. **SECTION 1 — File-by-File Explanation** (every `.py` file in the backend)
2. **SECTION 2 — Flow-Based Pipeline Breakdown** (sequential execution flows)
3. **SECTION 3 — Input/Output Specifications per Component**

---

# SECTION 1: File-by-File Explanation

---

## 📁 Root (`app/`)

### `app/__init__.py`
Marks `app` as a Python package. Exports `__version__ = "2.0.0"`.

---

## 📁 Core Infrastructure (`app/core/`)

### `app/core/config.py`
**Central settings singleton.** Reads all environment variables from `.env` via `python-dotenv`. Defines:
- **Directory paths** — `STORAGE_DIR`, `PAPERS_DIR`, `HISTORY_DIR`, `REPORTS_DIR`, `EXTRACTED_JSON_DIR`, `KNOWLEDGE_GRAPHS_DIR`, `RAG_EMBEDDINGS_DIR`, `TRACES_DIR`, `CONVERSATIONS_DIR`, `CODES_DIR`
- **Provider availability checks** — `has_groq()`, `has_openrouter()`, `has_gemini()`, `has_huggingface()`, `has_tavily()`
- **Hot-reload** — `_reload_env()` re-reads `.env` from disk; used by `GEMINI_API_KEY` and `HUGGINGFACE_API_KEY` properties on first access
- **`ensure_directories()`** — Creates all storage subdirectories on startup
- **`SECRET_KEY`** — Raises `RuntimeError` if unset, preventing silent auth failures

### `app/core/database.py`
**Flat-file JSON database engine (`ChatDatabase`).** All persistence is plain JSON files — no external DB.
- **Conversations** — Stored as `storage/conversations/{conv_id}.json`; each file contains `{title, project_id, messages: []}`
- **Active conversation** — Tracked in `storage/conversations/_active.json`
- **User profile** — Stored in `storage/user_profile.json` (username, email, API keys, Ollama link, mascot selection)
- **Document metadata** — Paper ingestion records in `storage/history/`
- **Deduplication** — `get_paper_by_hash(md5)` checks if a file was already ingested
- **User facts/memory** — `save_memory_fact()`, `get_user_facts()` for episodic memory persistence

### `app/core/model_router.py`
**Dynamic LLM provider router.** Dispatches inference to one of four adapters based on model ID prefix and quota state.
- **Groq** — IDs containing `qwen3`, `gpt-oss`, `groq`
- **OpenRouter** — IDs containing `gemini`, `deepseek`, `openrouter`
- **Ollama** — IDs containing `ollama`, or any locally installed model name
- **HuggingFace** — Backend-exclusive; called directly by `dual_code_engine.py`
- **`get_user_api_keys()`** — Reads private Groq/OR keys from `user_profile.json` (set in Profile page) as override
- **`generate(prompt, model_id)`** — Returns `(response_text, model_name_used)` tuple; model_name_used reflects actual provider after failover

### `app/core/quota_tracker.py`
**Rolling usage window tracker for all providers.** Maintains in-memory counters with timestamps.
- **Windows** — 1-minute, 60-minute, and 24-hour rolling windows
- **`record_usage(provider, model, tokens)`** — Called by every inference path including failover branches
- **`get_limits_summary()`** — Returns current usage vs limit per provider for dashboard rendering
- **Provider coverage** — Separate counters for Groq, OpenRouter, Gemini, HuggingFace

### `app/core/dual_code_engine.py`
**Parallel async code synthesis engine.** Runs two specialized models concurrently.
- **Engine A** — `Qwen/Qwen2.5-Coder-32B-Instruct` via HuggingFace (idiomatic PyTorch specialist)
- **Engine B** — `gemini-2.5-flash` via Gemini REST API (paper context + mathematical precision)
- **`extract_python_code(raw)`** — Strips markdown fences from raw LLM output
- **`validate_code_syntax(code)`** — `ast.parse()` + security blocklist check (`os.system`, `eval`, `exec`, `subprocess.run`, `__import__`)
- **Merge logic** — Both engines run via `asyncio.gather`; syntactically valid + higher-quality output wins; fallback to either engine if one fails

### `app/core/code_verifier.py`
**Post-generation code verification.** Additional semantic checks beyond AST syntax.
- Verifies required PyTorch imports are present
- Checks for class/function structure completeness
- Returns `(is_valid: bool, issues: List[str])` for the pipeline report

### `app/core/prompts.py`
**Central prompt library.** All system and user prompts are defined here — no inline strings in agent files.
- `CODE_SYNTHESIS_SYSTEM_PROMPT` — System role for Dual Code Engine
- `build_code_synthesis_user_prompt(paper_json, hyperparams, milestones)` — User turn for code synthesis
- Additional prompts for each pipeline agent (decomposition, feasibility, sequencing, specification, report)

### `app/core/constants.py`
**Shared string/URL constants** used across adapters, router, and dual engine.
- `GROQ_DEFAULT_MODEL`, `GROQ_SECONDARY_MODEL`
- `OPENROUTER_PDF_MODEL`, `OPENROUTER_REASONING_MODEL`
- `GEMINI_BASE_URL`, `BACKEND_GEMINI_MODEL`, `BACKEND_HF_CODER_MODEL`
- `OLLAMA_DEFAULT_HOST`

### `app/core/limits_dashboard.py`
**HTML/JSON rate limits dashboard generator.**
- `generate_limits_html_dashboard()` — Returns styled HTML page with live quota usage; served at `GET /limits-dashboard`
- `get_limits_json_payload()` — Returns machine-readable quota dict for `GET /models/limits`

### `app/core/history_logger.py`
**Simple conversation append logger.** Appends `{role, content, timestamp}` entries to conversation JSON files.

### `app/core/security.py`
**JWT authentication helper.** `create_access_token()` + `decode_access_token()` using `python-jose` with HS256.

### `app/core/tracer.py`
**Agent execution tracer (`AgentTracer`).** Logs pipeline node execution times, model used, and success/failure to `storage/traces/`.

---

## 📁 Provider Adapters (`app/providers/`)

### `app/providers/__init__.py`
Exports all four adapter modules for clean import in `model_router.py`.

### `app/providers/groq_adapter.py`
**Groq LPU inference adapter.**
- POST to `https://api.groq.com/openai/v1/chat/completions` with OpenAI-compatible payload
- Handles streaming and non-streaming modes
- Returns `(response_text, "groq/<model_id>")` on success; raises on 429 for router failover

### `app/providers/openrouter_adapter.py`
**OpenRouter multi-model adapter.**
- POST to `https://openrouter.ai/api/v1/chat/completions`
- Adds required `HTTP-Referer` and `X-Title` headers
- Supports both free and paid models via same interface

### `app/providers/hf_adapter.py`
**Hugging Face Serverless Inference Router adapter.**
- POST to `https://router.huggingface.co/hf-inference/models/{model}/v1/chat/completions`
- Dedicated to `Qwen/Qwen2.5-Coder-32B-Instruct` for Dual Code Engine
- Not exposed in frontend model selector — backend-exclusive

### `app/providers/ollama_adapter.py`
**Local Ollama REST adapter.**
- `generate(prompt, model, host)` — POST to `{host}/api/generate`
- `get_available_models(hosts)` — Probes `/api/tags` on each candidate host for installed model list
- Supports multi-host probing (`OLLAMA_HOST` env + user profile `ollamaLink`)

---

## 📁 Data Schemas (`app/schemas/`)

### `app/schemas/chat.py`
- `ChatMessageRequest` — `{message, paper_id, model_name}`; `get_query_text()` normalizes the content field
- `UserFactRequest` — `{fact_text}` for episodic memory writes

### `app/schemas/pipeline.py`
- `ParameterApprovalRequest` — User approval/rejection payload for pipeline step review
- `PipelineState` (in `app/graph/state.py`) — Shared mutable state dict across all LangGraph nodes

---

## 📁 PDF Extraction (`app/extraction/`)

### `app/extraction/pdf_parser.py`
**Extraction entry point.** Calls `router.py` to pick the right parser and returns canonical JSON.

### `app/extraction/router.py`
**Parser selection logic.** Chooses between Docling, PyMuPDF, GROBID, and Gemini based on `EXTRACTION_PROVIDER` setting and file characteristics.

### `app/extraction/docling_parser.py`
**Primary parser.** Uses Docling for structure-aware extraction of sections, tables, equations, and figures.

### `app/extraction/pymupdf_parser.py`
**Fallback parser.** Uses PyMuPDF (`fitz`) for coordinate-based layout extraction when Docling fails.

### `app/extraction/openrouter_parser.py`
**Cloud parser.** Sends PDF pages to `gemini-2.5-flash` via OpenRouter/Gemini for extraction of complex scientific layouts.

### `app/extraction/grobid_parser.py`
**GROBID TEI XML parser.** Parses scholarly metadata (authors, references, equations) from GROBID's TEI XML response when running at `localhost:8070`.

### `app/extraction/grobid_client.py`
**GROBID HTTP client.** POSTs PDF bytes to GROBID `/api/processFulltextDocument`.

### `app/extraction/merger.py`
**Multi-parser output reconciler.** Merges and deduplicates section content from multiple parsers into a canonical JSON with resolved sections, figures, tables, and equations. Largest/most-complete extraction wins per section.

### `app/extraction/block_extractor.py`
**Block classifier.** Segregates raw text into paragraphs, equations, table cells, and figure captions using layout heuristics.

### `app/extraction/section_detector.py`
**Section header detector.** Pattern-matches common academic section headings (Abstract, Introduction, Method, Experiments, Conclusion, References) across varied formatting styles.

### `app/extraction/pdf_inspector.py`
**PDF metadata inspector.** Quick pre-check for page count, file size, and layout complexity before choosing parser.

### `app/extraction/validator.py`
**Extraction quality validator.** Scores canonical JSON completeness and returns `QA_PASS` / `QA_PARTIAL` / `QA_FAIL`.

### `app/extraction/constants.py`
Shared regex patterns and section name normalizations.

---

## 📁 Retrieval Layer (`app/retrieval/`)

### `app/retrieval/chunker.py`
**Semantic text chunker.** Splits paper text into overlapping chunks (~500 tokens) at paragraph boundaries. Equations and tables are preserved as atomic (non-split) units.

### `app/retrieval/embeddings.py`
**Embedding generator.** Produces dense float vectors for text chunks using `sentence-transformers`. Used for FAISS indexing and cosine similarity search.

### `app/retrieval/vector_db.py`
**FAISS-based per-paper vector index (`PaperVectorDB`).**
- `index_paper(paper_id, chunks)` — Embeds chunks and saves FAISS index + metadata to `storage/rag_embeddings/`
- `search(paper_id, query, top_k)` — Returns top-k most similar chunks with similarity scores
- Index is loaded lazily per paper_id and cached in memory

### `app/retrieval/knowledge_graph.py`
**NetworkX knowledge graph per paper (`PaperKnowledgeGraph`).**
- Nodes: methods, datasets, metrics, hyperparameters, model components, citations
- Edges: `uses`, `evaluates_on`, `compared_with`, `optimizes`, `measures`
- `build_graph(paper_json)` — Extracts entities and relationships from canonical JSON
- `search_entities(query)` — Returns matching nodes and their neighbor context
- Persisted to `storage/knowledge_graphs/{paper_id}_kg.json`

---

## 📁 Agents (`app/agents/`)

### `app/agents/chat_agent.py`
**Core ReACT conversational agent (`ChatAgent`).**
- `process_message(conversation_id, query, paper_id, model_name)` — Non-streaming ReACT loop
- `process_message_stream(...)` — Async generator yielding SSE-formatted chunks
- Modularized into sub-components: `react_utils.py`, `smart_titler.py`, `context_builder.py`
- Max 5 ReACT turns per request
- On `Final Answer:` extraction, saves assistant message to `ChatDatabase`

### `app/agents/chat/react_utils.py`
- `is_code_request(query)` — Detects if user is asking for PyTorch code (routes to DualCodeEngine)
- `clean_react_content(text)` — Strips ReACT scaffolding from final answer
- `parse_react_traces(text)` — Extracts THOUGHT, ACTION, OBSERVATION from raw LLM output

### `app/agents/chat/context_builder.py`
- `build_context_prompt(db, tools, conversation_id, query, paper_id)` — Assembles full LLM prompt from: system instructions, available tools list, user facts, extracted hyperparameters, episodic memory, last N messages
- `resolve_active_paper_id(db, conversation_id, paper_id)` — Resolves which paper the conversation is about

### `app/agents/chat/smart_titler.py`
- `generate_smart_title(query, paper_id, answer_snippet, current_title)` — Rule-based + LLM title generator producing 3–5 word conversation titles

### `app/agents/ingestion_agent.py`
**LangGraph node: ingestion_node.** Loads canonical paper JSON into `PipelineState` from disk.

### `app/agents/parameter_agent.py`
**LangGraph node: extraction_node.** Extracts ML hyperparameters from paper sections using structured LLM prompting. Returns `ExtractedParameters` with provenance annotations.

### `app/agents/feasibility_agent.py`
**LangGraph node: feasibility_node.** Queries hardware metrics and scores model memory footprint vs available VRAM. Produces `FeasibilityReport`.

### `app/agents/gap_agent.py`
**Gap resolver for missing/ambiguous parameters.** Called within the extraction node pipeline to apply fallback heuristics (reduce batch size, add gradient accumulation, use mixed precision).

### `app/agents/sequencing_agent.py`
**LangGraph node: sequencing_node.** Generates `BuildSequence` — an ordered 6-milestone implementation DAG.

### `app/agents/specification_agent.py`
**Technical specification generator.** Synthesizes `ProjectSpecification` (architecture details, data loader plan, loss functions, scaled hyperparameters).

### `app/agents/report_agent.py`
**Adaptation report generator.** Produces a Markdown portfolio-grade executive report combining feasibility, specification, and milestones.

### `app/agents/code_gen_agent.py`
**LangGraph node: verification_node.** Orchestrates DualCodeEngine call, collects synthesized code, saves to `storage/codes/{paper_id}/`, and records AST verification result.

### `app/agents/decomposition_agent.py`
**Method decomposition agent.** Analyzes method sections to infer `ComponentGraph` (encoders, attention layers, fusion modules, decoders, loss functions).

---

## 📁 ReACT Tools (`app/tools/`)

### `app/tools/__init__.py`
**Tool registry.** `get_all_tools()` returns the full list of instantiated tool objects used by `ChatAgent`.

### `app/tools/base_tool.py`
**Abstract base class.** Defines `name`, `description`, and `execute(query, **kwargs)` interface for all tools.

### `app/tools/arxiv_search_tool.py`
**arXiv academic paper search.** Queries `http://export.arxiv.org/api/query` and returns top results with title, abstract, authors, URL.

### `app/tools/scholar_search_tool.py`
**Google Scholar search via Tavily API.** Returns academic search results for research-grade queries.

### `app/tools/vector_search_tool.py`
**FAISS vector similarity search.** Searches the uploaded paper's FAISS index for semantically similar passages. Returns top-k chunks with scores.

### `app/tools/graph_search_tool.py`
**NetworkX knowledge graph search.** Finds entities and their neighbors matching a query term in the paper's knowledge graph.

### `app/tools/canonical_document_tool.py`
**Full paper JSON retrieval.** Returns the complete structured canonical JSON (sections, figures, tables, equations) for the active paper from `storage/extracted_json/`.

### `app/tools/hyperparameter_tool.py`
**Hyperparameter retrieval.** Loads and returns the extracted ML hyperparameters from `storage/history/{paper_id}_params.json`.

### `app/tools/episodic_memory_tool.py`
**Episodic memory search.** Searches past conversation memory facts stored in `ChatDatabase` for context relevant to the current query.

---

## 📁 LangGraph Pipeline (`app/graph/`)

### `app/graph/state.py`
**Shared pipeline state.** `PipelineState` TypedDict carries all data between nodes: `paper_id`, `paper_json`, `hyperparameters`, `feasibility_report`, `build_sequence`, `generated_code`, `errors`.

### `app/graph/workflow.py`
**StateGraph compiler.** Builds and compiles the 5-node pipeline:
```
START → ingestion_node → extraction_node → feasibility_node → sequencing_node → verification_node → END
```

### `app/graph/nodes/`
Individual node wrapper functions that call agent methods and update `PipelineState`.

---

## 📁 API Endpoints (`app/api/v1/endpoints/`)

### `app/api/v1/api_router.py`
**Router aggregator.** Includes all 7 endpoint routers under `/api/v1`.

### `app/api/v1/endpoints/auth.py`
- `POST /auth/local-login` — Register or authenticate local user profile; returns JWT

### `app/api/v1/endpoints/chat.py`
- Full conversation CRUD (GET, POST, PATCH, DELETE)
- `POST /conversations/{id}/chat` — Non-streaming ReACT completion
- `POST /conversations/{id}/chat/stream` — SSE streaming (primary path)
- `GET|POST /memory` — Episodic memory read/write

### `app/api/v1/endpoints/papers.py`
- `POST /upload` — PDF/DOCX upload with MD5 deduplication → extraction → FAISS indexing
- `GET /history` — List all ingested papers
- `GET /history/{paper_id}/hyperparameters` — Extracted hyperparameters
- `GET /papers/{paper_id}/pdf` — Serve raw PDF for viewer
- `DELETE /history/{paper_id}` — Full paper data deletion
- `GET|PATCH /profile` — User profile CRUD

### `app/api/v1/endpoints/pipeline.py`
- `POST /pipeline/ingest` — Trigger LangGraph pipeline (background `threading.Thread`)
- `POST /pipeline/approve` — Submit parameter approval
- `GET /stream/{run_id}` — SSE stream for live logs + mascot state signals
- `GET /pipeline/status/{run_id}` — Job status check
- `GET /pipeline/report/{paper_id}` — Final report retrieval

### `app/api/v1/endpoints/models.py`
- `GET /models` — Provider groups: Groq (2 models) + OpenRouter (2 models) + Local Ollama (if available)
- `GET /models/limits` — Live quota metrics
- `GET /models/dual-engine` — Dual Code Engine availability status

### `app/api/v1/endpoints/hardware.py`
- `GET /hardware/metrics` — CPU (psutil), GPU (nvidia-smi → PyTorch fallback)

### `app/api/v1/endpoints/telemetry.py`
- `GET /telemetry/traces` — Agent execution trace retrieval

---

# SECTION 2: Flow-Based Pipeline Breakdown

---

## Flow A — PDF Upload & RAG Indexing

```
POST /upload (multipart PDF)
    │
    ├─ MD5 hash check → if duplicate: return existing paper_id
    │
    ├─ Save to storage/papers/{paper_id}.pdf
    │
    ├─ parse_pdf_document()
    │    └─ router.py selects: Docling → PyMuPDF → Gemini
    │    └─ merger.py reconciles multi-parser outputs
    │    └─ validator.py scores completeness
    │
    ├─ chunk_paper_document() → embed → FAISS index
    │    └─ saved: storage/rag_embeddings/{paper_id}/
    │
    ├─ PaperKnowledgeGraph.build_graph()
    │    └─ saved: storage/knowledge_graphs/{paper_id}_kg.json
    │
    ├─ ChatDatabase.save_paper_metadata()
    │
    └─ Return: {paper_id, conversation_id, title, limits}
```

---

## Flow B — LangGraph Autonomous Pipeline

```
POST /pipeline/ingest {paper_id, model_name}
    │
    ├─ Create job_id, set status → "queued"
    │
    └─ threading.Thread: run_pipeline_task()
           │
           ├─ app_workflow.invoke(PipelineState)
           │    │
           │    ├─ ingestion_node    → load paper JSON
           │    ├─ extraction_node   → ParameterAgent → hyperparameters
           │    ├─ feasibility_node  → FeasibilityAgent → VRAM score
           │    ├─ sequencing_node   → SequencingAgent → BuildSequence
           │    └─ verification_node → CodeGenAgent → DualCodeEngine
           │         ├─ Engine A: HF Qwen 2.5 Coder 32B (async)
           │         ├─ Engine B: Gemini 2.5 Flash (async)
           │         ├─ validate_code_syntax() → AST + security check
           │         └─ save: storage/codes/{paper_id}/
           │
           └─ set status → "completed" / "failed"

GET /stream/{run_id}   ← SSE: log + mascot-state events
```

---

## Flow C — Streaming Chat (Primary Path)

```
POST /conversations/{id}/chat/stream {message, paper_id, model_name}
    │
    ├─ db.set_active_conversation_id(id)
    │
    └─ chat_agent.process_message_stream()
           │
           ├─ context_builder.build_context_prompt()
           │    └─ user facts + hyperparams + episodic memory + chat history
           │
           ├─ model_router.generate(prompt, model_id)
           │    └─ Groq → OpenRouter → Ollama (quota-aware failover)
           │
           ├─ ReACT Loop (max 5 turns):
           │    ├─ yield SSE: event: thought   data: <THOUGHT>
           │    ├─ yield SSE: event: action    data: <TOOL_NAME>
           │    ├─ tool_executor.execute(tool_name, args)
           │    └─ yield SSE: event: observation data: <RESULT>
           │
           ├─ yield SSE: event: token   data: <word>  (per token)
           │
           ├─ yield SSE: event: done    data: {title, model_used, failover_model, ...}
           │
           └─ db.save_message(conversation_id, role="assistant", content=answer)
```

---

## Flow D — Model Failover Chain

```
model_router.generate(prompt, model_id="qwen/qwen3.8-27b")
    │
    ├─ Try Groq: POST api.groq.com
    │    ├─ 200 → return (text, "groq/qwen3.8-27b")
    │    └─ 429 → quota_tracker.record_failure("groq")
    │
    ├─ Try OpenRouter: POST openrouter.ai
    │    ├─ 200 → return (text, "openrouter/google/gemini-2.5-flash") ← failover_model
    │    └─ 429 → try next
    │
    └─ Try Ollama: POST localhost:11434
         └─ 200 → return (text, "ollama/<model>")
```

---

# SECTION 3: Input/Output Specifications

---

## `parse_pdf_document(file_path)`
- **Input:** Absolute path to a PDF or DOCX file
- **Output:** `dict` — canonical paper JSON `{title, authors, abstract, sections: [{title, content, subsections}], figures, tables, equations, raw_full_text}`

## `ChatAgent.process_message_stream(conversation_id, query, paper_id, model_name)`
- **Input:** `str` conv ID, `str` query, optional `str` paper ID, optional `str` model name
- **Output:** `AsyncGenerator[str, None]` — SSE-formatted strings (`event: X\ndata: Y\n\n`)

## `ModelRouter.generate(prompt, model_id)`
- **Input:** `str` prompt, optional `str` model_id
- **Output:** `Tuple[str, str]` — `(response_text, model_name_used)`

## `dual_code_engine.synthesize(paper_json, hyperparams, milestones)`
- **Input:** paper JSON dict, hyperparameters dict, BuildSequence milestones list
- **Output:** `Dict[str, Any]` — `{code: str, engine_used: str, is_valid: bool, issues: List[str]}`

## `PaperVectorDB.search(paper_id, query, top_k=3)`
- **Input:** `str` paper_id, `str` query, `int` top_k
- **Output:** `List[Dict]` — `[{text: str, chunk_index: int, score: float}]`

## `PaperKnowledgeGraph.search_entities(query)`
- **Input:** `str` query term
- **Output:** `List[Dict]` — matching nodes with `{id, type, label, neighbors: [...]}`

## `GET /hardware/metrics`
- **Output:**
```json
{
  "status": "online",
  "cpu": {"platform": "Windows", "cores": 16, "usage_percent": 12.3, "ram_total_gb": 23.6, "ram_used_gb": 8.1, "ram_available_gb": 15.5},
  "gpu": {"cuda_available": true, "name": "NVIDIA GeForce RTX 5050", "vram_total_gb": 8.0, "vram_used_gb": 0.5, "vram_free_gb": 7.5}
}
```

## `GET /models`
- **Output:**
```json
{
  "default_model": "qwen/qwen3.8-27b",
  "groups": {
    "groq": {"models": [{"id": "qwen/qwen3.8-27b", ...}, {"id": "openai/gpt-oss-120b", ...}]},
    "openrouter": {"models": [{"id": "google/gemini-2.5-flash", ...}, {"id": "deepseek/deepseek-r1:free", ...}]},
    "local": {"models": [...installed ollama models...]}
  }
}
```

## `POST /upload` (multipart)
- **Input:** `file` (PDF/DOCX binary), optional `model_name`
- **Output:**
```json
{
  "paper_id": "paper_attention_is_all_you",
  "conversation_id": "conv_a1b2c3d4",
  "title": "Attention Is All You Need",
  "duplicate": false,
  "limits": {...quota summary...}
}
```

## `POST /conversations/{id}/chat` (non-streaming)
- **Input:** `{message: str, paper_id: str, model_name: str}`
- **Output:** `{answer: str, model_used: str, failover_model: str|null, thought: str, action: str, observation: str, title: str}`

## `GET /models/limits`
- **Output:**
```json
{
  "groq": {"rpm_used": 12, "rpm_limit": 30, "rpd_used": 156, "rpd_limit": 14400},
  "openrouter": {"rpm_used": 3, "rpm_limit": 20, "rpd_used": 47, "rpd_limit": 200},
  "local": {"available": true, "host": "http://localhost:11434"}
}
```
