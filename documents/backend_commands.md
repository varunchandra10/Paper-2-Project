# Backend Commands & Setup Guide

All essential commands for setting up, configuring, and running the **RUEXIS AI Backend** (v2.0).

---

## 1. Virtual Environment Setup

```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
venv\Scripts\Activate.ps1
# If execution policy blocks it:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate (Windows CMD)
venv\Scripts\activate.bat
```

---

## 2. Install Dependencies

```powershell
# From the backend/ directory
pip install -r requirements.txt

# For running tests (dev dependencies):
pip install pytest pytest-asyncio
```

### Key Package Groups

| Group | Packages | Purpose |
|-------|----------|---------|
| **API Server** | `fastapi`, `uvicorn`, `sse-starlette`, `python-multipart` | HTTP + SSE streaming |
| **HTTP Client** | `httpx`, `requests` | Provider API calls |
| **Schemas** | `pydantic`, `python-dotenv` | Validation + env config |
| **Agents** | `langgraph` | 5-node autonomous pipeline |
| **PDF Parsing** | `docling`, `pymupdf` | Multi-engine PDF extraction |
| **Search** | `tavily-python` | arXiv + Google Scholar tools |
| **ML/Hardware** | `torch`, `numpy`, `psutil` | CUDA check + hardware metrics |
| **Graph** | `networkx` | Knowledge graph construction |
| **Local LLM** | `ollama` | Offline local model client |
| **Testing (Dev)** | `pytest`, `pytest-asyncio` | Test runner & async fixtures |

### Freeze/Update requirements.txt

```powershell
pip freeze > requirements.txt
```

---

## 3. Environment Configuration

```powershell
# Copy template (PowerShell)
Copy-Item .env.example .env

# Or in Windows CMD:
copy .env.example .env
```

Edit `backend/.env` with your keys:

```env
# Required
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-...
GEMINI_API_KEY=AIza...
HUGGINGFACE_API_KEY=hf_...

# Recommended
TAVILY_API_KEY=tvly-...

# Optional
OLLAMA_HOST=http://localhost:11434
GEMINI_MODEL=gemini-2.5-flash
EXTRACTION_PROVIDER=gemini
GROBID_URL=http://localhost:8070
GITHUB_TOKEN=ghp_...
```

Validate your keys are loaded:

```powershell
python -c "from app.core.config import settings; print('Groq:', settings.has_groq()); print('Gemini:', settings.has_gemini()); print('HF:', settings.has_huggingface()); print('OpenRouter:', settings.has_openrouter())"
```

---

## 4. Optional External Services

### GROBID (Scholarly PDF metadata — optional)

```powershell
docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf
```

Verify:
```powershell
curl http://localhost:8070/api/isalive
# Expected: true
```

### Ollama (Local offline models — optional)

```powershell
# Start daemon
ollama serve

# Pull any model (shown in ModelSelector when running)
ollama pull qwen2.5:7b
ollama pull llama3.2:3b

# List installed models
ollama list
```

---

## 5. Start the Backend Server

```powershell
# From inside backend/
python main.py

# Or directly with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

| URL | Purpose |
|-----|---------|
| `http://localhost:8000` | Root — HTML dashboard or JSON status |
| `http://localhost:8000/docs` | Interactive Swagger API docs |
| `http://localhost:8000/redoc` | ReDoc API reference |
| `http://localhost:8000/api/status` | Machine-readable JSON health check |
| `http://localhost:8000/limits-dashboard` | Live rate limits & quota UI |

---

## 6. API Quick-Test Commands

### Health check
```powershell
curl http://localhost:8000/api/status
```

### Check Ollama local availability
```powershell
curl http://localhost:8000/api/v1/auth/check-ollama
```

### Setup wizard onboarding (submit provider API key)
```powershell
curl -X POST http://localhost:8000/api/v1/auth/setup-wizard `
  -H "Content-Type: application/json" `
  -d '{"apiKey": "AIzaSy...", "preferredProvider": "gemini"}'
```

### List available models & status
```powershell
curl http://localhost:8000/api/v1/models
curl http://localhost:8000/api/v1/models/status
```

### Check rate limits / quota dashboard
```powershell
curl http://localhost:8000/api/v1/models/limits
```

### Check Dual Code Engine status
```powershell
curl http://localhost:8000/api/v1/models/dual-engine
```

### Check hardware metrics
```powershell
curl http://localhost:8000/api/v1/hardware/metrics
```

### Upload a PDF paper
```powershell
curl -X POST http://localhost:8000/api/v1/papers/upload `
  -F "file=@path/to/paper.pdf"
```

### List uploaded papers
```powershell
curl http://localhost:8000/api/v1/papers
```

### Dispatch an autonomous pipeline job
```powershell
curl -X POST http://localhost:8000/api/v1/pipeline/analyze `
  -H "Content-Type: application/json" `
  -d '{"filePath": "storage/papers/<paper_id>.pdf", "modelName": "llama-3.3-70b-versatile"}'
```

### Stream live pipeline SSE events
```powershell
# Replace <job_id> with actual job ID returned by analyze
curl -N http://localhost:8000/api/v1/pipeline/jobs/<job_id>/events
```

### Inspect job status & report manifest
```powershell
curl http://localhost:8000/api/v1/pipeline/jobs/<job_id>
curl http://localhost:8000/api/v1/pipeline/jobs/<job_id>/manifest
curl http://localhost:8000/api/v1/pipeline/manifests
```

### Synthesize code for a paper
```powershell
curl -X POST http://localhost:8000/api/v1/papers/<paper_id>/synthesize `
  -H "Content-Type: application/json" `
  -d '{"engine": "both"}'
```

### Knowledge graph & traces
```powershell
curl http://localhost:8000/api/v1/papers/<paper_id>/knowledge_graph
curl http://localhost:8000/api/v1/papers/<paper_id>/knowledge_graph/validate
curl http://localhost:8000/api/v1/papers/<paper_id>/traces
```

### RAG benchmark & evals
```powershell
curl http://localhost:8000/api/v1/evals/baseline
curl -X POST http://localhost:8000/api/v1/evals/run-rag `
  -H "Content-Type: application/json" `
  -d '{"paper_id": "<paper_id>"}'
```

### List conversations & chat
```powershell
curl http://localhost:8000/api/v1/conversations

# Create conversation
curl -X POST http://localhost:8000/api/v1/conversations `
  -H "Content-Type: application/json" `
  -d '{"title": "Test Chat"}'

# Stream chat response
curl -N -X POST http://localhost:8000/api/v1/conversations/<conv_id>/chat/stream `
  -H "Content-Type: application/json" `
  -d '{"message": "What is this paper about?", "model_name": "llama-3.3-70b-versatile"}'
```

---

## 7. Module Connectivity Checks

Verify that all core components can be imported and initialized:

```powershell
# Core Routers and Engines
python -c "from app.core.config import settings; print('Config OK')"
python -c "from app.core.model_router import ModelRouter; print('ModelRouter OK')"
python -c "from app.core.dual_code_engine import dual_code_engine; print('DualCodeEngine OK')"
python -c "from app.core.job_store import get_job_store; print('JobStore OK')"
python -c "from app.core.report_manifest import ReportManifest; print('ReportManifest OK')"

# Agents & Graph Workflow
python -c "from app.agents.chat_agent import ChatAgent; print('ChatAgent OK')"
python -c "from app.graph.workflow import app_workflow; print('LangGraph pipeline OK')"
python -c "from app.tools import get_all_tools; print('Tools:', [t.name for t in get_all_tools()])"

# Extraction & Retrieval
python -c "from app.extraction.pdf_parser import parse_pdf_document; print('PDF parser OK')"
python -c "from app.extraction.multimodal_vlm import vlm_extractor; print('VLM Extractor OK')"
python -c "from app.retrieval.vector_db import PaperVectorDB; print('VectorDB OK')"
python -c "from app.retrieval.knowledge_graph import PaperKnowledgeGraph; print('KnowledgeGraph OK')"
python -c "from app.retrieval.hybrid_search import HybridSearch; print('HybridSearch OK')"
```

---

## 8. Run Tests

```powershell
cd backend

# Run entire test suite (35 test files)
python -m pytest tests/ -v

# Run quick tests without verbose output
python -m pytest tests/ -q

# Run a specific test module
python -m pytest tests/test_vlm_extractor.py -v
python -m pytest tests/test_pipeline_jobs.py -v
python -m pytest tests/test_dual_code_engine.py -v
```
