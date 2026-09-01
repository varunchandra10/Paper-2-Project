import json
from app.core.config import settings
from app.schemas.pipeline import BuildSequence


def run_specification_agent(build_sequence: BuildSequence, model_name: str = settings.DEFAULT_MODEL) -> dict:
    """Generates project specification tree and file mapping."""
    files = [step.file_path for step in build_sequence.steps]
    return {
        "project_name": "SynthexisAdaptedModel",
        "file_tree": files,
        "framework": "PyTorch 2.x"
    }
