# Extraction Pipeline — RUEXIS AI

> Covers all files under `backend/app/extraction/` plus the retrieval layer that consumes its output.

---

## 1. High-Level Flow

```mermaid
flowchart TD
    A([PDF / DOCX Upload]) --> B[pdf_parser.py\nparse_pdf_document]
    B --> C[router.py\nroute_and_extract]
    C --> D[merger.py\nmerge_extractions]
    D --> E([Canonical PaperDocument])
    E --> F[chunker.py\nchunk_paper_document]
    E --> G[knowledge_graph.py\nbuild_from_canonical]
    F --> H[vector_db.py\nindex_paper_chunks]
    H --> I([RAG Vector Cache])
    G --> J([KG JSON on disk])
```

---

## 2. Inside `router.py` — Phase-by-Phase

```mermaid
flowchart TD
    Start([PDF Path]) --> P1

    P1["Phase 1 · pdf_inspector.py
    • Validate PDF integrity
    • Detect scanned pages ratio
    • Generate paper_id slug"]

    P1 -->|Invalid| ERR([Return error result])
    P1 -->|Scanned PDF| P2A

    P2A["Phase 2A · docling_parser.py
    OCR route — Docling extracts
    text from image-only pages"]
    P2A --> DONE([Return early with Docling output])

    P1 -->|Native text PDF| P3

    P3["Phase 3 · block_extractor.py + section_detector.py
    Deterministic PyMuPDF extraction
    — 0 API tokens consumed
    Produces: blocks, sections, raw_full_text"]

    P3 --> P4

    P4["Phase 4 · element_cropper.py
    Detect & crop visual elements
    → Figures needing VLM
    → Tables needing VLM
    → Equations needing VLM"]

    P4 --> VLMGate{daily_quota_manager
    .can_use_vlm ?}

    VLMGate -->|Yes + elements exist| P5A
    VLMGate -->|No / quota exhausted| P5B

    P5A["Phase 5A · vlm_processor.py
    Gemini VLM targeted calls
    Figures  → up to 6
    Tables   → up to 6
    Equations → up to 8"]

    P5A --> SH{Self-healing
    needed?}
    SH -->|Table: no pipes / Eq: unbalanced LaTeX| Retry["Re-crop at 250 DPI
    Retry VLM once"]
    Retry --> P6
    SH -->|OK| P6

    P5B["Phase 5B · Local Fallback
    100% deterministic output only
    reason: daily_quota_exhausted
    or pure_deterministic_document"]

    P5B --> P6

    P6["Phase 6 · grobid_client + grobid_parser
    Optional — if GROBID reachable
    References + header metadata enrichment"]

    P6 --> Result([Raw router result dict])
```

---

## 3. Inside `merger.py` — Consensus Assembly

```mermaid
flowchart LR
    subgraph Inputs
        A1[PyMuPDF output\nsections · raw text]
        A2[VLM output\nfigures · tables · equations]
        A3[GROBID output\nreferences · metadata]
        A4[Docling output\nOCR text · tables]
    end

    subgraph Merger["merger.py — merge_extractions()"]
        direction TB
        M1["extract_consensus_tables()
        Priority: VLM > Docling > PyMuPDF
        ⚠ isinstance(data, dict) guard"]
        M2["extract figures
        Priority: VLM > PyMuPDF caption"]
        M3["extract equations
        Priority: VLM LaTeX > PyMuPDF text"]
        M4["extract sections
        Always: PyMuPDF (deterministic)"]
        M5["extract abstract
        Priority: GROBID > Docling
        ⚠ isinstance guard"]
        M6["extract references
        Priority: GROBID > Docling
        ⚠ isinstance guard per item"]
        M7["extract metadata
        Priority: GROBID > Docling > PyMuPDF"]
    end

    Inputs --> Merger
    Merger --> Out([PaperDocument])
```

> **Why the `isinstance` guards?**  
> Parsers like Grobid/Docling return a raw `str` when they partially fail (e.g., no XML response).  
> Calling `.get()` on a `str` raises `AttributeError`. Every parser output is now guarded:
> ```python
> if isinstance(data, dict) and data.get("tables"):
>     ...
> ```

---

## 4. VLM Quota System

```mermaid
flowchart TD
    DQM["daily_quota_manager
    daily_extraction_quota.json"]

    DQM --> L1["max_papers_per_day: 50"]
    DQM --> L2["max_vlm_requests_per_day: 200"]
    DQM --> L3["Resets at midnight UTC"]

    Check{can_use_vlm?} -->|Quota OK| VLM[Dispatch Gemini VLM]
    Check -->|Exhausted| Local[100% Local Fallback]

    VLM --> Record["record_vlm_request(paper_id, type, in_tok, out_tok)"]
    VLM --> Complete["record_paper_completion(paper_id, used_vlm=True)"]

    DQM --> Check
```

---

## 5. Benchmark Modes — `benchmark.py`

```mermaid
flowchart LR
    subgraph ModeA["Mode A — deterministic_offline"]
        direction TB
        A1[VLM: ❌ Never]
        A2[Measures: local latency only]
        A3[Tokens: zero cloud = reported as 0]
    end

    subgraph ModeB["Mode B — adaptive_vlm"]
        direction TB
        B1[VLM: ✅ Surgical]
        B2[Measures: actual latency per phase]
        B3[Tokens: only if actually returned by API]
    end

    subgraph ModeC["Mode C — whole_doc_baseline"]
        direction TB
        C1[VLM: ✅ All pages]
        C2[Measures: worst-case comparison]
        C3[Tokens: full document cost]
    end

    ModeA --> Stats
    ModeB --> Stats
    ModeC --> Stats

    Stats["Statistical Rollup
    Mean · Median · P95 · Min · Max
    Per metric: latency, tokens, reductions"]
```

---

## 6. Canonical Schema — What Extraction Produces

```mermaid
classDiagram
    class PaperDocument {
        paper_id: str
        raw_text: str
        metadata: PaperMetadata
        sections: List~Section~
        figures: List~Figure~
        tables: List~Table~
        equations: List~Equation~
        references: List~Reference~
        algorithms: List~Algorithm~
    }
    class Section {
        title: str
        content: str
        subsections: dict
        page_start: int
        page_end: int
        confidence: float
    }
    class Figure {
        id: str
        caption: str
        visual_description: str
        vlm_used: bool
        confidence: float
    }
    class Table {
        id: str
        caption: str
        content_markdown: str
        headers: List~str~
        rows: List~List~str~~
        vlm_used: bool
        confidence: float
    }
    class Equation {
        id: str
        latex: str
        variables: List~str~
        vlm_used: bool
        confidence: float
    }
    class Provenance {
        page: int
        section: str
        text_span: str
    }

    PaperDocument *-- Section
    PaperDocument *-- Figure
    PaperDocument *-- Table
    PaperDocument *-- Equation
    Figure *-- Provenance
    Table *-- Provenance
    Equation *-- Provenance
```

---

## 7. Retrieval Consumers

```mermaid
flowchart TD
    PD([PaperDocument])

    PD --> CH["chunker.py
    chunk_paper_document()
    500-word chunks with 50-word overlap
    Attaches fig_refs · table_refs · eq_refs"]

    PD --> KG["knowledge_graph.py
    build_from_canonical()
    7-tier NetworkX DiGraph
    ⚠ isinstance guard on raw_modules"]

    CH --> VDB["vector_db.py
    index_paper_chunks()
    SHA-256 dedup · per-paper JSON
    NumPy cosine similarity retrieval"]

    KG --> KGDISK["reports/knowledge_graphs/
    paper_id_graph.json"]

    VDB --> VDBDISK["storage/rag_embeddings/
    paper_id.json"]
```

---

## 8. File Reference

| File | Role |
|---|---|
| `extraction/pdf_parser.py` | Public entry — calls router then merger |
| `extraction/router.py` | Phase orchestrator — Deterministic-First logic |
| `extraction/merger.py` | Multi-parser consensus assembler |
| `extraction/benchmark.py` | A/B/C mode benchmark suite |
| `extraction/validator.py` | Post-merge quality check |
| `extraction/pdf_inspector.py` | PDF metadata + scanned page detection |
| `extraction/block_extractor.py` | PyMuPDF layout block extraction |
| `extraction/section_detector.py` | Heading hierarchy detection |
| `extraction/element_cropper.py` | Visual element detection & image cropping |
| `extraction/vlm_processor.py` | Gemini VLM transcription (figures/tables/eq) |
| `extraction/pymupdf_parser.py` | PyMuPDF text + structure parsing |
| `extraction/grobid_parser.py` | GROBID XML reference/header parsing |
| `extraction/grobid_client.py` | GROBID REST client |
| `extraction/docling_parser.py` | Docling OCR path for scanned PDFs |
| `extraction/semantic_analyzer.py` | NLP section classification |
| `extraction/constants.py` | DPI settings, detection thresholds |
| `retrieval/chunker.py` | Provenance-aware RAG chunker |
| `retrieval/vector_db.py` | Local flat-file vector store |
| `retrieval/knowledge_graph.py` | 7-level NetworkX KG service |
| `retrieval/embeddings.py` | Embedding model adapter |
| `core/quota_tracker.py` | `daily_quota_manager` — VLM budget enforcement |
