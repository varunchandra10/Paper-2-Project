# Phase 1 Documentation — Agentic Core

This document tracks the features, implementation details, and verification results for Phase 1 (Days 1–14) of the Paper-to-Project Agent.

---

## 📅 Day 1 — Environment + Parsing Pipeline

### Implementation Details
We set up the project environment and built a layout-aware, section-aware PDF text extraction pipeline:
* **Dependency Management:** Configured [`requirements.txt`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/requirements.txt) to track all Python requirements (`pymupdf`, `langgraph`, `langchain-ollama`, `fastapi`, `uvicorn`, `sse-starlette`, `pydantic`, `tavily-python`).
* **Section Segmentation:** Developed [`parser.py`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/parser.py) using PyMuPDF to group text blocks page-by-page according to standard academic section headers (e.g., *Abstract, Introduction, Related Works, Method, Experiments, Discussion, Conclusion*).
* **Context Budget Optimization (Pruning):** Added automatic pruning of `References`, `Bibliography`, and `Acknowledgments` to prevent wasting local LLM context window space. It captures the preceding section completely, then terminates parsing.

### Verification Results
Tested on your uploaded thesis paper [`vlcd_paper.pdf`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/papers/vlcd_paper.pdf):
* **Output File:** Successfully generated the parsed JSON structure: [`vlcd_paper_parsed.json`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/papers/vlcd_paper_parsed.json).
* **Sections Captured:**
  * **Metadata / Front Matter:** 1,638 characters
  * **I. INTRODUCTION:** 10,772 characters
  * **II. RELATED WORKS:** 8,160 characters
  * **III. METHOD:** 14,759 characters
  * **IV. EXPERIMENTS:** 7,676 characters
  * **V. DISCUSSION:** 5,131 characters
  * **VI. CONCLUSION:** 974 characters
* **Pruning:** Successfully triggered on `'REFERENCES'` on Page 12, trimming the bibliography and saving token capacity.

---

## 📅 Day 2 — Paper Ingestion Agent

### Implementation Details
We developed the Ingestion Agent to parse the extracted PDF metadata and sections into a structured Pydantic schema using a local LLM:
* **Pydantic Structuring:** Defined a structured model `PaperMetadata` containing fields for `title`, `authors` (as a list of strings), `abstract`, `sections_found` (with section title and exact character count), and `primary_contribution`.
* **Local LLM Integration:** Connected to the local Ollama runtime using `langchain-ollama`'s `ChatOllama` model class, leveraging the lightweight **`qwen2.5-coder:1.5b`** model (986 MB) to prevent out-of-memory errors on local consumer GPUs.
* **LangGraph Orchestration:** Wrapped the ingestion LLM call in a LangGraph `StateGraph` node, which safely processes the parsed paper dictionary and outputs the typed metadata object.

### Verification Results
Ran `backend/ingestion_agent.py` on the parsed JSON output from Day 1:
* **Output File:** Successfully generated [`vlcd_paper_metadata.json`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/papers/vlcd_paper_metadata.json).
* **Metadata Extraction Quality:**
  * **Title:** `"A Novel Change Detection Method Based on Visual Language from High-Resolution Remote Sensing Images"`
  * **Authors:** Junlong Qiu, Wei Liu, Hui Zhang, Erzhu Li, Lianpeng Zhang, Xing Li
  * **Primary Contribution:** Successfully summarized the core idea (proposed VLCD visual-language change detection method and state-of-the-art results on three datasets) in 2 sentences.
  * **Sections Found:** Cleanly mapped all 6 major sections and their exact character counts.

