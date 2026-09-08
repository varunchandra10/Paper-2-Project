# RUEXIS AI — Backend

FastAPI backend for the RUEXIS AI Platform. Provides all inference, ingestion, retrieval, telemetry, and hardware APIs consumed by the Electron desktop app.

---

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Fill in: GROQ_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY, HUGGINGFACE_API_KEY, TAVILY_API_KEY, SECRET_KEY

# 4. Start the backend server
python main.py
# Or directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server runs at **http://localhost:8000**
- Interactive API docs: http://localhost:8000/docs
- Rate Limits Dashboard: http://localhost:8000/limits-dashboard
- JSON Health Check: http://localhost:8000/api/status

---

## Directory Structure

```
backend/
├── main.py                   # FastAPI app, CORS middleware, root routes
├── requirements.txt          # Minimal pinned dependencies
├── .env.example              # Environment variable template
├── storage/                  # All runtime-persisted data (git-ignored)
│   ├── papers/               # Raw uploaded PDF/DOCX files
│   ├── extracted_json/       # Structured extraction output per paper
│   ├── conversations/        # Per-conversation JSON message history
│   ├── history/              # User profile & document metadata
│   ├── reports/              # Generated analysis reports
│   ├── rag_embeddings/       # FAISS vector indices per paper
│   ├── knowledge_graphs/     # NetworkX knowledge graphs per paper
│   ├── codes/                # Generated PyTorch code outputs
│   └── traces/               # Agent execution traces
└── app/
    ├── api/v1/               # HTTP endpoint routers
    ├── agents/               # Autonomous agent classes
    ├── core/                 # Config, routing, prompts, quota tracker
    ├── providers/            # LLM provider adapters
    ├── extraction/           # PDF/DOCX parsing pipeline
    ├── retrieval/            # Chunking, embedding, vector DB, knowledge graph
    ├── graph/                # LangGraph StateGraph workflow
    ├── schemas/              # Pydantic request/response models
    ├── tools/                # ReACT tool registry
    └── evals/                # Evaluation harness
```

---

## API Reference

All routes are mounted under `/api/v1`. Full interactive spec at `/docs`.

### Auth — `/api/v1/auth`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/local-login` | Register or authenticate a local developer profile. Returns JWT. |

---

### Chat — `/api/v1/conversations`

Core conversational interface powered by the ReACT agent loop.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/conversations` | List all conversation threads + active_conversation_id. |
| POST | `/conversations` | Create a new conversation thread (optional title, project_id). |
| GET | `/conversations/active` | Get metadata + messages for the currently active conversation. |
| POST | `/conversations/active` | Set or clear the active conversation. |
| GET | `/conversations/{id}` | Fetch all messages and metadata for a conversation. |
| GET | `/conversations/{id}/messages` | Alias of above. |
| POST | `/conversations/{id}/chat` | Non-streaming chat completion via ChatAgent ReACT loop. |
| POST | `/conversations/{id}/chat/stream` | **Primary path.** Streaming SSE chat completion. |
| PATCH | `/conversations/{id}` | Update conversation title. |
| DELETE | `/conversations/{id}` | Delete a conversation thread from disk. |
| GET | `/memory` | Retrieve stored user facts (episodic memory). |
| POST | `/memory` | Add a new user fact to persistent memory. |

#### SSE Stream Event Protocol

| Event | Payload | Description |
|-------|---------|-------------|
| `status` | string | Progress text ("Thinking...", "ReACT turn 1/3...") |
| `thought` | string | ReACT THOUGHT trace |
| `action` | string | Tool being executed |
| `observation` | string | Tool result summary |
| `token` | string | Individual response chunk (assembled client-side) |
| `done` | JSON | Final: `{title, model_used, failover_model, thought, action, observation}` |
| `error` | string | Error message string |

---

### Papers — `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Upload PDF/DOCX, parse, and RAG-index. Returns paper_id + conversation_id. |
| POST | `/history/upload` | Alias of `/upload`. |
| GET | `/history` | List all ingested papers (title, paper_id, status). |
| GET | `/history/{paper_id}` | Get metadata for a specific paper. |
| GET | `/history/{paper_id}/hyperparameters` | Get extracted hyperparameters JSON. |
| GET | `/papers/{paper_id}/pdf` | Serve the raw PDF file. |
| GET | `/papers/{paper_id}/view` | Serve PDF inline for browser rendering. |
| DELETE | `/history/{paper_id}` | Delete paper + all associated data from disk. |
| GET | `/profile` | Retrieve user profile JSON. |
| PATCH | `/profile` | Update user profile (name, API keys, Ollama link). |

---

### Pipeline — `/api/v1`

LangGraph autonomous paper-to-experiment analysis pipeline.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/pipeline/ingest` | Trigger full 5-node LangGraph pipeline for a paper (background task). |
| POST | `/pipeline/approve` | Submit parameter approval or rejection after user review. |
| GET | `/stream/{run_id}` | SSE stream for live pipeline logs + mascot state signals. |
| GET | `/extraction/stream/{run_id}` | Alias of above. |
| GET | `/pipeline/status/{run_id}` | Current job status (queued / processing / completed / failed). |
| GET | `/pipeline/report/{paper_id}` | Retrieve the final generated analysis report. |

---

### Models — `/api/v1/models`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/models` | List all frontend-visible models (Groq, OpenRouter, Local Ollama). |
| GET | `/models/limits` | Live rate limits and quota metrics for all providers. |
| GET | `/models/dual-engine` | Gemini + HF Dual Code Engine availability and configuration. |

---

### Hardware — `/api/v1/hardware`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hardware/metrics` | Live CPU (cores, RAM, usage%) and GPU (VRAM, CUDA) via psutil + nvidia-smi. |

---

### Telemetry — `/api/v1/telemetry`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/telemetry/traces` | Retrieve stored agent execution traces for evaluation. |

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
