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

### Freeze/Update requirements.txt

```powershell
pip freeze > requirements.txt
```

---

## 3. Environment Configuration

```powershell
# Copy template
cp .env.example .env
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
```

Validate your keys are loaded:

```powershell
python -c "from app.core.config import settings; print('Groq:', settings.has_groq()); print('Gemini:', settings.has_gemini()); print('HF:', settings.has_huggingface())"
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

### List available models
```powershell
curl http://localhost:8000/api/v1/models
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

### List conversations
```powershell
curl http://localhost:8000/api/v1/conversations
```

### Create a conversation
```powershell
curl -X POST http://localhost:8000/api/v1/conversations `
  -H "Content-Type: application/json" `
  -d '{"title": "Test Chat"}'
```

### Send a streaming chat message
```powershell
# Replace <conv_id> with actual conversation ID
curl -N -X POST http://localhost:8000/api/v1/conversations/<conv_id>/chat/stream `
  -H "Content-Type: application/json" `
  -d '{"message": "What is this paper about?", "model_name": "qwen/qwen3.8-27b"}'
```

### Upload a PDF paper
```powershell
curl -X POST http://localhost:8000/api/v1/upload `
  -F "file=@path/to/paper.pdf"
```

---

## 7. Module Connectivity Checks

```powershell
# Verify all core imports
python -c "from app.agents.chat_agent import ChatAgent; print('ChatAgent OK')"
python -c "from app.core.model_router import ModelRouter; print('ModelRouter OK')"
python -c "from app.core.dual_code_engine import dual_code_engine; print('DualCodeEngine OK')"
python -c "from app.graph.workflow import app_workflow; print('LangGraph pipeline OK')"
python -c "from app.tools import get_all_tools; print('Tools:', [t.name for t in get_all_tools()])"
python -c "from app.extraction.pdf_parser import parse_pdf_document; print('PDF parser OK')"
python -c "from app.retrieval.vector_db import PaperVectorDB; print('VectorDB OK')"
python -c "from app.retrieval.knowledge_graph import PaperKnowledgeGraph; print('KnowledgeGraph OK')"
```

---

## 8. Run Tests

```powershell
cd backend
python -m pytest tests/ -v
```
