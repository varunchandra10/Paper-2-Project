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

---

## 📅 Day 3 — Method Decomposition Agent

### Implementation Details
We implemented the Method Decomposition Agent to extract a structured component graph from the paper's main architectural descriptions:
* **Pydantic Graph Structure:** Defined `Component` and `ComponentGraph` models mapping components (name, type, description, inputs, outputs, hyperparameters) and their connections.
* **Context Fusing:** Configured the agent to receive both the `Method` and `Experiments` sections, allowing the local LLM to extract both structural blocks and training parameters.
* **Prompt Enforcements:** Added rules to strictly extract concrete hyperparameters (e.g. batch size `24`, epochs `250`) and prevent the LLM from outputting template variable placeholders (like `"{batch_size}"`).
* **Test Isolation:** Relocated testing scripts into a modular `backend/tests/` folder for clean verification and future regression testing.

### Verification Results
Ran `python backend/tests/test_decomposition.py` on the parsed sections:
* **Output File:** Successfully generated the architectural graph in [`vlcd_paper_components.json`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/papers/vlcd_paper_components.json).
* **Extraction Quality:** Correctly isolated 9 distinct components, mapping their inputs, outputs, and exact hyperparameters (e.g. `optimizer: 'AdamW'`, `learning_rate: '0.001'`, `batch_size: '24'`).

---

## 📅 Day 4 — Validation Checkpoint 1 🔒

### Validation Process
We manually cross-referenced the component graph outputted in `vlcd_paper_components.json` on Day 3 against the ground-truth VLCD paper specifications.

### Results
* **Core Components Isolated:** Correctly identified the frozen base encoder `RemoteCLIP / CLIP Image Encoder`, the visual backbone `Swin Transformer (RFN)`, and the parameter-efficient adapter layers `Side Fusion Network (SFN)`.
* **Sub-Modules Mapped:** Correctly identified the intermediate `Bridging Module`, text prompt learning `Context Optimization (CoOp)`, and pixel-level relevance map computation `Change Feature Calculation (CFC) module`.
* **Validation Outcome:** **PASS**. The LLM correctly mapped the inputs and outputs of each module and cleanly extracted concrete hyperparameters.

---

## 📅 Day 5 — Gap-Finding Agent

### Implementation Details
We developed the Gap-Finding Agent to scan the decomposed component graph for missing or unspecified hyperparameters, query web search and code APIs, and reason about confidence levels:
* **Centralized Schemas:** Created [`backend/schemas.py`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/schemas.py) to centralize all Pydantic models. Modified the `Component` model to store hyperparameters in a structured `parameters` dictionary mapping names to `ParameterDetails` objects (containing `value`, `confidence`, and `rationale` fields).
* **Gap-Finding Logic:** Created [`backend/gap_agent.py`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/gap_agent.py). This script parses the component graph, flags unspecified parameters, constructs targeted queries, and queries the Tavily (web search) and GitHub (code search) APIs.
* **Offline Fallback & Package-Free env Loader:** Integrated a custom environment loader to parse `.env` files for keys without external dependencies. Programmed local LLM decoding rules to fallback to standard machine learning defaults (e.g. Swin-T default patch size) if search keys are missing, preventing runtime crashes.
* **Harness & Automation:** Created [`backend/tests/test_gap.py`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/tests/test_gap.py) to test the agent, and template [`backend/.env.example`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/.env.example).

### Verification Results
Ran `python backend/tests/test_gap.py`:
* **Output File:** Successfully generated the gap-filled component graph in [`vlcd_paper_gap_filled.json`](file:///c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/papers/vlcd_paper_gap_filled.json).
* **Tagging Accuracy:** Confirmed parameters like word embedding width `512` as `CONFIRMED`, successfully resolved prompt length `M = 100` as `CONFIRMED` based on search context, and kept unknown modules tagged as `ASSUMED` with fallback rationales, matching our expected test outcomes.

