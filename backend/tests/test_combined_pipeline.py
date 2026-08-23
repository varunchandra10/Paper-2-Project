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


def run_combined_test():
    """
    Executes a combined validation run over the entire 29-paper corpus.
    Runs Phase 1 (Routing & Parsing), Phase 2 (Canonical Merging), and Phase 3 (Quality Gating)
    end-to-end for every document.
    """
    papers_dir = os.path.join(backend_path, "papers", "research_papers")
    output_dir = os.path.join(settings.storage_dir, "combined_pipeline_test")
    report_path = os.path.join(
        os.path.dirname(settings.backend_dir), 
        "docs", "backend_docs", "Tests_docs", "phase_2_test.md"
    )

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    if not os.path.exists(papers_dir):
        print(f"Error: Papers directory not found: {papers_dir}")
        return

    pdf_files = [f for f in os.listdir(papers_dir) if f.lower().endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDF papers in corpus.")
    print("🚀 Starting Combined End-to-End Ingestion Pipeline Audit (Phases 1-3)...\n")

    start_time = time.time()
    records = []
    success_count = 0
    fail_count = 0
    
    total_pages = 0
    total_tables = 0
    total_equations = 0
    total_algorithms = 0

    for idx, filename in enumerate(sorted(pdf_files)):
        pdf_path = os.path.join(papers_dir, filename)
        base_name = os.path.splitext(filename)[0]
        
        # Dedicated subfolder for each paper
        paper_folder = os.path.join(output_dir, base_name)
        os.makedirs(paper_folder, exist_ok=True)

        print(f"[{idx+1}/{len(pdf_files)}] Processing {filename}...")
        try:
            # --- PHASE 1: Route & Parse ---
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

            errors = sum(1 for m in quality_report.scorecard.values() if m.status == "ERROR")
            warnings = sum(1 for m in quality_report.scorecard.values() if m.status == "WARNING")

            if quality_report.valid:
                success_count += 1
            else:
                fail_count += 1

            p_count = len(paper_doc.pages)
            t_count = len(paper_doc.tables)
            eq_count = len(paper_doc.equations)
            alg_count = len(paper_doc.algorithms)

            total_pages += p_count
            total_tables += t_count
            total_equations += eq_count
            total_algorithms += alg_count

            records.append({
                "Paper ID": f"`{paper_doc.paper_id}`",
                "Filename": filename,
                "Status": "✓ Valid" if quality_report.valid else "✗ Blocked",
                "Errors": errors,
                "Warnings": warnings,
                "Tables": t_count,
                "Equations": eq_count,
                "Algorithms": alg_count,
                "References": len(paper_doc.references)
            })
            print(f"   ✓ Success | Extracted {t_count} Tables, {eq_count} Equations, {alg_count} Algorithms | Errors: {errors}")

        except Exception as e:
            fail_count += 1
            print(f"   💥 Ingestion Pipeline Crash on {filename} | Error: {e}")

    duration = time.time() - start_time
    success_rate = (success_count / len(pdf_files)) * 100 if pdf_files else 0.0

    # Build md scorecard report
    md = [
        "# Combined End-to-End Ingestion Pipeline Scorecard Report\n",
        "This report summarizes the combined parsing, merging, and validation scorecard across the entire 29-paper corpus.\n",
        "## 📊 Combined Statistics",
        f"- **Total Papers Processed**: {len(pdf_files)}",
        f"- **Valid Canonical Outputs**: {success_count} ({success_rate:.1f}%)",
        f"- **Validation Blocked Ingestions**: {fail_count}",
        f"- **Total Pages Compiled**: {total_pages}",
        f"- **Total Tables Extracted**: {total_tables}",
        f"- **Total Equations Extracted**: {total_equations}",
        f"- **Total Algorithms Extracted**: {total_algorithms}",
        f"- **Total Pipeline Duration**: {duration:.2f} seconds\n",
        "## 📋 Combined Ingestion Ledger",
        "| Paper ID | Filename | Status | Errors | Warnings | Tables | Equations | Algorithms | References |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]

    for r in records:
        md.append(
            f"| {r['Paper ID']} | {r['Filename']} | {r['Status']} | {r['Errors']} | {r['Warnings']} | "
            f"{r['Tables']} | {r['Equations']} | {r['Algorithms']} | {r['References']} |"
        )

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"\n🎉 Combined Ingestion Pipeline Audit Complete!")
    print(f"💾 Report saved to: {report_path}")


if __name__ == "__main__":
    run_test = True
    # Can run standalone if desired
    run_combined_test()
