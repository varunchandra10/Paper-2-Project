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
