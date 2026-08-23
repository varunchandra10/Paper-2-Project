import os
import json
from typing import Dict, Any, List
from schemas.canonical_paper import PaperDocument


# Defined expectations (ground truth thresholds) for the golden test subset
BENCHMARK_EXPECTATIONS = {
    "[1]": {
        "title_keyword": "change detection",
        "min_pages": 10,
        "min_sections": 10,
        "min_tables": 4,
        "min_equations": 15,
        "min_algorithms": 1,
        "min_references": 50
    },
    "[2]": {
        "title_keyword": "learning paradigm",
        "min_pages": 10,
        "min_sections": 10,
        "min_tables": 0,
        "min_equations": 10,
        "min_algorithms": 1,
        "min_references": 50
    },
    "[11]": {
        "title_keyword": "survey",
        "min_pages": 20,
        "min_sections": 15,
        "min_tables": 2,
        "min_equations": 5,
        "min_algorithms": 0,
        "min_references": 50
    },
    "[17]": {
        "title_keyword": "copula",
        "min_pages": 15,
        "min_sections": 15,
        "min_tables": 5,
        "min_equations": 15,
        "min_algorithms": 0,
        "min_references": 50
    },
    "[18]": {
        "title_keyword": "change detection",
        "min_pages": 30,
        "min_sections": 30,
        "min_tables": 40,  # outlier paper with 43 tables
        "min_equations": 15,
        "min_algorithms": 0,
        "min_references": 50
    },
    "[24]": {
        "title_keyword": "manifold",
        "min_pages": 5,
        "min_sections": 5,
        "min_tables": 0,
        "min_equations": 10,
        "min_algorithms": 0,
        "min_references": 20
    }
}


def run_extraction_benchmark(storage_dir: str) -> Dict[str, Any]:
    """
    Executes the Phase 3 Day 13 extraction accuracy benchmark over the golden test subset.
    Calculates accuracy metrics and compiles the baseline extraction audit report.
    """
    audit_results = {}
    
    # Track segment performance counts: (passed_checks, total_checks)
    metrics = {
        "metadata_accuracy": [0, 0],
        "section_accuracy": [0, 0],
        "text_coverage": [0, 0],
        "figure_detection": [0, 0],
        "table_detection": [0, 0],
        "equation_detection": [0, 0],
        "reference_extraction": [0, 0],
        "provenance_correctness": [0, 0]
    }
    
    for base_name, expected in BENCHMARK_EXPECTATIONS.items():
        paper_folder = os.path.join(storage_dir, base_name)
        canonical_path = os.path.join(paper_folder, f"{base_name}_canonical.json")
        
        if not os.path.exists(canonical_path):
            continue
            
        try:
            with open(canonical_path, "r", encoding="utf-8") as f:
                doc = PaperDocument.model_validate_json(f.read())
                
            # --- 1. Metadata Check ---
            title_ok = expected["title_keyword"].lower() in doc.metadata.title.lower()
            authors_ok = len(doc.metadata.authors) > 0 and doc.metadata.authors != ["Unknown Author"]
            abstract_ok = len(doc.metadata.abstract) > 100
            
            metrics["metadata_accuracy"][1] += 3
            if title_ok: metrics["metadata_accuracy"][0] += 1
            if authors_ok: metrics["metadata_accuracy"][0] += 1
            if abstract_ok: metrics["metadata_accuracy"][0] += 1
            
            # --- 2. Section Check ---
            sections_ok = len(doc.sections) >= expected["min_sections"]
            metrics["section_accuracy"][1] += 1
            if sections_ok: metrics["section_accuracy"][0] += 1
            
            # --- 3. Text Coverage Check ---
            total_chars = sum(p.character_count for p in doc.pages)
            avg_coverage = total_chars / len(doc.pages) if doc.pages else 0
            coverage_ok = avg_coverage > 1000  # High-quality text coverage density
            
            metrics["text_coverage"][1] += 1
            if coverage_ok: metrics["text_coverage"][0] += 1
            
            # --- 4. Table Check ---
            tables_ok = len(doc.tables) >= expected["min_tables"]
            metrics["table_detection"][1] += 1
            if tables_ok: metrics["table_detection"][0] += 1
            
            # --- 5. Equation Check ---
            eqs_ok = len(doc.equations) >= expected["min_equations"]
            metrics["equation_detection"][1] += 1
            if eqs_ok: metrics["equation_detection"][0] += 1
            
            # --- 6. Reference Check ---
            refs_ok = len(doc.references) >= expected["min_references"]
            metrics["reference_extraction"][1] += 1
            if refs_ok: metrics["reference_extraction"][0] += 1
            
            # --- 7. Figure Check ---
            figs_ok = len(doc.figures) > 0
            metrics["figure_detection"][1] += 1
            if figs_ok: metrics["figure_detection"][0] += 1
            
            # --- 8. Provenance Check (Visual objects have correct page ranges)
            prov_ok = True
            for tbl in doc.tables:
                if tbl.page < 1 or tbl.page > len(doc.pages):
                    prov_ok = False
            for fig in doc.figures:
                if fig.page < 1 or fig.page > len(doc.pages):
                    prov_ok = False
                    
            metrics["provenance_correctness"][1] += 1
            if prov_ok: metrics["provenance_correctness"][0] += 1

            audit_results[base_name] = {
                "Title Verified": "✓" if title_ok else "✗",
                "Pages": len(doc.pages),
                "Sections": len(doc.sections),
                "Tables (Extracted/Expected)": f"{len(doc.tables)}/{expected['min_tables']}",
                "Equations (Extracted/Expected)": f"{len(doc.equations)}/{expected['min_equations']}",
                "Algorithms (Extracted/Expected)": f"{len(doc.algorithms)}/{expected['min_algorithms']}",
                "References (Extracted/Expected)": f"{len(doc.references)}/{expected['min_references']}",
                "Passed": all((title_ok, authors_ok, abstract_ok, sections_ok, coverage_ok, tables_ok, eqs_ok, refs_ok, prov_ok))
            }
            
        except Exception as e:
            audit_results[base_name] = {"Error": str(e), "Passed": False}

    # Calculate percentages
    summary = {}
    for key, val in metrics.items():
        passed, total = val
        pct = (passed / total) * 100 if total > 0 else 0.0
        summary[key] = f"{passed}/{total} ({pct:.1f}%)"

    return {
        "summary": summary,
        "details": audit_results
    }
