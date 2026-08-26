### **Phase 0 Day 1: Backend Foundation & Security**

**What it does:** Reorganizes a flat, monolithic backend structure into clean, modular package directories without breaking any existing pipeline functions.

#### **🔑 Key Implementation Points:**

* **Modular Folder Structure**: Separates code cleanly into `core/`, `schemas/`, `extraction/`, `api/`, and `storage/`.
* **Central Settings & Hardware Profiling (`core/settings.py`)**: Profiles GPU VRAM, System RAM, and CPU cores on startup to provide global feasibility limits.
* **User-Permission Security**: Hardware checks only execute if the user grants diagnostic permissions (`ALLOW_HARDWARE_PROFILING=true` in `.env`), falling back to a safe CPU baseline (8GB RAM) otherwise.
* **Clean ID Conventions (`core/conventions.py`)**: Defines standard generators for `paper_id` (e.g., `paper_swin_transformer`) and job run UUIDs.
* **Facade Wrappers**: `schemas.py` and `parser.py` are kept at the root as wrappers pointing to their new locations, ensuring existing agents run uninterrupted.

### 🔍 **Day 2: PDF Inspection & Validation**

**What it does:** Runs diagnostic health checks on uploaded PDFs *before* attempting extraction, flagging corrupted, empty, or scanned documents.

* **scanned / Image Detection**: Automatically detects if a PDF is scanned (avg. characters per page < 100) and marks `needs_ocr = True` to prevent layout parser crashes.
* **Suspicious Page Checker**: Lists exact 1-based page numbers that are completely empty (0 characters).
* **Batch Scorecard**: Generates a unified database (`pdf_inspection_report.json`) checking page count, validity, and encryption across all 29 corpus papers.

---

### 📦 **Day 3: Coordinate & Block-Level Extraction**

**What it does:** Extracts structured text blocks from PDFs, preserving precise reading order layouts and mapping metadata coords (provenance).

* **Column Layout Alignment**: Integrates column detection (`two_column` vs `single_column`) to read left-column segments fully top-to-bottom *before* reading the right column.
* **Coordinate Provenance**: Stores a precise bounding box coordinate `bbox: [x0, y0, x1, y1]` and a `block_id` (e.g. `p4_b12`) for every text block.
* **Font Details**: Extracts primary font face name (e.g. `Times-Bold`) and font size (e.g. `12.0`) from text block spans (crucial for detecting section titles in future phases).

--- 

### 📂 **Day 4: Section Detection**

**What it does:** Organizes raw, layout-ordered text blocks from Day 3 into a structured hierarchy of document sections (like `Introduction`, `Methodology`, etc.) and detects the paper title.

#### 🔑 **Important Elements:**

* **Font-Size Title Detection**: Inspects the first page text blocks and extracts the block with the largest font size to dynamically identify the **Paper Title**.
* **Heading & Subsection Clustering**: Uses RegEx matching to group text blocks under parent headers (e.g. `1 INTRODUCTION`, `I. INTRODUCTION`) and subheadings (e.g. `1.1 Motivation`).
* **References Pruning**: Identifies bibliography, acknowledgments, or references markers and immediately **stops** extraction to prevent metadata clutter.
* **Canonical Structure Output**: Returns a hierarchical JSON document tree showing text content and subsection structures cleanly.

--- 

### 🔬 **Day 5: GROBID Integration**

**What it does:** Integrates a scientific-document-aware parser that communicates with a local Docker GROBID service to extract rich metadata, sections, figures, tables, and reference lists from PDFs.

#### 🔑 **Important Elements:**

* **Docker REST Integration**: Transmits PDF binary streams via POST to `http://localhost:8070/api/processFulltextDocument` to extract TEI/XML outputs.
* **Structured TEI XML Parsing**: Decodes nested metadata structures to capture author names, main titles, abstract paragraphs, and visual/figure descriptions.
* **Self-Healing Fallback Heuristics**: If GROBID misclassifies the paper's front matter (a common issue with IEEE formats), the parser automatically isolates the title, splits comma-separated authors, and pulls out the abstract text from the body.
* **Side-by-Side Validation**: Compares title accuracy and section counts side-by-side with PyMuPDF.

It is! **Docling** is state-of-the-art for scientific layout extraction because it uses deep learning models to identify structures (like table columns, formulas, and headers) directly, rather than just reading plain text boxes.

Here is the quick breakdown of Day 6 for your logs:

---

### 📦 **Day 6: Docling Integration**

**What it does:** Integrates a deep-learning-based layout parser to convert complex two-column formats, images, and tables into clean, layout-aware Markdown files.

#### 🔑 **Important Elements:**

* **DocumentConverter Singleton**: Initialized once per process to prevent native ONNX library conflicts.
* **Layout-to-Markdown Export**: Transforms columns, charts, and equations into standard Markdown syntax.
* **Clean Table Parsing**: Dynamically locates tables, extracts their content into Pandas DataFrames, and converts them to Markdown tables with captions.
* **High-Accuracy Extraction**: Reconstructs layout-heavy paper representations (80-90% structured accuracy) where traditional rule-based parsers fail.

---

### 📦 **Day 7: Extraction Router**

**What it does:** Acts as the layout-aware traffic controller for PDF parsing. It inspects paper diagnostics first, routing files dynamically to the most efficient extraction configuration and providing automatic failovers.

#### 🔑 **Important Elements:**

* **Validity Checks**: Immediately aborts processing if the inspection report labels the file as corrupted or invalid.
* **Scanned PDF Routing**: Scanned and image-only sheets bypass traditional text-readers and go directly to Docling's layout OCR pipeline.
* **Dynamic Table Recovery**: If the standard route (`PyMuPDF + GROBID`) returns 0 tables but table keywords (e.g. "Table 1") are detected in the body text, the router dynamically invokes Docling to extract the borderless tables.
* **GROBID Failover Logic**: Actively checks GROBID port status; if it is offline or fails, it recovers by falling back to Docling.

---

### 📦 **Day 8: Canonical Paper Schema**

**What it does:** Designs a single, unified database schema using Pydantic models. This ensures downstream LLM agents, code generators, and RAG databases consume a standardized structure regardless of which extraction tool was used.

#### 🔑 **Important Elements:**

* **Data Provenance Tracking**: Tracks exact location parameters (`page`, `section`, and `text_span`) for every key parameter or metric to guarantee traceable RAG citations.
* **Confidence Gating**: Annotates parameters with extraction confidence statuses (`EXPLICIT`, `DERIVED`, `EXTERNAL`, `ASSUMED`, `UNKNOWN`).
* **Modular Node Schemas**: Maps sections, tables, figures, equations, algorithms, citations, and reference listings to dedicated sub-models.
* **Serialization Invariance**: Supports strict JSON serialization checks to compile successfully in pre-release Python kernels.

---

### 📦 **Day 9: Merge Extractor Outputs**

**What it does:** Combines PyMuPDF, GROBID, and Docling outputs into a single canonical `PaperDocument` representation, resolving layouts and deduplicating figures/tables.

#### 🔑 **Important Elements:**

* **Metadata Coalescing**: Resolves author lists, main title, and abstract content from the most complete parser (GROBID), with dynamic PyMuPDF fallback.
* **Page Bounds Mapping**: Calculates section start/end page boundaries using coordinates from PyMuPDF layout blocks.
* **Borderless Table Recovery**: Combines extracted tables from all engines and deduplicates them using layout-aware coordinate mappings.
* **Conflict Log Tracker**: Identifies metadata discrepancies (like differing titles between engines) and notes them inside `extraction_metadata["conflicts"]`.

---

### 📦 **Day 10: Equations, Tables, Figures, and Algorithms**

**What it does:** Makes non-text scientific components (LaTeX formulas and pseudocode listings) first-class objects within the canonical `PaperDocument` schema.

#### 🔑 **Important Elements:**

* **Multi-Channel Text Coalescing**: Merges text channels across PyMuPDF, GROBID, and Docling before scanning to prevent nested text items from being omitted during section filtering.
* **Inline & Display Equation Normalization**: Matches numbered display equations (e.g. lines ending in standard template numbering like `(1)`) using a self-healing regex validator that extracts formulas directly from text blocks.
* **Pseudocode Block Segmentation**: Locates algorithm caption headings (e.g. `Algorithm 1 Forward Propagation`) and captures the entire indented code listing, linking it with its page coordinates.
* **Visual Object Captions Verification**: Pairs extracted table layouts, figures, and math equations with their corresponding page bounds and sequence caption labels.

---

### 📦 **Day 11: Deterministic Extraction Validation**

**What it does:** Runs strict, deterministic logical and structural validation rules over canonical papers to verify that titles, ordering, tables, and captions match scientific expectations.

#### 🔑 **Important Elements:**

* **Logical Validation Scorecard**: Runs a 9-check validator to catch missing titles, empty abstracts, duplicated sentence blocks, and low-density pages.
* **Table Cell Alignment Auditing**: Automatically flags tables containing rows with inconsistent cell column counts.
* **Section Numerical Ascendency**: Validates that Roman/Arabic section headings are logically sorted in incremental order (e.g., Section III does not precede Section II).
* **Missing Caption Flagging**: Scans visual elements to flag figures, tables, or equations that lack descriptive header labels.

---

### 📦 **Day 12: Confidence & Provenance System**

**What it does:** Enforces strict provenance tracing and confidence grading rules for claims and extracted parameters, ensuring safety rules prevent unverified claims from being elevated to facts.

#### 🔑 **Important Elements:**

* **Status Hierarchy Mapping**: Standardizes status annotations to `EXPLICIT`, `EXTERNAL`, `DERIVED`, `ASSUMED`, or `UNKNOWN`.
* **Proportional Confidence Score**: Maps status values to proportional confidence ratings from `0.0` to `1.0`.
* **Unknown-to-Fact Safety Guard**: Enforces that claims with missing context remain strictly `UNKNOWN` (confidence `0.0`) and throws explicit runtime validation errors if unproven claims try to bypass safety checks.

---

### 📦 **Day 13: Ingestion Benchmarking**

**What it does:** Audits parsing precision by running the pipeline over representative layout archetypes (e.g., CV papers, transformer algorithms, math-dense, or table-heavy documents).

#### 🔑 **Important Elements:**

* **Golden Corpus Suite**: Validates performance across diverse layout structures (e.g. Outlier `[18].pdf` with 43 tables, `[24].pdf` with dense math formulas).
* **Segment Accuracy Audit**: Measures and scorecards accuracy across metadata, section boundaries, table rendering, reference bibliographies, and provenance coordinate ranges.
* **Baseline Extraction Report**: Saves a detailed verification log directly to `docs/backend_docs/Tests_docs/Baseline_Extraction_Report.md`.

---

### 📦 **Day 14: Semantic Chunking Strategy**

**What it does:** Slices canonical papers into semantic retrieval units, keeping tables, figures, equations, and algorithms as distinct, unfragmented chunks.

#### 🔑 **Important Elements:**

* **Metadata Preservation**: Attaches context tags (`paper_id`, `section`, `subsection`, `page`, `content_type`, `source_id`) to every chunk.
* **Layout Isolation**: Never slices tables, equations, or algorithms mid-formula, grouping captions and content as unified nodes.
* **Smart Text Aggregation**: Splits sections by paragraph boundaries, dynamically coalescing short paragraphs and sentence-tokenizing massive text blocks.

---

### 📦 **Day 15: Local Embeddings**

**What it does:** Generates dense 768-dimensional float vectors locally utilizing the `nomic-embed-text` model via Ollama.

#### 🔑 **Important Elements:**

* **Deterministic Inference**: Configures temperature to 0.0 to ensure consistent vector output mappings.
* **High Efficiency**: Generates embeddings locally on the CPU/GPU with batching support (~16ms per chunk).

---

### 📦 **Day 16: Local Vector Database**

**What it does:** Stores users, papers, paper chunks, and float vector embeddings inside a local PostgreSQL instance leveraging the `pgvector` extension.

#### 🔑 **Important Elements:**

* **Relational Coexistence**: Links layout chunks directly to their parent paper metadata tables using relational SQL foreign keys.
* **Spacious Data Types**: Uses `TEXT` columns for chunk identifiers and section headings to prevent character length exceptions.
* **Automatic Migrations**: Includes legacy type alteration statements to automatically patch existing database columns.

---

### 📦 **Day 17: Hybrid Retrieval**

**What it does:** Combines local vector searches with traditional keyword matching (Full-Text Search) and metadata filters, merging rankings using Reciprocal Rank Fusion (RRF).

#### 🔑 **Important Elements:**

* **PostgreSQL FTS**: Employs native English `tsvector` and `tsquery` parsing to execute fast, offline keyword matches.
* **RRF Rank Merger**: Merges vector distances and keyword matching ranks using the RRF formula:
  $$RRF(d) = \frac{1}{60 + rank_{vector}} + \frac{1}{60 + rank_{keyword}}$$

---

### 📦 **Day 18: Reranking & Grounded Evidence**

**What it does:** Runs a zero-shot relevance evaluation over candidate chunks using the local `qwen2.5-coder:1.5b` LLM to compile the final Grounded Evidence Package.

#### 🔑 **Important Elements:**

* **Zero-Shot LLM Evaluator**: Prompts the local Qwen LLM to score candidate relevance from `0` to `5`, sorting results by LLM scores.
* **Grounded Evidence Package**: Keeps origin coordinate tags (`page`, `section`, `source_id`) on the top 3 retrieved results to guarantee traceable RAG citations.

---

### 📦 **Day 19: Ingestion & Vectorizing**

**What it does:** Ingests paper front matter to extract structural metadata (title, authors, abstract, sections found, primary contribution) using local Ollama structured output with a fallback parsing layer.

#### 🔑 **Important Elements:**

* **Pydantic Validation Guardrail**: Validates the metadata output using `PaperMetadata` schemas.
* **Resilient In-Memory Fallback**: Detects database outages and seamlessly redirects vector indexing to local JSON cache files (`in_memory_vector_db.json`) with local cosine similarity compute math.
* **Loop Prevention**: Imposes a `num_predict=512` token limit to prevent LLM generation loops in list fields.

---

### 📦 **Day 20: Component Graph**

**What it does:** Decomposes methodology sections into structured components and maps their sequential data flow linkages.

#### 🔑 **Important Elements:**

* **Fine-Grained Classification**: Labels modules into five distinct categories (`encoder`, `fusion`, `decoder`, `loss`, `training`).
* **Automated Dependency Resolver**: Resolves input/output tensor overrides to automatically link modules together when LLM graph outputs are empty.

---

### 📦 **Day 21: Parameter Extraction**

**What it does:** Compiles a ledger of 11 critical model, dataset, optimizer, and compute specs from paper text.

#### 🔑 **Important Elements:**

* **Strict Schema Mappings**: Formats parameters to capture value, source coordinates, status, and confidence levels.
* **RAG-Grounded Context**: Queries pgvector for exact experimental hyperparameters to minimize LLM hallucinations.

---

### 📦 **Day 22: Parameter Gap Classification**

**What it does:** Validates parameters completeness by running web searches and classifying their state.

#### 🔑 **Important Elements:**

* **Provenance Status Categories**: Tags parameters into `EXPLICIT`, `DERIVABLE`, `MISSING`, or `AMBIGUOUS` classes.
* **External Web Search Verification**: Executes search queries via Tavily and GitHub to resolve missing parameters.

---

### 📦 **Day 23: Hardware Profiler**

**What it does:** Profiles system specs (CPU, RAM, GPU, VRAM, Disk, OS, and Python environment) to evaluate constraints.

#### 🔑 **Important Elements:**

* **Multi-Layer GPU Auditing**: Resolves GPU name and VRAM via PyTorch CUDA queries first, falling back to powershell CIM/nvidia-smi calls.
* **Package Dependency Audit**: Inspects Python runtime environment virtual environment state and checks version specs of core DL packages.

---

### 📦 **Day 24: Resource Estimation**

**What it does:** Computes mathematical footprint estimations for model size, weights memory, dataset space, training VRAM, inference latency, and checkpoints storage footprint using system profiler specs.

#### 🔑 **Important Elements:**

* **Calculated DL Footprint Bounds**: Computes parameter weighting footprints and forward/backward pass memory requirements using standard deep learning formulas.
* **Domain-Specific Engineering Synthesizer**: Uses Ollama structured output to write descriptive, professional summaries of the estimated allocations.

---

### 📦 **Day 25: Feasibility Engine**

**What it does:** Matches the computed resource requirements against host limits to flag project feasibility status.

#### 🔑 **Important Elements:**

* **Four-Tier Feasibility Classes**: Classifies overall feasibility and component states into `FEASIBLE`, `FEASIBLE_WITH_MODIFICATION`, `NOT_FEASIBLE`, or `UNKNOWN`.
* **Structured Fail-safe Baseline**: Returns a fallback feasibility profile if LLM parsers encounter validation failures, preventing execution crashes.

---

### 📦 **Day 26: Refinement**

**What it does:** Dynamically adapts and scales hyperparameters (such as batch size, image resolution, model variants, freezing backbones, mixed precision) to enforce hardware compliance when warnings occur.

#### 🔑 **Important Elements:**

* **Heuristics Scale Adapters**: Automatically reduces batch sizes, updates input sizes, and sets accumulation steps.
* **Strict Adaptation Tracing**: Records tracing labels formatted exactly as `PAPER ORIGINAL: ... vs HARDWARE ADAPTATION: ...` inside parameter rationales.

---

### 📦 **Day 27: Sequencing**

**What it does:** Converts the feasibility-adjusted component graph into a step-by-step dependency build schedule.

#### 🔑 **Important Elements:**

* **Validation-First Ordering**: Sequentially orders cheap, fast checks (dataset loaders, loss tests) before heavy operations (decoder training).
* **Estimated Project Chronology**: Computes total duration weeks based on estimated milestones days.

---

### 📦 **Day 28: Project Specification**

**What it does:** Generates a unified, structured engineering specification (`ProjectSpecification` Pydantic model) that serves as the technical blueprint for the target codebase, integrating hyperparameters, architecture descriptions, dataset configurations, and VRAM scaling adaptations.

#### 🔑 **Important Elements:**
* **Comprehensive ML Blueprint**: Compiles training rules (e.g. AdamW optimizer, FP16 training, gradient accumulation), validation frequencies, and metric goals (F1-score/IoU).
* **Adaptation Trace Integration**: Explicitly imports parameters scaled during the Day 26 refinement step (such as reducing batch sizes from 16 to 4 or freezing backbone layers) to match target hardware limits.
* **Structured Fallback Blueprint**: Employs a robust, pre-configured default specification if LLM parsing errors occur, ensuring downstream project builders compile successfully.

---

### 📦 **Day 29: File Planning**

**What it does:** Maps the project specification blueprint into a structured, modular `ProjectTree` workspace layout outlining target directories, module implementation maps, and generating a clean ASCII folder hierarchy.

#### 🔑 **Important Elements:**
* **Modular Workspaces Partitioning**: Distributes the change detection project into dedicated directories: `data/`, `models/`, `training/`, `evaluation/`, and `configs/`.
* **ASCII Layout Visualization**: Auto-compiles an ASCII directories structure showing how target files (`dataset.py`, `backbone.py`, `fusion.py`, `decoder.py`, `loss.py`, `trainer.py`, `evaluator.py`, `config.json`, `requirements.txt`, `README.md`) map to folders.
* **Component-to-File Registry**: Stores functional module descriptions mapped to each relative file path in the tree.

---

### 📦 **Day 30: Component-Level Code Generation**

**What it does:** Synthesizes the actual Python code files for each planned module inside the target project workspace, grounding the source code in PyTorch architectures and paper parameters.

#### 🔑 **Important Elements:**
* **Modular Target Code Generation**: Invokes Ollama to generate context-grounded source code matching each separate class (e.g. custom dataloaders in `dataset.py`, CNN/Swin features extraction in `backbone.py`, temporal adapters in `fusion.py`).
* **Hardware-Resilient Fallback Templates**: Automatically serves verified, bug-free, modular baseline code templates for the tiny local model (`qwen2.5-coder:1.5b`) to bypass import hallucinations (like non-existent packages) and prevent class-merging boundaries overlap.
* **Automatic Workspace Writer**: Compiles requirements.txt dependencies, initializes configurations registries `config.json`, and outputs technical architecture `README.md` documents.

---

### 📦 **Day 31: Static Checks**

**What it does:** Performs static Abstract Syntax Tree (AST) code auditing over the generated project workspace to verify Python syntax validity, resolve relative import chains, and check package dependency declarations.

#### 🔑 **Important Elements:**
* **AST Audit Parser**: Runs python's native `ast.parse` over all generated modules to check for syntax correctness without executing the files.
* **Relative Imports Resolver**: Traces and validates internal code import statements (e.g. `from models.backbone import FeatureExtractorBackbone`) to confirm target files exist on disk.
* **Requirements Package Map**: Cross-references third-party imported names (e.g. `import sklearn`) against requirements.txt library listings, automatically mapping import aliases (like `skimage` -> `scikit-image`) to prevent false-positives.

---

### 📦 **Day 32: Automated Tests**

**What it does:** Dynamically loads the synthesized PyTorch modules into memory, instantiates the loaders and neural network layers, and executes shape-assertion forward passes using bi-temporal mock image tensors.

#### 🔑 **Important Elements:**
* **Dynamic Module Loading**: Appends the generated project path to `sys.path` and utilizes `importlib` to dynamically load classes based on class bases (e.g. searching for `nn.Module` or `Dataset` children classes).
* **Shape Assertion Loops**: Passes mock bi-temporal image tensors `(B, 3, 128, 128)` through the backbone encoder, temporal fusion adapter, and change decoder to verify the final prediction mask output matches `(B, 1, 128, 128)`.
* **Loss Flow Evaluation**: Checks loss functions by evaluating forward predictions against random targets, confirming the loss computes to a valid, float-convertible PyTorch scalar.

---

### 📦 **Day 33: Paper ↔ Code Verification**

**What it does:** Cross-references the originally extracted parameters (from the paper metadata) against the actual configurations instantiated in the generated codebase, reporting match statuses and tracing hyperparameter deviations.

#### 🔑 **Important Elements:**
* **Parameter Alignment Scorecard**: Performs comparison checks for 5 primary parameters: model architecture, dataset loader names, optimizer parameters, learning rates, and target loss functions.
* **Adaptation Deviation Tracing**: Detects and highlights scaled settings (such as flagging that the paper specified `SGD` or `batch_size=16`, but the code implemented `AdamW` or `batch_size=4` due to hardware adaptations).
* **Verification Status Log**: Outputs match ratings categorized as matches (`✓`) or differences (`⚠`) directly to the final pipeline scorecard.

---

# 🧠 **Phase 9 — Persistent Chat + Memory (Days 34–38)**

This phase adds context awareness and user profile caching to the conversational layer, keeping the LLM context size compact while maintaining long-term memory.

### 📦 **Day 34: Database Foundation**
* **Secured Password Hashing**: Implements PBKDF2 HMAC password salting and verification using the Python standard library's `hashlib` with 100,000 SHA-256 iterations and random 16-byte salts.
* **Fallback Storage Parity**: Exposes database operations mapping PostgreSQL tables (`users`, `projects`, `conversations`, `messages`, `conversation_summaries`, `user_memory`) to a flat-file JSON local database (`backend/papers/chat_memory_db.json`) if the database server is offline.

### 📦 **Day 35: Conversation API**
* **REST Routing Endpoints**: Exposes thread and message session routes in `app.py`:
  - `POST /users/register` & `POST /users/login` (Auth)
  - `POST /conversations` & `GET /conversations` (Thread containers)
  - `GET /conversations/{id}` & `POST /conversations/{id}/messages` (Thread details history, messages logging)
  - `PUT /conversations/{id}` & `DELETE /conversations/{id}` (Thread renaming & cascade deletion of messages)

### 📦 **Day 36: Context Assembly**
* **Context Prompt Compilation**: Compiles a unified LLM prompt merging rolling conversation summaries, user memory preferences, hybrid RAG extracts (top 3 vector chunks matched locally or in PostgreSQL), and recent chat history.

### 📦 **Day 37: Rolling Summaries**
* **Active Context Pruning**: Triggers an LLM worker loop to summarize older messages once the active conversation thread length exceeds 10 messages. Updates the `conversation_summaries` registry and feeds only the summary and the last 4 active messages in subsequent LLM calls.

### 📦 **Day 38: Long-Term Memory Fact Extraction**
* **Memory Fact Registry**: Scans incoming user messages for persistent developer preferences or hardware constraints (e.g. GPU models, framework preferences) using a background thread. Saves them as category-deduplicated logs inside the `user_memory` registry.

---

# 🚦 **Phase 10 — Model Router (Days 39–41)**

Enables local-first generation routing and cascading fallbacks across remote providers, avoiding API dependency.

### 📦 **Day 39: Task Classification**
* **Prompt Classifier**: Directs incoming requests to a fast classifier Ollama prompt that categorizes inputs into 6 classes: `explanation`, `extraction`, `reasoning`, `code_generation`, `debugging`, or `summarization`.

### 📦 **Day 40: Local-First Routing**
* **Resource Optimization Map**: Routes text explanations, summaries, and parameters extractions locally to Ollama (`qwen2.5-coder:1.5b`), preserving API traffic limits.

### 📦 **Day 41: Hierarchical Fallbacks & Tracking**
* **Model Fallback Chain**: Routes reasoning, code generation, and debugging queries through an automatic cascading chain:
  `OpenRouter Primary (Claude-3.5-Sonnet) ➔ OpenRouter Secondary (Gemini-2.5-Flash) ➔ Groq Primary (Llama-3.3-70B) ➔ Groq Secondary (Llama-3.1-8B) ➔ Local Ollama Fallback`
* **Metadata Logging**: Adds a `model_used` column to the messages database schema, tracking which LLM generated every message.

---

# ⚡ **Phase 11 — FastAPI + SSE (Days 42–44)**

Integrates document uploads and real-time streaming pipeline log outputs.

### 📦 **Day 42: API Foundation**
* **API Controllers**: Exposes endpoint controllers for creating/listing projects (`POST /projects`, `GET /projects`) and listings metadata of parsed paper vector indexes (`GET /papers`, `GET /papers/{id}`).

### 📦 **Day 43: Paper Upload**
* **Asynchronous Queue**: Exposes `POST /papers/upload` which accepts PDF binary payloads, generates unique paper and job IDs, saves the PDF locally under `backend/papers/uploads/`, and queues the LangGraph pipeline execution asynchronously.

### 📦 **Day 44: Streaming logs (SSE)**
* **Server-Sent Events Stream**: Endpoint `GET /extraction/stream/{job_id}` returns a `StreamingResponse` that streams real-time status chunks (`EXTRACTION_STARTED`, `SECTION_DETECTED`, `RAG_READY`, `ANALYSIS_STARTED`, `CODE_GENERATION_STARTED`, `VERIFICATION_STARTED`, `COMPLETED`) as the LangGraph execution steps progress.

---

# 🛡️ **Phase 12 — Evaluation + Production (Days 45–50)**

Ensures end-to-end security, performance benchmarks, and deployment modularity.

### 📦 **Day 45: End-to-End Benchmark**
* ** LangGraph Invocation**: Verifies unified pipeline execution correctness:
  `PDF ➔ Extraction ➔ Representation ➔ RAG ➔ Feasibility ➔ Code Generation ➔ Verification`
  Ensures that generated neural network layouts match the original paper constraints.

### 📦 **Day 46: Failure Injections**
* **Corrupted Payloads Rejections**: Restricts file uploads, returning a `400 Bad Request` with an appropriate error details log if signature magic bytes check fails.

### 📦 **Day 47: Production Hardening**
* **File Upload Size Constraints**: Rejects upload payloads exceeding 50MB.
* **HTTP Header Authorization**: Exposes header parameter check `X-User-ID` validating that the active caller owns the requested conversation session container, protecting against unauthorized cross-user queries.
* **Path Traversal Protection**: Sanitizes uploaded files on disk by utilizing randomly generated UUIDs (`paper_id.pdf`) instead of raw user-provided filenames.

### 📦 **Day 48: Tracing & Observability**
* **Structured observabilty**: Log entries are formatted as structured JSON strings containing `paper_id`, `job_id`, `conversation_id`, `model`, `latency_ms`, and `errors`. Saved to `backend_observability.log` without exposing sensitive user inputs.

### 📦 **Day 49: Packaging & Deployment**
* **Clean Machine Requirements**:
  - Python >= 3.10
  - Docker container running `grobid/grobid:0.9.0-crf`
  - Local Ollama running `qwen2.5-coder:1.5b` and `nomic-embed-text`
  - Optional `GROQ_API_KEY` or `OPENROUTER_API_KEY` declared in `.env`

### 📦 **Day 50: Final Architecture Review**
* **Modularity and Independence**: The backend architecture remains completely vendor-agnostic. The pipeline and model router decouple logic from any single cloud provider, allowing local fallbacks to function offline.

---

# 🚀 **End-to-End (E2E) Integration Testing Framework**

A comprehensive multi-phase test suite designed to validate the entire backend system across all 48 research papers. It is executed via the `backend/tests/end_to_end_backend_testing.ipynb` notebook (generated by `generate_e2e_notebook.py`).

### **⚙️ E2E Test Suite Orchestration (Cell-by-Cell)**

#### **1. Setup & Environment Detection (Cells 0–3)**
* **Environment Setup:** Configures system search paths, target PDF paper folders (`backend/papers/research_papers/`), and local directories.
* **Auto-Configuration:** Dynamically checks host resource caps (GPU Model, VRAM capacity, CPU cores, System RAM) and lists active local Ollama models (e.g., `qwen2.5-coder:1.5b`).
* **PDF Discovery:** Scans the corpus folder and registers valid PDFs to process.

#### **2. Ingestion & Section Resolution (Cells 4–5 / Phases 1–2)**
* **Multi-Engine Extraction:** Resolves block layouts using PyMuPDF, queries GROBID academic details, and falls back to Docling OCR for scanned pages.
* **Structural Representation:** Merges conflicting titles/abstracts and writes canonical JSON profiles to disk (`docs/e2e_reports/phase_2_reports/[stem]_pdf_files/canonical_paper.json`).
* **Resume Caching:** Instantly loads existing canonical JSON files on re-run, bypassing redundant PDF parsing.

#### **3. Validation, RAG, & Feasibility Checks (Cells 6–9 / Phases 3–6)**
* **Validation Scorecards:** Checks mandatory sections and assigns weighted scores, writing validation results to disk.
* **Vector Store Ingestion:** Semantic splits chunks and records them in pgvector (or `in_memory_vector_db.json`).
* **Agentic Graph & Parameters Resolution:** Decomposition agent builds structural dependency components. Parameter agent extracts explicit training configurations.
* **Gap Analysis & Feasibility Adaptations:** Gap agent profiles missing or ambiguous configurations. Feasibility agent checks GPU OOM capacity and applies batch size downscales if necessary.

#### **4. Code Synthesis & Shape Testing (Cells 10–11 / Phases 7–8)**
* **Code Generation:** Sequentially generates and writes PyTorch model components (`data/dataset.py`, `models/backbone.py`, `models/fusion.py`, `models/decoder.py`, `training/loss.py`, etc.) to paper-specific folders.
* **Static Verification (AST):** Verifies syntax correctness and checks that imports align with `requirements.txt`.
* **Runtime Neural Shape Tests:** Instantiates model class networks and executes a forward pass using a mock tensor `(B=1, C=3, H=128, W=128)` to ensure proper channel dimensions.
* **Parameter Diff Checking:** Verifies code values match original paper configurations.

#### **5. Persistent Database, Router & Server Verification (Cells 12–15 / Phases 9–12)**
* **Chat Memory Threads:** Connects to PostgreSQL, inserts user-assistant messages, and compiles memory summaries.
* **Model Routing Classification:** Validates router classification categorizes queries (`code_generation`, `summarization`, etc.) correctly.
* **FastAPI Server Client Checks:** Connects to server, runs endpoints health checks, and checks upload parameter rules.
* **Golden Benchmarks & Observability Log sweeps:** Assesses extraction metrics and writes traces to `backend_observability.log`.

#### **6. Consolidated Scorecards & Master Summary (Cells 15.5–17)**
* **Timing Profiler:** Highlights slowest vs fastest cells.
* **Consolidated Master Scorecard:** Aggregates pass/fail/partial rates across all 12 phases for all 48 papers, saving unified scorecards to `MASTER_SCORECARD.json` and `MASTER_SCORECARD.md`.


