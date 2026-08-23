import os
import sys
import json
import time

# Ensure backend path is configured
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from core import settings
from extraction import route_and_extract, merge_extractions, validate_paper_document
from retrieval import chunk_paper_document, generate_local_embedding, batch_embed_chunks, PaperVectorDB, generate_grounded_evidence


def run_complete_backend_test(run_from_scratch: bool = False):
    """
    Executes a complete end-to-end integration test across Phase 1, 2, 3, and 4.
    Processes the corpus, merges schemas, validates structure, slices chunks,
    generates embeddings, inserts into pgvector, and runs query reranking.
    """
    papers_dir = os.path.join(backend_path, "papers", "research_papers")
    routed_cache_dir = os.path.join(settings.storage_dir, "complete_phase_2_test")
    output_dir = os.path.join(settings.storage_dir, "complete_backend_test")
    report_path = os.path.join(
        os.path.dirname(settings.backend_dir), 
        "docs", "backend_docs", "Tests_docs", "Phase_4_test.md"
    )

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    # 1. Initialize local pgvector database schemas
    db = PaperVectorDB()
    db.initialize_db()

    if not os.path.exists(papers_dir):
        print(f"Error: Papers directory not found: {papers_dir}")
        return

    pdf_files = [f for f in os.listdir(papers_dir) if f.lower().endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDF papers in corpus.")
    print("Starting Complete Phase 1-4 End-to-End Ingestion & RAG Audit...\n")

    start_time = time.time()
    records = []
    success_count = 0
    fail_count = 0
    total_chunks = 0

    for idx, filename in enumerate(sorted(pdf_files)):
        pdf_path = os.path.join(papers_dir, filename)
        base_name = os.path.splitext(filename)[0]
        
        # Dedicated subfolder for each paper
        paper_folder = os.path.join(output_dir, base_name)
        os.makedirs(paper_folder, exist_ok=True)

        print(f"[{idx+1}/{len(pdf_files)}] Processing {filename}...")
        try:
            # --- PHASE 1: Route & Parse ---
            cached_routed_path = os.path.join(routed_cache_dir, base_name, f"{base_name}_routed.json")
            if not run_from_scratch and os.path.exists(cached_routed_path):
                # Load from cache
                with open(cached_routed_path, "r", encoding="utf-8") as f:
                    routed_result = json.load(f)
            else:
                routed_result = route_and_extract(pdf_path)
                
            routed_path = os.path.join(paper_folder, f"{base_name}_routed.json")
            with open(routed_path, "w", encoding="utf-8") as f:
                json.dump(routed_result, f, indent=4)

            # --- PHASE 2: Merge into Canonical Pydantic Schema ---
            paper_doc = merge_extractions(routed_result)
            canonical_path = os.path.join(paper_folder, f"{base_name}_canonical.json")
            with open(canonical_path, "w", encoding="utf-8") as f:
                f.write(paper_doc.model_dump_json(indent=4))

            # --- PHASE 3: Deterministic Quality Validation ---
            quality_report = validate_paper_document(paper_doc)
            quality_path = os.path.join(paper_folder, f"{base_name}_quality.json")
            with open(quality_path, "w", encoding="utf-8") as f:
                f.write(quality_report.model_dump_json(indent=4))

            # --- PHASE 4: Semantic Chunking & Local Vector Insertion ---
            chunks = chunk_paper_document(paper_doc)
            embeddings = [generate_local_embedding(c.content) for c in chunks]
            db.insert_paper_document(paper_doc, chunks, embeddings)

            if quality_report.valid:
                success_count += 1
            else:
                fail_count += 1

            total_chunks += len(chunks)
            records.append({
                "Paper ID": f"`{paper_doc.paper_id}`",
                "Filename": filename,
                "Status": "Valid" if quality_report.valid else "Blocked",
                "Chunks": len(chunks),
                "Tables": len(paper_doc.tables),
                "Equations": len(paper_doc.equations),
                "Algorithms": len(paper_doc.algorithms)
            })
            print(f"   Chunks: {len(chunks)} | Tables: {len(paper_doc.tables)} | Equations: {len(paper_doc.equations)} | Algs: {len(paper_doc.algorithms)}")

        except Exception as e:
            fail_count += 1
            print(f"   [CRASH] Ingestion Pipeline Crash on {filename} | Error: {e}")

    duration = time.time() - start_time
    success_rate = (success_count / len(pdf_files)) * 100 if pdf_files else 0.0

    # Run a test query against the complete database
    test_query = "What optimizer and learning rate were used?"
    print(f"\n[QUERY] Running Test Reranked Retrieval: '{test_query}'...")
    query_vector = generate_local_embedding(test_query)
    
    # Retrieve and rerank top 3 chunks
    test_results = generate_grounded_evidence(test_query, query_vector, top_k=3)
    
    # Compile markdown scorecard report
    md = [
        "# Phase 4 Complete End-to-End Ingestion & RAG Scorecard Report\n",
        "This report summarizes the end-to-end integration checks across Routing, Merging, Validation, "
        "and pgvector local database storage for all 29 papers.\n",
        "## 📊 Aggregate Pipeline Statistics",
        f"- **Total Papers Processed**: {len(pdf_files)}",
        f"- **Valid Ingestions**: {success_count} ({success_rate:.1f}%)",
        f"- **Validation Blocked Ingestions**: {fail_count}",
        f"- **Total Semantic Chunks Stored**: {total_chunks}",
        f"- **Total Pipeline Duration**: {duration:.2f} seconds\n",
        "## 🔍 Grounded Evidence Reranker Verification",
        f"**Test Query**: `{test_query}`\n",
        "| Rank | Score | Chunk ID | Page | Section | Content Snippet |",
        "| :---: | :---: | :--- | :---: | :--- | :--- |"
    ]

    for idx, res in enumerate(test_results):
        snippet = res['content'][:150].replace('\n', ' ') + "..."
        md.append(
            f"| {idx+1} | {res.get('rerank_score', 0)}/5 | `{res['chunk_id']}` | {res['page']} | "
            f"'{res['section']}' | {snippet} |"
        )

    md.append("\n## 📋 Combined Ingestion Ledger")
    md.append("| Paper ID | Filename | Status | Chunks | Tables | Equations | Algorithms |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |")

    for r in records:
        md.append(
            f"| {r['Paper ID']} | {r['Filename']} | {r['Status']} | {r['Chunks']} | {r['Tables']} | "
            f"{r['Equations']} | {r['Algorithms']} |"
        )

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"\n[DONE] Complete Ingestion & RAG Pipeline Audit Complete!")
    print(f"[SAVE] Report saved to: {report_path}")


if __name__ == "__main__":
    run_complete_backend_test()
