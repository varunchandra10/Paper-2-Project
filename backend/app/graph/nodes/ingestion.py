import os
from app.graph.state import PipelineState
from app.extraction.pdf_parser import parse_pdf_document
from app.retrieval.chunker import chunk_paper_document
from app.retrieval.embeddings import generate_local_embedding, generate_local_embeddings_batch
from app.retrieval.vector_db import PaperVectorDB
from app.agents.ingestion_agent import run_ingestion_agent
from app.core.tracer import AgentTracer
from app.core.manifest import compute_file_sha256
from app.core.cost_optimizer import cost_optimizer

MAX_ALLOWED_PDF_BYTES = 50 * 1024 * 1024  # 50 MB safety limit


def ingestion_node(state: PipelineState) -> dict:
    pdf_path = state.get("pdf_path", "")
    if state.get("paper_doc"):
        return {"paper_doc": state["paper_doc"], "raw_sections": state.get("raw_sections", {})}

    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")

    # Validate file size (empty / huge PDF detection)
    file_size = os.path.getsize(pdf_path)
    if file_size == 0:
        raise ValueError(f"PDF document is completely empty (0 bytes): {os.path.basename(pdf_path)}")
    if file_size > MAX_ALLOWED_PDF_BYTES:
        raise ValueError(f"PDF document exceeds 50MB safety limit ({round(file_size / (1024*1024), 2)}MB): {os.path.basename(pdf_path)}")

    # Phase 14 Optimization: Check if paper hash was already ingested
    pdf_hash = compute_file_sha256(pdf_path)
    cached = cost_optimizer.get_cached_paper_ingestion(pdf_hash)
    if cached:
        tracer = AgentTracer()
        tracer.log_step(
            cached["paper_doc"].paper_id,
            "PAPER_INGESTION_CACHE_HIT",
            "success",
            f"Paper hash {pdf_hash[:10]} matched existing cache. Skipped parsing and embedding.",
            duration_ms=2,
            model_used="cache"
        )
        return {
            "raw_sections": cached["raw_sections"],
            "metadata": cached["metadata"],
            "paper_doc": cached["paper_doc"],
            "loop_count": 0,
            "cache_hit": True
        }

    # 1. Parse PDF
    paper_doc = parse_pdf_document(pdf_path)
    if not paper_doc.sections and not paper_doc.metadata.abstract:
        err = paper_doc.extraction_metadata.get("error_message") or "Corrupted or non-extractable PDF content"
        raise ValueError(f"Failed to ingest PDF: {err}")

    # 2. Chunk & Embed vector layout (ALL chunks, complete paper indexing)
    chunks = chunk_paper_document(paper_doc)
    texts = [c.content for c in chunks]
    embeddings = generate_local_embeddings_batch(texts)

    vdb = PaperVectorDB()
    vdb.initialize_db()
    vdb.insert_paper_document(paper_doc, chunks, embeddings)

    # 3. Parse Sections
    parsed_sections = {sec.title: sec.content for sec in paper_doc.sections}
    parsed_sections["Metadata"] = f"Title: {paper_doc.metadata.title}\nAbstract: {paper_doc.metadata.abstract}"

    model = state.get("model_name", "qwen2.5-coder:1.5b")
    metadata = run_ingestion_agent(parsed_sections, model_name=model)

    tracer = AgentTracer()
    tracer.log_step(paper_doc.paper_id, "PAPER_INGESTION", "success", f"Parsed PDF document with {len(chunks)} layout chunks.", duration_ms=1250, model_used=model)

    # Phase 14 Optimization: Cache ingested paper state for unchanged paper reuse
    cost_optimizer.cache_paper_ingestion(
        pdf_hash=pdf_hash,
        paper_doc=paper_doc,
        raw_sections=parsed_sections,
        metadata=metadata,
        estimated_tokens_saved=max(1000, sum(len(c.content)//4 for c in chunks)),
        estimated_latency_ms=1250.0
    )

    return {
        "raw_sections": parsed_sections,
        "metadata": metadata,
        "paper_doc": paper_doc,
        "loop_count": 0
    }
