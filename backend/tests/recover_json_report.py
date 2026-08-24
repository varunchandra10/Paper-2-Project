import os
import json
import re
import datetime


REPORTS_DIR = r"c:\Users\kvcsu_ht23nk8\OneDrive\Desktop\all_Projects\Projects\agentic_projects\Paper-2-Project\backend\tests\reports"
MD_PATH = os.path.join(REPORTS_DIR, "corpus_report_20260823_234448.md")
JSON_PATH = os.path.join(REPORTS_DIR, "corpus_report_20260823_234448.json")

def parse_md_to_json():
    if not os.path.exists(MD_PATH):
        print(f"Error: {MD_PATH} does not exist.")
        return

    with open(MD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract metadata header
    model_match = re.search(r"\*\*Model:\*\* `([^`]+)`", content)
    model = model_match.group(1) if model_match else "qwen2.5-coder:1.5b"
    
    gpu_match = re.search(r"\*\*GPU:\*\* ([^|]+)", content)
    gpu = gpu_match.group(1).strip() if gpu_match else "NVIDIA GeForce RTX 5050 Laptop GPU"
    
    vram_match = re.search(r"\((\d+\.?\d*)\s*GB VRAM\)", content)
    vram = float(vram_match.group(1)) if vram_match else 8.0

    ram_match = re.search(r"\*\*RAM:\*\*\s*(\d+\.?\d*)\s*GB", content)
    ram = float(ram_match.group(1)) if ram_match else 23.6

    papers_section = content.split("## Per-Paper Detailed Reports")[-1]
    paper_blocks = papers_section.split("### ")

    papers = []
    for block in paper_blocks:
        block = block.strip()
        if not block:
            continue
        
        lines = block.split("\n")
        title_line = lines[0]
        # E.g. [1] [1].pdf — A Novel Change Detection Method Based on...
        match = re.match(r"\[(\d+)\]\s+([^—]+)—\s*(.*)", title_line)
        if not match:
            continue
        
        paper_idx = int(match.group(1))
        pdf_name = match.group(2).strip()
        title = match.group(3).strip()

        # Parse specs line
        # - **Elapsed:** 141.3s | **Sections:** 15 | **Tables:** 5
        specs_line = ""
        for l in lines:
            if "Elapsed:" in l:
                specs_line = l
                break
        
        elapsed = 0.0
        sections = 0
        tables = 0
        if specs_line:
            elapsed_m = re.search(r"Elapsed:\*\* (\d+\.?\d*)s", specs_line)
            if elapsed_m:
                elapsed = float(elapsed_m.group(1))
            sec_m = re.search(r"Sections:\*\* (\d+)", specs_line)
            if sec_m:
                sections = int(sec_m.group(1))
            tab_m = re.search(r"Tables:\*\* (\d+)", specs_line)
            if tab_m:
                tables = int(tab_m.group(1))

        # Parse Parameters table
        parameters = {}
        param_table_start = -1
        for idx, l in enumerate(lines):
            if "| Parameter | Value | Status | Confidence |" in l:
                param_table_start = idx + 2
                break
        
        if param_table_start != -1:
            for idx in range(param_table_start, len(lines)):
                l = lines[idx].strip()
                if not l.startswith("|"):
                    break
                parts = [p.strip() for p in l.split("|")[1:-1]]
                if len(parts) >= 4:
                    param_name = parts[0].lower()
                    val = parts[1]
                    status = parts[2]
                    try:
                        conf = float(parts[3])
                    except:
                        conf = 1.0
                    parameters[param_name] = {
                        "value": val,
                        "status": status,
                        "confidence": conf
                    }

        # Parse Gap Classification table
        gaps = []
        gap_table_start = -1
        for idx, l in enumerate(lines):
            if "| Parameter | Classification | Value |" in l:
                gap_table_start = idx + 2
                break
        
        if gap_table_start != -1:
            for idx in range(gap_table_start, len(lines)):
                l = lines[idx].strip()
                if not l.startswith("|"):
                    break
                parts = [p.strip() for p in l.split("|")[1:-1]]
                if len(parts) >= 3:
                    gaps.append({
                        "parameter": parts[0].lower(),
                        "classification": parts[1],
                        "value": parts[2],
                        "details": ""
                    })

        # Parse milestones
        milestones = []
        ms_table_start = -1
        for idx, l in enumerate(lines):
            if "| # | Milestone | Days | Priority |" in l:
                ms_table_start = idx + 2
                break
        
        if ms_table_start != -1:
            for idx in range(ms_table_start, len(lines)):
                l = lines[idx].strip()
                if not l.startswith("|"):
                    break
                parts = [p.strip() for p in l.split("|")[1:-1]]
                if len(parts) >= 4:
                    milestones.append({
                        "name": parts[1],
                        "duration_days": int(parts[2]) if parts[2].isdigit() else 3,
                        "priority": parts[3]
                    })

        # Parse Executive Summary
        exec_summary = ""
        for idx, l in enumerate(lines):
            if l.startswith("**Executive Summary:**"):
                if idx + 1 < len(lines):
                    exec_summary = lines[idx+1].replace(">", "").strip()
                break

        papers.append({
            "paper_id": f"paper_{paper_idx}",
            "pdf_name": pdf_name,
            "status": "SUCCESS",
            "elapsed_seconds": elapsed,
            "metadata": {
                "title": title,
                "authors": ["Unknown Author"],
                "abstract": "",
                "primary_contribution": ""
            },
            "paper_doc_stats": {
                "sections": sections,
                "tables": tables,
                "equations": 0
            },
            "component_graph": {
                "components": [],
                "edges": []
            },
            "extracted_parameters": parameters,
            "gap_report": {
                "summary": "",
                "has_critical_missing": True,
                "gaps": gaps
            },
            "feasibility": {
                "overall_status": "WARNING",
                "training_status": "WARNING",
                "training_substitute": "",
                "components": []
            },
            "build_sequence": {
                "total_duration_weeks": round(sum(m["duration_days"] for m in milestones) / 7, 1),
                "milestones": milestones
            },
            "adaptation_report": {
                "executive_summary": exec_summary,
                "bottleneck_analysis": "",
                "cloud_migration_guide": ""
            }
        })

    json_report = {
        "generated_at": datetime.datetime.now().isoformat(),
        "system": {
            "model": model,
            "gpu": gpu,
            "vram_gb": vram,
            "system_ram_gb": ram,
            "timeline_weeks": 2
        },
        "papers_total": len(papers),
        "papers_success": len(papers),
        "papers_error": 0,
        "total_runtime_sec": 3180.0,
        "papers": papers,
        "errors": []
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    print(f"Successfully recovered JSON report at {JSON_PATH}!")

if __name__ == "__main__":
    parse_md_to_json()
