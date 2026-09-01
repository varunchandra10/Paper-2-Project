from app.graph.state import PipelineState
from app.extraction.pdf_parser import parse_pdf_document
from app.retrieval.chunker import chunk_paper_document
from app.retrieval.embeddings import generate_local_embedding
from app.retrieval.vector_db import PaperVectorDB
from app.agents.ingestion_agent import run_ingestion_agent
from app.core.tracer import AgentTracer


def ingestion_node(state: PipelineState) -> dict:
    pdf_path = state.get("pdf_path", "")
    if state.get("paper_doc"):
        return {"paper_doc": state["paper_doc"], "raw_sections": state.get("raw_sections", {})}

    # 1. Parse PDF
    paper_doc = parse_pdf_document(pdf_path)

    # 2. Chunk & Embed vector layout
    chunks = chunk_paper_document(paper_doc)
    embeddings = [generate_local_embedding(c.content) for c in chunks[:5]]

    vdb = PaperVectorDB()
    vdb.initialize_db()
    vdb.insert_paper_document(paper_doc, chunks[:5], embeddings)

    # 3. Parse Sections
    parsed_sections = {sec.title: sec.content for sec in paper_doc.sections}
    parsed_sections["Metadata"] = f"Title: {paper_doc.metadata.title}\nAbstract: {paper_doc.metadata.abstract}"

    model = state.get("model_name", "qwen2.5-coder:1.5b")
    metadata = run_ingestion_agent(parsed_sections, model_name=model)

    tracer = AgentTracer()
    tracer.log_step(paper_doc.paper_id, "PAPER_INGESTION", "success", f"Parsed PDF document with {len(chunks)} layout chunks.", duration_ms=1250, model_used=model)

    return {
        "raw_sections": parsed_sections,
        "metadata": metadata,
        "paper_doc": paper_doc,
        "loop_count": 0
    }
