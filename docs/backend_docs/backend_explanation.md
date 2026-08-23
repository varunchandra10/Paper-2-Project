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
