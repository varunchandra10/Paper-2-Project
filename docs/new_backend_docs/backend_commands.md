# Backend Commands & Setup Guide

This document contains all the essential setup, dependency installation, service orchestration, and execution commands for the **Synthexis Backend**.

---

## 1. Virtual Environment Setup

> **Note:** We strongly recommend using **`uv`** for managing environments and packages because it is 10x–100x faster than standard `pip`. However, standard Python `venv`/`pip` commands work as well.

### A. Activate Virtual Environment (PowerShell)
Always ensure your `.venv` is activated before running backend commands:
```powershell
.venv\Scripts\Activate.ps1
```
*(If script execution is disabled on Windows, run once: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### B. Create Virtual Environment (If setting up fresh)
```powershell
# Using uv (Recommended - ultra-fast)
uv venv .venv --python 3.12

# OR using standard Python
python -m venv .venv
```

---

## 2. Dependency Installation Commands

Choose **ONE** of the two approaches below:

---

### 👉 OPTION 1: All-in-One Installation (Recommended)
If you just want to get the entire backend running immediately with all tested dependencies:

```powershell
# Using uv (Recommended - takes seconds)
uv pip install -r backend/requirements.txt

# OR using standard pip
pip install -r backend/requirements.txt
```

---

### 👉 OR OPTION 2: Step-by-Step Modular Installation
If you want to understand what each dependency is used for or install packages category-by-category:

#### 1. Core Backend & API Framework
*FastAPI server, Uvicorn ASGI runner, Pydantic schemas, and file upload handlers:*
```powershell
# Using uv
uv pip install fastapi uvicorn pydantic pydantic-settings python-multipart requests

# OR using pip
pip install fastapi uvicorn pydantic pydantic-settings python-multipart requests
```

#### 2. Local AI & LLM (Ollama & LangChain)
*Ollama client library and LangChain primitives for agent reasoning:*
```powershell
# Using uv
uv pip install ollama langchain langchain-ollama langchain-core

# OR using pip
pip install ollama langchain langchain-ollama langchain-core
```

#### 3. PDF Processing & Layout Extraction
*PyMuPDF, pdfplumber, and Docling for document layout, font metrics, and table parsing:*
```powershell
# Using uv
uv pip install pymupdf pdfplumber docling

# OR using pip
pip install pymupdf pdfplumber docling
```

#### 4. Math, Machine Learning & PyTorch (Code Synthesis)
*NumPy for vector cosine similarity and PyTorch for code generation & evaluation:*
```powershell
# Using uv
uv pip install numpy scipy torch torchvision

# OR using pip
pip install numpy scipy torch torchvision
```

---

### 🔄 Freezing / Updating requirements.txt
Whenever you install new packages, freeze them back to `backend/requirements.txt`:
```powershell
# Using uv
uv pip freeze > backend/requirements.txt

# OR using standard pip
python -m pip freeze > backend/requirements.txt
```

---

## 3. External Services Orchestration

### A. Grobid Document Layout Parser (Docker)
Grobid parses scientific headers, TEI-XML, citations, and formulas on port `8070`:
```powershell
docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.9.0-crf
```
**Verify Grobid Status:**
```powershell
curl http://localhost:8070/api/isalive
# Expected response: true
```

### B. Ollama Local LLM Daemon & Models
Ensure Ollama is running and download the required local models:
```powershell
# Start Ollama service (if not running in background)
ollama serve

# Pull coder reasoning model
ollama pull qwen2.5-coder:1.5b

# Pull text embedding model for RAG search
ollama pull nomic-embed-text:latest

# List installed models
ollama list
```

---

## 4. Running the Backend Server

### Start the FastAPI Application
Run directly from the repository root:
```powershell
python backend/main.py
```
Or directly using `uvicorn`:
```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc UI:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Server Health Check:** [http://localhost:8000/](http://localhost:8000/)

---

## 5. Verification & Health Check Commands

### Check Python Interpreter & Environment
```powershell
python -c "import sys; print('Active Python:', sys.executable)"
```

### Test Ollama Python Integration
```powershell
python -c "import ollama; client = ollama.Client(); print('Ollama Models:', client.list())"
```

### Test PDF Extraction & PyMuPDF Integration
```powershell
python -c "import fitz, requests; print('PyMuPDF Version:', fitz.__version__)"
```

### Test Backend Extraction Pipeline Import
```powershell
python -c "import sys; sys.path.insert(0, 'backend'); from app.extraction.pdf_parser import parse_pdf_document; print('Extraction modules connected successfully!')"
```
