import os
import json
from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.pipeline import FeasibilityReport, BuildSequence, ExtractedParameters, ComponentGraph
from app.core.model_router import ModelRouter


def run_report_agent(
    paper_title: str = "Research Paper",
    component_graph: Any = None,
    feasibility_report: Optional[FeasibilityReport] = None,
    build_sequence: Optional[BuildSequence] = None,
    parameters: Optional[ExtractedParameters] = None,
    model_name: str = settings.DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Compiles a comprehensive Executive Markdown & JSON Adaptation Proposal Report,
    combining component graphs, feasibility metrics, DAG build steps, and LLM narrative summaries.
    """
    feasibility_status = getattr(feasibility_report, "overall_status", "FEASIBLE") if feasibility_report else "FEASIBLE"
    est_vram = getattr(feasibility_report, "estimated_vram_gb", 4.2) if feasibility_report else 4.2
    avail_vram = getattr(feasibility_report, "available_vram_gb", 6.0) if feasibility_report else 6.0

    comp_rows = []
    if isinstance(component_graph, ComponentGraph) and component_graph.components:
        for c in component_graph.components:
            comp_rows.append(f"| **{c.name}** | `{c.type}` | {', '.join(c.inputs)} | {', '.join(c.outputs)} | {c.description} |")
    elif isinstance(component_graph, dict):
        for c in component_graph.get("components", []):
            comp_rows.append(f"| **{c.get('name', 'Module')}** | `{c.get('type', 'encoder')}` | Inputs | Outputs | {c.get('description', '')} |")

    comp_table = "\n".join(comp_rows) if comp_rows else "| **ModelBackbone** | `encoder` | Inputs | Outputs | Visual backbone feature extractor |"

    build_rows = []
    if build_sequence and build_sequence.steps:
        for s in build_sequence.steps:
            build_rows.append(f"| {s.step_num} | **{s.component_name}** | `{s.file_path}` | {s.description} |")

    build_table = "\n".join(build_rows) if build_rows else "| 1 | **config** | `config.py` | Environment setup |"

    prompt = f"""You are a Lead AI Systems Optimization Engineer. Write an executive summary (3-4 sentences) and an educational cloud migration guide (2 paragraphs) for adapting this research paper's deep learning architecture.

PAPER TITLE: {paper_title}
FEASIBILITY STATUS: {feasibility_status} (Estimated VRAM: {est_vram} GB / Available GPU RAM: {avail_vram} GB)

INSTRUCTION:
Return ONLY a valid JSON object matching the following structure:
{{
  "executive_summary": "Executive summary paragraph explaining paper adaptation goals and hardware compatibility.",
  "cloud_migration_guide": "Educational cloud migration guide for training on Google Colab T4 or Kaggle Kernels."
}}
"""

    exec_summary = f"Executive adaptation proposal for '{paper_title}'. Feasibility evaluated at {feasibility_status} with peak estimated VRAM of {est_vram} GB against host available VRAM of {avail_vram} GB."
    cloud_guide = "To scale training beyond local GPU limits, deploy PyTorch training scripts to Google Colab (free T4 GPU with ~15GB VRAM) or Kaggle Kernels (30 free GPU hours/week)."

    try:
        router = ModelRouter()
        raw_res, _ = router.generate(prompt, model_id=model_name)

        json_str = raw_res
        if "```json" in raw_res:
            json_str = raw_res.split("```json")[-1].split("```")[0]
        elif "```" in raw_res:
            json_str = raw_res.split("```")[1]

        narrative = json.loads(json_str.strip())
        exec_summary = narrative.get("executive_summary", exec_summary)
        cloud_guide = narrative.get("cloud_migration_guide", cloud_guide)
    except Exception as e:
        print(f"[Report Agent WARN] Narrative LLM generation fallback ({e}).")

    markdown_content = f"""# 🏆 Project Adaptation Proposal: {paper_title}

## 📊 Executive Summary
{exec_summary}

---

## 1. Extracted Architectural Component Registry

| Component Name | Type | Inputs | Outputs | Description |
|---|---|---|---|---|
{comp_table}

---

## 2. Hardware Feasibility & Compute Profile
- **Overall System Feasibility:** `{feasibility_status}`
- **Estimated Peak VRAM:** `{est_vram} GB`
- **Available System GPU Memory:** `{avail_vram} GB`

---

## 3. Cloud Scaling & Hardware Adaptation Guide
{cloud_guide}

---

## 4. Engineering Build Sequence & File Roadmap

| Step # | Module / Component | Target File Path | Description |
|---|---|---|---|
{build_table}
"""

    return {
        "paper_title": paper_title,
        "executive_summary": exec_summary,
        "cloud_migration_guide": cloud_guide,
        "feasibility_status": feasibility_status,
        "markdown_report": markdown_content,
        "total_build_steps": len(build_rows)
    }

