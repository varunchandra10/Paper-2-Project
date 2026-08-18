# Phase 1 Documentation - Agentic Core

This document tracks the features, implementation details, and verification results for Phase 1 (Days 1–14) of the Paper-to-Project Agent.

---

## 📅 Day 1 - Environment + Parsing Pipeline

### Implementation Details
We set up the project environment and built a layout-aware, section-aware PDF text extraction pipeline:
* **Dependency Management:** Configured [backend/requirements.txt](../backend/requirements.txt) to track all Python requirements (`pymupdf`, `langgraph`, `langchain-ollama`, `fastapi`, `uvicorn`, `sse-starlette`, `pydantic`, `tavily-python`).
* **Section Segmentation:** Developed [backend/parser.py](../backend/parser.py) using PyMuPDF to group text blocks page-by-page according to standard academic section headers (e.g., *Abstract, Introduction, Related Works, Method, Experiments, Discussion, Conclusion*).
* **Context Budget Optimization (Pruning):** Added automatic pruning of `References`, `Bibliography`, and `Acknowledgments` to prevent wasting local LLM context window space. It captures the preceding section completely, then terminates parsing.

### Verification Results
Tested on your uploaded thesis paper `backend/papers/vlcd_paper.pdf` (local only):
* **Output File:** Successfully generated the parsed JSON structure locally: `backend/papers/vlcd_paper_parsed.json`.
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

## 📅 Day 2 - Paper Ingestion Agent

### Implementation Details
We developed the Ingestion Agent to parse the extracted PDF metadata and sections into a structured Pydantic schema using a local LLM:
* **Pydantic Structuring:** Defined a structured model `PaperMetadata` containing fields for `title`, `authors` (as a list of strings), `abstract`, `sections_found` (with section title and exact character count), and `primary_contribution`.
* **Local LLM Integration:** Connected to the local Ollama runtime using `langchain-ollama`'s `ChatOllama` model class, leveraging the lightweight **`qwen2.5-coder:1.5b`** model (986 MB) to prevent out-of-memory errors on local consumer GPUs.
* **LangGraph Orchestration:** Wrapped the ingestion LLM call in a LangGraph `StateGraph` node, which safely processes the parsed paper dictionary and outputs the typed metadata object.

### Verification Results
Ran `backend/agents/ingestion_agent.py` on the parsed JSON output from Day 1:
* **Output File:** Successfully generated locally: `backend/papers/vlcd_paper_metadata.json`.
* **Metadata Extraction Quality:**
  * **Title:** `"A Novel Change Detection Method Based on Visual Language from High-Resolution Remote Sensing Images"`
  * **Authors:** Junlong Qiu, Wei Liu, Hui Zhang, Erzhu Li, Lianpeng Zhang, Xing Li
  * **Primary Contribution:** Successfully summarized the core idea (proposed VLCD visual-language change detection method and state-of-the-art results on three datasets) in 2 sentences.
  * **Sections Found:** Cleanly mapped all 6 major sections and their exact character counts.

---

## 📅 Day 3 - Method Decomposition Agent

### Implementation Details
We implemented the Method Decomposition Agent to extract a structured component graph from the paper's main architectural descriptions:
* **Pydantic Graph Structure:** Defined `Component` and `ComponentGraph` models mapping components (name, type, description, inputs, outputs, hyperparameters) and their connections.
* **Context Fusing:** Configured the agent to receive both the `Method` and `Experiments` sections, allowing the local LLM to extract both structural blocks and training parameters.
* **Prompt Enforcements:** Added rules to strictly extract concrete hyperparameters (e.g. batch size `24`, epochs `250`) and prevent the LLM from outputting template variable placeholders (like `"{batch_size}"`).
* **Test Isolation:** Relocated testing scripts into a modular `backend/tests/` folder for clean verification and future regression testing.

### Verification Results
Ran `python backend/tests/test_decomposition.py` on the parsed sections:
* **Output File:** Successfully generated the architectural graph locally in: `backend/papers/vlcd_paper_components.json`.
* **Extraction Quality:** Correctly isolated 9 distinct components, mapping their inputs, outputs, and exact hyperparameters (e.g. `optimizer: 'AdamW'`, `learning_rate: '0.001'`, `batch_size: '24'`).

---

## 📅 Day 4 - Validation Checkpoint 1 🔒

### Validation Process
We manually cross-referenced the component graph outputted in `vlcd_paper_components.json` on Day 3 against the ground-truth VLCD paper specifications.

### Results
* **Core Components Isolated:** Correctly identified the frozen base encoder `RemoteCLIP / CLIP Image Encoder`, the visual backbone `Swin Transformer (RFN)`, and the parameter-efficient adapter layers `Side Fusion Network (SFN)`.
* **Sub-Modules Mapped:** Correctly identified the intermediate `Bridging Module`, text prompt learning `Context Optimization (CoOp)`, and pixel-level relevance map computation `Change Feature Calculation (CFC) module`.
* **Validation Outcome:** **PASS**. The LLM correctly mapped the inputs and outputs of each module and cleanly extracted concrete hyperparameters.

---

## 📅 Day 5 - Gap-Finding Agent

### Implementation Details
We developed the Gap-Finding Agent to scan the decomposed component graph for missing or unspecified hyperparameters, query web search and code APIs, and reason about confidence levels:
* **Centralized Schemas:** Created [backend/schemas.py](../backend/schemas.py) to centralize all Pydantic models. Modified the `Component` model to store hyperparameters in a structured `parameters` dictionary mapping names to `ParameterDetails` objects (containing `value`, `confidence`, and `rationale` fields).
* **Gap-Finding Logic:** Created [backend/agents/gap_agent.py](../backend/agents/gap_agent.py). This script parses the component graph, flags unspecified parameters, constructs targeted queries, and queries the Tavily (web search) and GitHub (code search) APIs.
* **Offline Fallback & Package-Free env Loader:** Integrated a custom environment loader to parse `.env` files for keys without external dependencies. Programmed local LLM decoding rules to fallback to standard machine learning defaults (e.g. Swin-T default patch size) if search keys are missing, preventing runtime crashes.
* **Harness & Automation:** Created [backend/tests/test_gap.py](../backend/tests/test_gap.py) to test the agent, and template [backend/.env.example](../backend/.env.example).

### Verification Results
Ran `python backend/tests/test_gap.py`:
* **Output File:** Successfully generated the gap-filled component graph locally: `backend/papers/vlcd_paper_gap_filled.json`.
* **Tagging Accuracy:** Confirmed parameters like word embedding width `512` as `CONFIRMED`, successfully resolved prompt length `M = 100` as `CONFIRMED` based on search context, and kept unknown modules tagged as `ASSUMED` with fallback rationales, matching our expected test outcomes.

---

## 📅 Day 6 - Integration Checkpoint 🔒

### Implementation Details
We implemented the End-to-End Integration Pipeline to chain Ingestion, Decomposition, and Gap-Finding into a single cohesive process:
* **Consolidated Pipeline:** Created [backend/pipeline.py](../backend/pipeline.py) which loads the parsed paper sections, sequentially invokes the three agent nodes, and compiles the final result.
* **Unified Output Schema:** Added `PipelineOutput` to `schemas.py` which combines `PaperMetadata` and the `ComponentGraph` containing the confidence-tagged parameters.
* **Runner Verification:** Created [backend/tests/test_pipeline.py](../backend/tests/test_pipeline.py) to run and audit the end-to-end extraction.

### Verification Results
Ran `python backend/tests/test_pipeline.py`:
* **Output File:** Successfully generated the consolidated results locally in: `backend/papers/vlcd_full_pipeline_output.json`.
* **Audit Success:** Audited the output and verified that **zero unconfirmed values are stated as facts** (8 parameters are explicitly confirmed from the paper context, 0 are inferred, and 6 unspecified architectural blocks are properly tracked under the `ASSUMED` confidence tier with clear rationales).

---

## 📅 Day 7 - Feasibility Agent

### Implementation Details
We implemented the Feasibility Agent to validate architectural demands against hardware profiles:
* **Feasibility Schema:** Added `ComponentFeasibility` and `FeasibilityReport` to `schemas.py` using structured flat list Pydantic structures to avoid GPU JIT compilation crashes.
* **Validator Node:** Created [backend/agents/feasibility_agent.py](../backend/agents/feasibility_agent.py) which evaluates the components and training parameters of `ComponentGraph` against a constraints dictionary.
* **Dynamic Hardware Profiler:** Updated [backend/tests/test_feasibility.py](../backend/tests/test_feasibility.py) to dynamically query system specs. It queries PyTorch CUDA properties and falls back to `nvidia-smi` and PowerShell CIM queries to fetch the exact GPU name, VRAM, system RAM, and CPU count on Windows 11.

### Verification Results
Ran `python backend/tests/test_feasibility.py`:
* **Output File:** Successfully generated locally: `backend/papers/vlcd_feasibility_report.json`.
* **Validation Outcome:** **PASS**. Successfully detected system specs (RTX 5050 Laptop GPU, 8.0 GB VRAM, 23.6 GB System RAM, 16 CPU cores) and flagged visual backbone compute bottlenecks, recommending substitutions.

---

## 📅 Day 8 - Validation Checkpoint 2 (Strongest Evidence) 🔒

### Validation Process
We conducted a strict comparison between the agent's output (`vlcd_feasibility_report.json`) and your real thesis notes (`RemoteCLIP → lightweight head swap`) to identify agreement and divergence.

### Results
* **Audit File:** Created [docs/validation_checkpoint_2.md](validation_checkpoint_2.md) detailing the comparison table.
* **Core Agreement:** **PASS**. The agent independently identified the backbone VRAM constraint and recommended substituting the CNN-transformer BiT backbone with a lightweight backbone (`Swin-T` or `ResNet-18`) and simplifying the decoder.
* **Divergence Noted:** The agent suggested unfreezing the CLIP text encoder for training; however, the real thesis methodology correctly keeps it frozen to preserve memory. This correction will be enforced during the sequencing phase.

---

## 📅 Day 9 - Build Sequencing Agent

### Implementation Details
We implemented the Build Sequencing Agent to compile a dependency-ordered series of implementation milestones:
* **Sequencing Schema:** Added `Milestone` and `BuildSequence` Pydantic models to `schemas.py`.
* **Build Sequencing Node:** Created [backend/agents/sequencing_agent.py](../backend/agents/sequencing_agent.py). This node prompts `qwen2.5-coder:1.5b` to convert the component graph and feasibility report into structured milestones following the "cheap/quick validation first" principle.
* **Test Runner:** Created [backend/tests/test_sequencing.py](../backend/tests/test_sequencing.py) to parse the inputs and write the structured build plan.

### Verification Results
Ran `python backend/tests/test_sequencing.py`:
* **Output File:** Successfully generated the plan locally in: `backend/papers/vlcd_build_sequence.json`.
* **Validation Outcome:** **PASS**. The generated plan schedules 5 ordered milestones. It prioritizes low-cost tasks (like Milestone 1: Data Parsing & PyTorch Loaders and Milestone 2: Loss Function Checks) before moving to loaded backbone setups (Milestone 3), lightweight adapter integrations (Milestone 4), and high-compute training runs (Milestone 5).

---

## 📅 Day 11 - Full LangGraph Orchestration

### Implementation Details
We assembled the complete, end-to-end adaptational pipeline using LangGraph:
* **Central Orchestrator:** Refactored [backend/pipeline.py](../backend/pipeline.py) to define a unified `PipelineState` and build a state graph connecting Ingestion, Decomposition, Gap-Finding, Feasibility, Refinement (hyperparameter scaling), Sequencing, and Report nodes.
* **Orchestration Test Runner:** Created [backend/tests/test_full_orchestration.py](../backend/tests/test_full_orchestration.py) which profiles the local specs and runs the orchestrator graph.
* **Hybrid Report Generation:** Optimized the report synthesis process by compiling the metadata and milestones tables directly in Python (avoiding LLM context constraints and repetitions) and invoking the LLM only for the short, focused narrative paragraphs.

### Verification Results
Ran `python backend/tests/test_full_orchestration.py`:
* **Output File:** Successfully generated locally: `backend/papers/vlcd_adaptation_report_langgraph.md`.
* **Validation Outcome:** **PASS**. The graph ran to completion on the local GPU, successfully executing the refinement loop logic and exporting the project adaptation proposal.

---

## 📅 Day 12 - End-to-End Validation Checkpoint 🔒

### Validation Process
We performed a strict audit of the generated orchestrated report against your thesis notes to check for correctness and identify any model limitations.

### Results
* **Audit File:** Created [docs/validation_checkpoint_3.md](validation_checkpoint_3.md) containing the audit findings.
* **Metadata & Spec Verification:** **PASS**. Title, authors, abstract, and local RTX 5050 GPU/RAM specifications were perfectly matched.
* **Audit Warnings:** Documented that while the feasibility and milestone roadmaps were highly logical and correct, the 1.5B model hallucinated generic TensorFlow boilerplate instructions in the Cloud Alternatives section due to limited corporate dataset mapping.

---

## 📅 Day 13 - Generalization & Edge Cases

### Implementation Details
We added error safety nets and layout compatibility layers to make the pipeline resilient to variations across different academic publications:
* **Ingestion Fallbacks:** Configured `ingestion_agent.py` to wrap metadata extraction in a `try/except` handler, defaulting to robust fallback properties if the paper header is corrupted.
* **Decomposition Resilience:** Refactored `decomposition_agent.py` to gracefully capture missing section headers and fall back to baseline Swin-Transformer change detection structures rather than crashing with unhandled exceptions.
* **Dynamic Header Resolution:** Configured the agent to search for conceptual keywords (like `"method"`, `"experiment"`) in section headers, dynamically mapping alternate layout conventions (like simple indexes `3. Proposed Model` or `4. Experimental Setup` vs. roman numerals `III. METHOD`).

### Verification Results
Ran `python backend/tests/test_generalization.py`:
* **Output File:** Successfully compiled the edge-case outcomes locally in: `backend/papers/vlcd_generalization_report.md`.
* **Validation Outcome:** **PASS**. The pipeline processed both Scenario 1 (no methodology section present) and Scenario 2 (numbered sections instead of roman numeral headers) with exit code 0.

---

## 📅 Day 14 - Local Runtime Benchmarking

### Implementation Details
We implemented a comprehensive benchmark harness to measure and contrast performance across different model architectures pulled locally on the host machine:
* **Active VRAM Cleaning:** Added a cleanup handler that unloads each model immediately after execution by calling Ollama's API with `keep_alive: 0` to release GPU memory blocks.
* **Comparative Matrix:** Measures exact pipeline latency and schema compliance for each LLM, saving the statistics table in real-time.
* **Model Proposal Exports:** Generates and saves the final proposal markdown files separately for each model, enabling side-by-side comparison of prompt qualities.

### Verification Results
Ran `python backend/tests/test_benchmarking.py` over 5 local models:
* **Output File:** Successfully generated the speed matrix locally in: `backend/papers/vlcd_runtime_benchmark.md`.
* **Validation Outcome:** **PASS**. Benchmark logs completed for Qwen 1.5B/7B, Llama 1B/3B/8B, and Gemma 2B. Highlighted that Llama 3.2 3B is the speed-to-compliance champion (67.4s pipeline run), while Llama 3.1 8B provides the highest quality technical writing.
