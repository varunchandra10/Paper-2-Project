# RUEXIS AI — Backend (v2.0)

FastAPI backend for the RUEXIS AI Platform. Provides multi-engine document extraction, an autonomous 5-node LangGraph agent swarm, Dual Code Synthesis (Qwen + Gemini), a 12-rung verification ladder, and real-time SSE streaming.

> 📘 **Master Documentation:** For in-depth architectural textbook chapters, refer to the [Master Documentation Index](../documents/README.md) and [Backend Operational Commands](../documents/backend_commands.md).

---

## Quick Start

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1       # Windows PowerShell
# source venv/bin/activate      # macOS/Linux

# 2. Install runtime dependencies (and test dependencies if running tests)
pip install -r requirements.txt
pip install pytest pytest-asyncio  # Dev/testing

# 3. Configure environment variables
Copy-Item .env.example .env     # Windows PowerShell (or: copy .env.example .env)
# Fill in: GROQ_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY, HUGGINGFACE_API_KEY, TAVILY_API_KEY, SECRET_KEY

# 4. Start the backend server
python main.py
# Or directly with uvicorn:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server runs at **http://localhost:8000**
- Interactive Swagger API docs: `http://localhost:8000/docs`
- ReDoc API docs: `http://localhost:8000/redoc`
- Rate Limits & Quotas Dashboard: `http://localhost:8000/limits-dashboard`
- JSON Health Check: `http://localhost:8000/api/status`

---

## Directory Structure

```
backend/
├── main.py                   # FastAPI app, CORS middleware, startup recovery, root routes
├── requirements.txt          # Minimal pinned dependencies
├── pytest.ini                # Pytest configuration (asyncio_mode=auto, testpaths=tests)
├── .env.example              # Environment variable template
├── storage/                  # Runtime state & indices (git-ignored)
│   ├── papers/               # Raw uploaded PDF files
│   ├── conversations/        # Per-conversation JSON message threads
│   ├── history/              # User profile & document metadata
│   ├── rag_embeddings/       # Vector indices per paper
│   ├── codes/                # Generated code caches
│   └── jobs.db               # SQLite WAL autonomous job state machine
├── reports/                  # User deliverables & audit artifacts
│   ├── extracted_json/       # Canonical structured extraction JSON per paper
│   ├── knowledge_graphs/     # Built NetworkX 7-tier knowledge graphs
│   ├── manifests/            # Autonomous run manifests
│   ├── traces/               # Telemetry execution trace logs
│   ├── benchmarks/           # Performance benchmark reports
│   └── evaluation/           # RAG and code synthesis evaluation logs
├── tests/                    # 31-file automated pytest test suite
└── app/
    ├── api/v1/               # HTTP endpoint routers (auth, papers, pipeline, chat, etc.)
    ├── agents/               # Autonomous agent classes & ReACT ChatAgent
    ├── core/                 # Config, ModelRouter, QuotaTracker, JobStore, CodeVerifier
    ├── providers/            # LLM provider adapters (Groq, OpenRouter, HF, Ollama)
    ├── extraction/           # Multi-engine PDF layout parser (Docling, MuPDF, Gemini VLM)
    ├── retrieval/            # Chunking, vector DB, hybrid search, knowledge graph
    ├── graph/                # LangGraph 5-node autonomous StateGraph workflow
    ├── schemas/              # Pydantic request/response models
    ├── tools/                # ReACT tool registry
    └── evals/                # Evaluation and benchmarking harness
```

---

## API Reference

All routes are mounted under `/api/v1`. Full interactive OpenAPI Swagger spec at `/docs`.

### Auth — `/api/v1/auth`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/setup-wizard` | Initial onboarding wizard: set profile, API keys, and device prefs. |
| GET | `/auth/check-ollama` | Detect if local Ollama daemon is reachable on `localhost:11434`. |
| POST | `/auth/verify-key` | Test validity of an API key against provider endpoints. |
| POST | `/auth/local-login` | Authenticate or auto-register local developer profile (returns JWT). |
| POST | `/auth/reset-session` | Clear active token and session state. |

---

### Papers — `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/papers/upload` | Upload PDF paper, parse document layout, and index into vector store. |
| GET | `/papers` | List all ingested papers with metadata and extraction status. |
| GET | `/papers/{id}` | Retrieve parsed metadata, summary, and section tree for a paper. |
| GET | `/papers/{id}/pdf` | Stream raw PDF document file. |
| POST | `/papers/{id}/synthesize` | Trigger Dual Code Engine synthesis (Qwen + Gemini) for a paper. |
| GET | `/papers/{id}/knowledge_graph` | Retrieve 7-tier NetworkX knowledge graph for a paper. |
| GET | `/papers/{id}/codebase` | Download or view the synthesized PyTorch codebase. |
| GET | `/papers/{id}/manifest` | Retrieve the build and verification manifest. |
| DELETE | `/papers/{id}` | Delete paper, vector embeddings, and reports from disk. |

---

### Pipeline — `/api/v1/pipeline`

Autonomous 5-node LangGraph extraction and code synthesis pipeline.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/pipeline/analyze` | Dispatch background ingestion & synthesis job for an uploaded paper. |
| GET | `/pipeline/jobs/{id}` | Inspect real-time status, progress (0–100%), and active stage. |
| GET | `/pipeline/jobs/{id}/events` | **Primary SSE stream.** Real-time job logs and mascot state triggers. |
| POST | `/pipeline/jobs/{id}/cancel` | Request graceful cancellation of a running pipeline job. |
| GET | `/pipeline/jobs/{id}/manifest` | Retrieve execution manifest for a completed job. |
| GET | `/pipeline/manifests` | List all completed run manifests. |

---

### Chat — `/api/v1/conversations`

Conversational interface powered by the ReACT agent loop with RAG grounding.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/conversations` | List all conversation threads. |
| POST | `/conversations` | Create a new conversation thread. |
| GET | `/conversations/active` | Get metadata and messages for the active conversation. |
| POST | `/conversations/{id}/chat` | Non-streaming chat completion via ReACT loop. |
| POST | `/conversations/{id}/chat/stream` | **Primary path.** Streaming SSE chat completion. |
| PATCH | `/conversations/{id}` | Rename conversation thread title. |
| DELETE | `/conversations/{id}` | Delete conversation thread from disk. |

#### SSE Stream Event Protocol

| Event | Payload | Description |
|-------|---------|-------------|
| `status` | string | Progress text ("Thinking...", "ReACT turn 1/3...") |
| `thought` | string | ReACT reasoning thought trace |
| `action` | string | Tool being executed |
| `observation` | string | Tool execution observation output |
| `token` | string | Streamed response chunk (assembled client-side) |
| `done` | JSON | Final metadata: `{title, model_used, failover_model, ...}` |
| `error` | string | Error description |

---

### Models — `/api/v1/models`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/models` | List all available models (Groq, OpenRouter, Local Ollama). |
| GET | `/models/status` | Real-time connectivity and health across all model providers. |
| GET | `/models/limits` | Live rate limits and quota metrics for all providers. |
| GET | `/models/dual-engine` | Status and availability of Gemini + HF Dual Code Engines. |

---

### Hardware & Telemetry — `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hardware/metrics` | Live CPU, RAM, and GPU/CUDA metrics via `psutil` + `torch.cuda`. |
| GET | `/telemetry/traces` | Stored agent execution traces. |
| POST | `/evals/run-rag` | Run empirical RAG evaluation harness against an ingested paper. |
| GET | `/evals/baseline` | Retrieve baseline RAG accuracy and grounding benchmarks. |
| GET | `/evals/benchmark/{paper_id}` | Retrieve benchmark metrics for a specific paper. |

---

## Architecture

### ChatAgent — ReACT Inference Loop

`app/agents/chat_agent.py` implements a **ReACT** (Reasoning + Action + Observation) loop:

1. **Context Assembly** — `context_builder.py` gathers user facts, extracted hyperparameters, episodic memory, and recent chat history into a single LLM prompt.
2. **Model Routing** — `ModelRouter` dispatches to the selected provider (Groq → OpenRouter → Ollama) respecting quota windows.
3. **Tool Execution** — On `Action:` traces, the agent identifies the tool, executes it, and feeds the `Observation:` back for the next turn (up to 5 turns).
4. **Answer Extraction** — `Final Answer:` is streamed token-by-token as SSE `token` events.
5. **Auto-Failover** — On provider 429/error, `ModelRouter` retries the next available provider. `resolve_failover_model_id()` maps the backend model name back to the frontend model ID so the UI ticks the correct model.

```
User Message
    │
    ▼
context_builder.py  (user facts + hyperparams + episodic memory + chat history)
    │
    ▼
ModelRouter.generate()  (Groq → OpenRouter → Ollama, quota-aware failover)
    │
    ▼
ReACT Loop (max 5 turns)
    │  THOUGHT → ACTION → tool_executor → OBSERVATION
    ▼
Final Answer → SSE token stream → ChatDatabase.save_message()
```

---

### ModelRouter — Provider Dispatch & Failover

`app/core/model_router.py` routes to one of four adapters:

| Provider | Adapter | Use Case |
|----------|---------|----------|
| **Groq** | `groq_adapter.py` | Ultra-fast LPU chat (Qwen 3.8 27B, GPT-OSS 120B) |
| **OpenRouter** | `openrouter_adapter.py` | Free-tier reasoning (Gemini 2.5 Flash, DeepSeek R1) |
| **Hugging Face** | `hf_adapter.py` | Backend-exclusive Dual Code Engine (Qwen 2.5 Coder 32B) |
| **Ollama** | `ollama_adapter.py` | Fully offline local models (user-configured) |

Every inference path calls `quota_tracker.record_usage()` including all failover branches.

**Provider Exclusions (by design):**
- **Gemini** — Dedicated to PDF extraction + Dual Code Engine; not available in chat UI
- **Hugging Face** — Dedicated to Dual Code Engine; not available in chat UI
- **SambaNova** — Retired (402 payment required)
- **Cerebras** — Legacy, removed

---

### Dual Code Engine

`app/core/dual_code_engine.py` runs **parallel async code synthesis** using two specialized backends:

| Engine | Model | Role |
|--------|-------|------|
| **Engine A** | `Qwen/Qwen2.5-Coder-32B-Instruct` (HuggingFace) | Idiomatic PyTorch specialist |
| **Engine B** | `gemini-2.5-flash` (Google Gemini) | Deep paper context + mathematical precision |

Both generate code concurrently. Each output is:
1. Validated via `ast.parse()` for syntax correctness
2. Security-checked (blocks `os.system`, `subprocess.run`, `eval`, `exec`)
3. Merged: the syntactically valid, higher-quality output is selected and verified by `code_verifier.py`

---

### LangGraph Pipeline — 5-Node Autonomous Workflow

`app/graph/workflow.py` builds a compiled LangGraph `StateGraph`:

```
START → ingestion_node → extraction_node → feasibility_node → sequencing_node → verification_node → END
```

| Node | Agent | Responsibility |
|------|-------|---------------|
| `ingestion_node` | IngestionAgent | Loads parsed paper JSON into state |
| `extraction_node` | ParameterAgent | Extracts ML hyperparameters, datasets, metrics |
| `feasibility_node` | FeasibilityAgent | Scores hardware feasibility (VRAM, compute budget) |
| `sequencing_node` | SequencingAgent | Orders implementation milestones into a workplan |
| `verification_node` | CodeGenAgent | Synthesizes and verifies PyTorch training code |

---

### PDF Extraction Pipeline

`app/extraction/` implements a multi-engine document parsing system with automatic fallback:

| Parser | Trigger |
|--------|---------|
| **Docling** | Primary (structure-aware, ML-native) |
| **PyMuPDF** | Fallback for Docling failures |
| **GROBID** | Optional scholarly metadata (if running locally at port 8070) |
| **OpenRouter / Gemini** | Gemini 2.5 Flash for complex scientific PDFs |

`merger.py` reconciles outputs from multiple parsers into a canonical JSON schema with sections, equations, figures, and tables.

---

### Retrieval Layer

| Component | File | Description |
|-----------|------|-------------|
| **Chunker** | `chunker.py` | Overlapping semantic text chunks |
| **Embeddings** | `embeddings.py` | Sentence-transformer embeddings for FAISS |
| **Vector DB** | `vector_db.py` | Per-paper FAISS index with similarity search |
| **Knowledge Graph** | `knowledge_graph.py` | NetworkX entity graph (methods, datasets, metrics, citations) |

---

### Tools Registry

| Tool | Description |
|------|-------------|
| `arxiv_search` | Search arXiv for related papers |
| `scholar_search` | Google Scholar search via Tavily |
| `vector_search` | Semantic search within the paper's FAISS index |
| `graph_search` | Entity/relationship lookup in the paper's knowledge graph |
| `canonical_document` | Full structured paper JSON (sections, equations, figures) |
| `hyperparameter_tool` | Extracted ML hyperparameters for a paper |
| `episodic_memory` | Episodic memory search from past relevant context |

---

### Quota Tracker

`app/core/quota_tracker.py` maintains rolling quota windows for all providers in memory:

- Tracks request counts and token usage over **1-minute, 60-minute, and 24-hour** rolling windows
- Exposed via `GET /models/limits` → consumed by the frontend Quota Dashboard
- `record_usage(provider, model, tokens)` is called by every inference path including all failover branches

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | JWT signing secret. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GROQ_API_KEY` | ✅ | Groq cloud API key (`gsk_...`) |
| `OPENROUTER_API_KEY` | ✅ | OpenRouter API key (`sk-or-...`) |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key (PDF extraction + Dual Code Engine) |
| `HUGGINGFACE_API_KEY` | ✅ | HuggingFace token (`hf_...`) for Qwen 2.5 Coder 32B |
| `TAVILY_API_KEY` | Recommended | Enables academic search tools (arXiv, Scholar) |
| `OLLAMA_HOST` | Optional | Override default `http://localhost:11434` |
| `GEMINI_MODEL` | Optional | Override Gemini model (default: `gemini-2.5-flash`) |
| `EXTRACTION_PROVIDER` | Optional | `gemini` (default) or `openrouter` for PDF parsing |

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | Async HTTP server + ASGI runtime |
| `sse-starlette` | Server-Sent Events for streaming chat responses |
| `langgraph` | StateGraph autonomous pipeline orchestration |
| `docling` | Primary scientific PDF parsing |
| `pymupdf` | Fallback PDF parsing |
| `httpx` | Async HTTP client for provider API calls |
| `tavily-python` | Web + academic search tool |
| `torch` | CUDA detection + PyTorch code verification |
| `psutil` | Live CPU/RAM hardware metrics |
| `networkx` | Knowledge graph construction |
| `pydantic` | Request/response schema validation |
| `python-dotenv` | `.env` file loading |

---

## Running Tests

All 31 automated backend tests are powered by `pytest` and configured in `pytest.ini`:

```powershell
# Run entire test suite (quiet mode)
python -m pytest tests/ -q

# Run verbose output
python -m pytest tests/ -v

# Run a specific module
python -m pytest tests/test_dual_code_engine.py -v
python -m pytest tests/test_model_router.py -v
```

> For mocking patterns, fail-fast options, and RAG evaluation benchmarks, see the [Testing & Benchmarking Guide](../documents/testing_and_benchmarking.md).

---

## Further Reading

* 📘 [Master Engineering Textbook & Index](../documents/README.md)
* 🛠️ [Backend Operational Commands & Curl Reference](../documents/backend_commands.md)
* 🧪 [Testing & Benchmarking Guide](../documents/testing_and_benchmarking.md)
* 🚀 [Developer Extension & Contributing Recipes](../documents/developer_contributing.md)
