# Paper-to-Project --- Backend Implementation Roadmap

## Purpose

This roadmap updates the existing backend phases without throwing away
the work already completed.

The main architectural decision is:

> **Paper extraction and canonical paper representation are the
> foundation.**

Everything else --- RAG, paper understanding, feasibility, code
generation, memory, model routing, and chat --- should consume this
reliable representation.

The implementation is intentionally **day-wise** so each day has a
concrete deliverable and a testable stopping point.

------------------------------------------------------------------------

# Current Backend Direction

``` text
PDF
 ↓
Phase 1 — Scientific Paper Extraction
 ↓
Phase 2 — Canonical Paper Representation
 ↓
Phase 3 — Extraction Validation
 ↓
Phase 4 — RAG / Paper Knowledge Layer
 ↓
Phase 5 — Paper Understanding
 ↓
Phase 6 — Feasibility + Adaptation
 ↓
Phase 7 — Code Generation
 ↓
Phase 8 — Code Verification
 ↓
Phase 9 — Chat + Memory
 ↓
Phase 10 — Model Router
 ↓
Phase 11 — FastAPI + SSE
 ↓
Phase 12 — Evaluation + Production
```

The existing decomposition → gap finding → feasibility → refinement →
sequencing → report work is preserved and moved into the appropriate
phases.

------------------------------------------------------------------------

# Phase 0 --- Backend Foundation

## Day 1 --- Freeze the architecture and clean boundaries

### Objectives

-   Separate extraction, agents, retrieval, memory, APIs, and model
    routing.
-   Stop adding features directly into the current monolithic pipeline.
-   Define interfaces between modules.

### Tasks

-   Create/clean package structure:
    -   `extraction/`
    -   `models/`
    -   `agents/`
    -   `retrieval/`
    -   `memory/`
    -   `services/`
    -   `api/`
    -   `tests/`
    -   `storage/`
    -   `core/`
-   Move configuration into a central settings module.
-   Add logging and consistent exception handling.
-   Define `paper_id`, `job_id`, and later `conversation_id`
    conventions.

### Output

A clean backend skeleton with no change in existing functionality.

### Done when

The current Phase 1 pipeline still runs after the restructuring.

------------------------------------------------------------------------

# Phase 1 --- Scientific Paper Extraction ⭐ Highest Priority

## Day 2 --- PDF inspection and validation

### Objectives

Know what kind of PDF entered the system before choosing an extraction
path.

### Tasks

Build a PDF inspector using PyMuPDF.

Detect: - valid/invalid PDF - page count - text presence - image
presence - scanned/image-only pages - encrypted PDFs - approximate text
coverage - suspicious/empty pages

### Output

``` json
{
  "paper_id": "paper_001",
  "pages": 12,
  "has_text": true,
  "has_images": true,
  "is_scanned": false,
  "needs_ocr": false
}
```

### Done when

The inspector correctly classifies a test set of different PDFs.

------------------------------------------------------------------------

## Day 3 --- Improve raw PyMuPDF extraction

### Objectives

Turn raw PDF text into reliable page/block-level data.

### Tasks

Extract: - page number - text blocks - bounding boxes - font information
where useful - images - page-level text - block ordering

Preserve provenance:

``` text
paper_id
page_number
block_id
bbox
raw_text
```

### Output

``` json
{
  "page": 4,
  "blocks": [
    {
      "block_id": "p4_b12",
      "text": "...",
      "bbox": [x0, y0, x1, y1]
    }
  ]
}
```

### Done when

Text can be reconstructed page-by-page without losing source location.

------------------------------------------------------------------------

## Day 4 --- Section detection

### Objectives

Stop relying on one paper's exact section names.

### Tasks

Detect: - title - abstract - introduction - related work - methodology -
experiments - results - conclusion - references - subsections

Support variants such as:

``` text
Methodology
Methods
Proposed Method
Approach
Materials and Methods
```

Use deterministic heuristics first.

### Output

``` text
1 Introduction
2 Related Work
3 Proposed Method
  3.1 Architecture
  3.2 Training
4 Experiments
5 Results
6 Conclusion
```

### Done when

Section detection works on at least 5 structurally different papers.

------------------------------------------------------------------------

## Day 5 --- GROBID integration

### Objectives

Add a scientific-document-aware extraction path.

### Tasks

-   Run GROBID locally.
-   Send supported PDFs to GROBID.
-   Parse returned TEI/XML.
-   Extract:
    -   metadata
    -   sections
    -   paragraphs
    -   figures
    -   tables
    -   captions
    -   references
    -   citations

### Output

A normalized GROBID result independent of raw TEI XML.

### Done when

The same paper can be extracted using both PyMuPDF and GROBID.

------------------------------------------------------------------------

## Day 6 --- Docling integration

### Objectives

Handle layout-heavy scientific content.

### Tasks

Test Docling on: - two-column papers - tables - figures - equations -
complex layouts

Generate structured Markdown/JSON where appropriate.

### Output

``` text
PDF
 ↓
Docling
 ↓
layout-aware document
```

### Done when

You can identify cases where Docling provides information PyMuPDF/GROBID
misses.

------------------------------------------------------------------------

## Day 7 --- Extraction router

### Objectives

Don't blindly run every extractor.

### Design

``` text
PDF
 ↓
Inspector
 ↓
Extraction Router
 ├── PyMuPDF
 ├── GROBID
 ├── Docling
 └── OCR fallback
```

### Rules

Examples:

``` text
Normal scientific PDF
→ PyMuPDF + GROBID

Complex layout
→ PyMuPDF + GROBID + Docling

Scanned PDF
→ OCR + layout extraction

Failed GROBID
→ PyMuPDF/Docling fallback
```

### Output

A single extraction job that selects appropriate tools.

### Done when

A paper can pass through extraction without manually choosing a parser.

------------------------------------------------------------------------

# Phase 2 --- Canonical Paper Representation ⭐

## Day 8 --- Design the Paper schema

### Objectives

Create one canonical representation independent of extraction library.

### Core schema

``` json
{
  "paper": {},
  "metadata": {},
  "sections": [],
  "figures": [],
  "tables": [],
  "equations": [],
  "algorithms": [],
  "citations": [],
  "references": [],
  "pages": [],
  "extraction_metadata": {}
}
```

### Important rule

Every important object should contain provenance.

Example:

``` json
{
  "value": "Adam",
  "source": {
    "page": 7,
    "section": "Training Details",
    "text_span": "..."
  },
  "status": "EXPLICIT"
}
```

### Done when

Pydantic models can represent an entire extracted paper.

------------------------------------------------------------------------

## Day 9 --- Merge extractor outputs

### Objectives

Combine:

``` text
PyMuPDF
GROBID
Docling
```

into one canonical representation.

### Tasks

-   Match pages.
-   Match sections.
-   Deduplicate paragraphs.
-   Merge figure/table metadata.
-   Preserve source provenance.
-   Record conflicts.

### Output

``` text
UnifiedPaper
```

### Done when

Changing the extraction engine does not require changing downstream
agents.

------------------------------------------------------------------------

## Day 10 --- Equations, tables, figures and algorithms

### Objectives

Make non-text content first-class.

### Tasks

Represent:

``` text
Equation
Table
Figure
Caption
Algorithm/Pseudocode
```

with page and source information.

### Output

``` json
{
  "type": "equation",
  "page": 8,
  "content": "...",
  "confidence": "..."
}
```

### Done when

A paper's important visual/scientific objects are not lost during
normalization.

------------------------------------------------------------------------

# Phase 3 --- Extraction Validation ⭐

## Day 11 --- Deterministic extraction validation

### Checks

-   missing title
-   missing abstract
-   broken section ordering
-   duplicated text
-   suspicious empty pages
-   missing references
-   abnormal text coverage
-   malformed tables
-   missing captions

### Output

``` text
Extraction Quality Report

✓ Title
✓ Authors
✓ Abstract
✓ Sections

⚠ Equation 8 uncertain
⚠ Figure 4 needs visual inspection
✓ References
```

------------------------------------------------------------------------

## Day 12 --- Confidence and provenance system

### Standardize statuses

``` text
EXPLICIT
DERIVED
EXTERNAL
ASSUMED
UNKNOWN
```

### Rule

Never silently convert:

``` text
UNKNOWN → FACT
```

### Output

Every important claim has:

``` text
value
status
confidence
source
```

------------------------------------------------------------------------

## Day 13 --- Extraction benchmark

### Build a test corpus

Use at least: - CV paper - NLP paper - transformer/LLM paper - computer
vision paper - non-ML technical paper - difficult two-column paper -
paper with many equations - paper with many tables

### Measure

``` text
metadata accuracy
section accuracy
text coverage
figure detection
table detection
equation detection
reference extraction
provenance correctness
```

### Output

Baseline extraction report.

------------------------------------------------------------------------

# Phase 4 --- RAG / Paper Knowledge Layer

## Day 14 --- Chunking strategy

### Objective

Create retrieval units that preserve scientific meaning.

Don't use blind fixed-size chunks only.

Include metadata:

``` text
paper_id
section
subsection
page
content_type
source_id
```

### Output

Searchable paper chunks.

------------------------------------------------------------------------

## Day 15 --- Local embeddings

### Objective

Avoid API cost for embeddings.

### Tasks

-   Choose a local embedding model.
-   Generate embeddings locally.
-   Store vectors.
-   Benchmark embedding generation speed and memory.

### Output

``` text
Paper chunks
 ↓
Local embeddings
 ↓
Vector store
```

------------------------------------------------------------------------

## Day 16 --- Vector database

### Recommended direction

Use PostgreSQL + pgvector if practical so relational data and vectors
can coexist.

Store:

``` text
users
papers
paper_chunks
embeddings
```

### Done when

A query can retrieve semantically relevant paper chunks.

------------------------------------------------------------------------

## Day 17 --- Hybrid retrieval

Implement:

``` text
Vector search
+
Keyword/BM25 search
+
Metadata filtering
```

Then combine results.

### Example

Query:

> What optimizer and learning rate were used?

Should search for:

``` text
optimizer
learning rate
training
hyperparameters
```

not only semantically similar sentences.

------------------------------------------------------------------------

## Day 18 --- Reranking and evidence

### Objective

Improve retrieval quality.

Pipeline:

``` text
Query
 ↓
Vector + Keyword Retrieval
 ↓
Candidate chunks
 ↓
Reranker
 ↓
Top evidence
```

Every retrieved result should retain:

``` text
page
section
source_id
```

### Output

Grounded evidence package.

------------------------------------------------------------------------

# Phase 5 --- Paper Understanding

## Day 19 --- Restore existing ingestion/decomposition pipeline

Bring your existing work back on top of:

``` text
Canonical Paper
+
RAG evidence
```

Keep: - ingestion - decomposition - component identification -
confidence tracking

------------------------------------------------------------------------

## Day 20 --- Component graph

Convert paper methodology into structured components.

Example:

``` text
Dataset
 ↓
Preprocessing
 ↓
Encoder
 ↓
Feature Fusion
 ↓
Decoder
 ↓
Loss
 ↓
Training
```

### Output

A machine-readable dependency/component graph.

------------------------------------------------------------------------

## Day 21 --- Parameter extraction

Extract important parameters:

``` text
model
dataset
optimizer
learning rate
batch size
epochs
loss
scheduler
input size
augmentation
hardware
```

Every parameter must retain:

``` text
value
source
status
confidence
```

------------------------------------------------------------------------

## Day 22 --- Gap finding

Restore and improve the existing gap-finding phase.

Classify:

``` text
EXPLICIT
DERIVABLE
MISSING
AMBIGUOUS
```

Example:

``` text
Learning rate → EXPLICIT
Batch size → EXPLICIT
GPU → MISSING
Preprocessing detail → AMBIGUOUS
```

------------------------------------------------------------------------

# Phase 6 --- Feasibility + Adaptation

## Day 23 --- Hardware profiler

Preserve your existing hardware profiling work.

Collect:

``` text
CPU
RAM
GPU
VRAM
disk
OS
Python environment
```

------------------------------------------------------------------------

## Day 24 --- Resource estimation

Estimate requirements for:

``` text
model
dataset
training
inference
storage
```

------------------------------------------------------------------------

## Day 25 --- Feasibility engine

Produce:

``` text
FEASIBLE
FEASIBLE_WITH_MODIFICATION
NOT_FEASIBLE
UNKNOWN
```

------------------------------------------------------------------------

## Day 26 --- Refinement

Keep your existing refinement logic.

Examples:

``` text
batch size ↓
image size ↓
model variant ↓
gradient accumulation ↑
freeze layers
use mixed precision
```

Important:

Every modification must be labelled:

``` text
PAPER ORIGINAL
vs
HARDWARE ADAPTATION
```

------------------------------------------------------------------------

## Day 27 --- Sequencing

Restore your existing sequencing phase.

Generate:

``` text
Environment
 ↓
Dataset
 ↓
Preprocessing
 ↓
Model components
 ↓
Training
 ↓
Evaluation
```

with dependencies.

------------------------------------------------------------------------

# Phase 7 --- Code Generation

## Day 28 --- Project specification

Convert the blueprint into:

``` text
ProjectSpecification
```

containing:

``` text
requirements
architecture
components
dependencies
datasets
training setup
evaluation
assumptions
adaptations
```

------------------------------------------------------------------------

## Day 29 --- File planning

Generate a deterministic project tree.

Example:

``` text
project/
├── data/
├── models/
├── training/
├── evaluation/
├── configs/
├── utils/
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

## Day 30 --- Component-level code generation

Generate one file/component at a time.

Do not ask the LLM to generate the entire project in one call.

``` text
dataset.py
 ↓
model.py
 ↓
loss.py
 ↓
train.py
 ↓
evaluate.py
```

Each generation receives only relevant paper evidence.

------------------------------------------------------------------------

# Phase 8 --- Code Verification

## Day 31 --- Static checks

Run:

``` text
Python syntax
imports
type checking where practical
dependency validation
```

------------------------------------------------------------------------

## Day 32 --- Automated tests

Generate/run:

``` text
unit tests
shape tests
data pipeline tests
basic model forward-pass tests
```

------------------------------------------------------------------------

## Day 33 --- Paper ↔ Code verification

Compare:

``` text
Paper specification
        vs
Generated implementation
```

Report:

``` text
✓ Architecture matches
✓ Dataset matches
⚠ Optimizer differs
✓ Learning rate matches
⚠ Scheduler unspecified
```

This becomes one of the project's strongest features.

------------------------------------------------------------------------

# Phase 9 --- Persistent Chat + Memory

## Day 34 --- Database foundation

Use PostgreSQL.

Core tables:

``` text
users
papers
projects
conversations
messages
conversation_summaries
user_memory
paper_chunks
```

Use password hashing rather than storing passwords directly.

------------------------------------------------------------------------

## Day 35 --- Conversation persistence

Implement:

``` text
Create conversation
List conversations
Load conversation
Save message
Delete/archive conversation
Rename conversation
```

------------------------------------------------------------------------

## Day 36 --- Context management

Implement:

``` text
recent messages
+
conversation summary
+
relevant memory
+
paper RAG
```

Do not send the entire conversation to the model indefinitely.

------------------------------------------------------------------------

## Day 37 --- Conversation summaries

When conversations become long:

``` text
Old messages
 ↓
Summary
 ↓
Database
```

Then future requests use:

``` text
summary
+
recent messages
```

------------------------------------------------------------------------

## Day 38 --- Long-term memory

Store only useful persistent facts.

Examples:

``` text
User preferences
Project decisions
Important constraints
Chosen architecture
```

Do not store every message as memory.

------------------------------------------------------------------------

# Phase 10 --- Model Router

## Day 39 --- Task classification

Classify requests:

``` text
simple explanation
paper extraction
paper reasoning
code generation
code debugging
summarization
```

------------------------------------------------------------------------

## Day 40 --- Local-first routing

Example:

``` text
Simple task
→ local Ollama

Extraction/structured task
→ local model where possible

Complex reasoning
→ Groq/OpenRouter

Heavy code generation
→ stronger API model

API unavailable
→ local fallback
```

------------------------------------------------------------------------

## Day 41 --- Model fallback

Implement:

``` text
Primary model
 ↓
failure?
 ↓
secondary model
 ↓
failure?
 ↓
local fallback
```

Record model used for every generation.

------------------------------------------------------------------------

# Phase 11 --- FastAPI + SSE

## Day 42 --- API foundation

Create endpoints for:

``` text
/auth
/papers
/extraction
/projects
/conversations
/messages
```

------------------------------------------------------------------------

## Day 43 --- Paper upload API

Flow:

``` text
Upload
 ↓
Create paper_id
 ↓
Store PDF
 ↓
Create extraction job
 ↓
Return job_id
```

------------------------------------------------------------------------

## Day 44 --- Streaming pipeline

Use SSE for:

``` text
extraction progress
agent progress
LLM tokens
tool events
verification events
errors
```

Example:

``` text
EXTRACTION_STARTED
SECTION_DETECTED
RAG_READY
ANALYSIS_STARTED
CODE_GENERATION_STARTED
VERIFICATION_STARTED
COMPLETED
```

------------------------------------------------------------------------

# Phase 12 --- Evaluation + Production

## Day 45 --- End-to-end benchmark

Test:

``` text
PDF
 ↓
Extraction
 ↓
Representation
 ↓
RAG
 ↓
Understanding
 ↓
Feasibility
 ↓
Code
 ↓
Verification
```

------------------------------------------------------------------------

## Day 46 --- Failure testing

Test:

``` text
corrupted PDF
scanned PDF
huge PDF
no abstract
missing methodology
many equations
many tables
unusual headings
unsupported paper
API failure
local model failure
database failure
```

------------------------------------------------------------------------

## Day 47 --- Security

Implement:

``` text
password hashing
authentication
authorization
file validation
file size limits
path traversal protection
safe temporary files
rate limiting where appropriate
secret management
```

------------------------------------------------------------------------

## Day 48 --- Observability

Log:

``` text
paper_id
job_id
conversation_id
model
latency
tokens where available
retrieval results
errors
pipeline state
```

Do not log sensitive user content unnecessarily.

------------------------------------------------------------------------

## Day 49 --- Packaging

Test:

``` text
Python backend
local models
GROBID
Docling
database
Electron
```

on a clean machine/environment.

Document installation and system requirements.

------------------------------------------------------------------------

## Day 50 --- Final architecture review

Verify that:

``` text
Extraction
    ↓
Representation
    ↓
Validation
    ↓
RAG
    ↓
Understanding
    ↓
Feasibility
    ↓
Code
    ↓
Verification
    ↓
Memory
    ↓
Routing
    ↓
API
```

is modular and replaceable.

The backend should not depend on one LLM provider.

------------------------------------------------------------------------

# Final Backend Architecture

``` text
                         ELECTRON
                            │
                            ▼
                         FastAPI
                            │
                 ┌──────────┴──────────┐
                 │                     │
              Chat API             Paper API
                 │                     │
                 ▼                     ▼
          Context Manager       Extraction Manager
                 │                     │
       ┌─────────┼─────────┐     ┌─────┼──────┐
       │         │         │     │     │      │
    History    Memory     RAG  PyMuPDF GROBID Docling
       │         │         │     │     │      │
       └─────────┼─────────┘     └─────┼──────┘
                 │                     │
                 └──────────┬──────────┘
                            ▼
                   Canonical Paper
                       Schema
                            │
                            ▼
                     LangGraph Core
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
     Decomposition      Gap Finding       Feasibility
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                       Refinement
                            │
                            ▼
                       Sequencing
                            │
                            ▼
                   Project Specification
                            │
                            ▼
                    Code Generation
                            │
                            ▼
                    Code Verification
                            │
                            ▼
                     Final Project
```

------------------------------------------------------------------------

# Priority Order

If time becomes limited, do **not** try to complete all 50 days equally.

Priority should be:

``` text
⭐⭐⭐⭐⭐  Phase 1  Extraction
⭐⭐⭐⭐⭐  Phase 2  Canonical Representation
⭐⭐⭐⭐⭐  Phase 3  Extraction Validation
⭐⭐⭐⭐⭐  Phase 5  Paper Understanding
⭐⭐⭐⭐⭐  Phase 7  Code Generation
⭐⭐⭐⭐⭐  Phase 8  Code Verification

⭐⭐⭐⭐   Phase 4  RAG
⭐⭐⭐⭐   Phase 6  Feasibility
⭐⭐⭐⭐   Phase 9  Chat + Memory
⭐⭐⭐⭐   Phase 10 Model Router

⭐⭐⭐    Phase 11 FastAPI/SSE
⭐⭐⭐    Phase 12 Production
```

The reason RAG is not above extraction is simple:

> **Bad extraction → bad chunks → bad retrieval → bad context → bad
> reasoning → bad code.**

Therefore, the first milestone is not "make the LLM smarter."

It is:

> **Given an arbitrary research paper, produce a reliable, structured,
> traceable representation of what the paper actually contains.**

Once that works, the rest of Paper-to-Project has a solid foundation.
