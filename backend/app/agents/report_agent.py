import json
from app.core.config import settings
from app.schemas.pipeline import FeasibilityReport, BuildSequence


def run_report_agent(pipeline_output: dict, feasibility_report: FeasibilityReport, build_sequence: BuildSequence, model_name: str = settings.DEFAULT_MODEL) -> dict:
    """Compiles the final markdown adaptation report."""
    summary_text = (
        f"# Synthexis Adaptation Report\n"
        f"**Feasibility Status:** {feasibility_report.overall_status}\n"
        f"**Estimated VRAM:** {feasibility_report.estimated_vram_gb} GB / Available: {feasibility_report.available_vram_gb} GB\n"
        f"**Build Steps:** {build_sequence.total_steps} modular components ready for implementation.\n"
    )
    return {
        "summary": summary_text,
        "status": "COMPLETED",
        "total_steps": build_sequence.total_steps
    }
