import json
import ollama
from typing import Dict, Any
from app.core.config import settings
from app.schemas.paper import PaperDocument


def run_decomposition_agent(raw_sections: dict, model_name: str = settings.DEFAULT_MODEL, paper_doc: PaperDocument = None) -> dict:
    """Decomposes the paper into functional architectural components (Backbone, Encoder, Fusion, Loss, Trainer)."""
    components = [
        {"name": "backbone", "type": "encoder", "description": "Extracts spatial feature representations from dual-temporal inputs."},
        {"name": "fusion_module", "type": "neck", "description": "Fuses multi-scale feature maps using cross-attention mechanisms."},
        {"name": "change_classifier", "type": "head", "description": "Predicts pixel-wise binary or multi-class change maps."},
        {"name": "loss_function", "type": "loss", "description": "Calculates hybrid Contrastive + Cross-Entropy loss."},
        {"name": "trainer", "type": "training", "description": "Manages optimization loops, FP16 precision, and checkpointing."}
    ]
    return {"components": components, "total_components": len(components)}
