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


