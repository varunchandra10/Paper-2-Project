import json
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.pipeline import BuildSequence, FeasibilityReport, ComponentGraph, ExtractedParameters
from app.core.model_router import ModelRouter


def run_specification_agent(
    component_graph: Any = None,
    feasibility_report: Optional[FeasibilityReport] = None,
    build_sequence: Optional[BuildSequence] = None,
    parameters: Optional[ExtractedParameters] = None,
    model_name: str = settings.DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Compiles a formal, structured engineering blueprint (Project Specification)
    from ComponentGraph, FeasibilityReport, parameters, and BuildSequence.
    """
    comp_names = []
    if isinstance(component_graph, ComponentGraph) and component_graph.components:
        comp_names = [c.name for c in component_graph.components]
    elif isinstance(component_graph, dict):
        comp_names = [c.get("name", "Module") for c in component_graph.get("components", [])]

    if not comp_names:
        comp_names = ["BackboneEncoder", "CrossAttentionFusion", "ChangeClassifierDecoder"]

    file_tree = []
    if build_sequence and build_sequence.steps:
        file_tree = [s.file_path for s in build_sequence.steps]
    else:
        file_tree = ["config.py", "dataset.py", "models/encoder.py", "models/fusion.py", "losses.py", "train.py"]

    lr = "0.0001"
    batch_size = "16"
    optimizer = "AdamW"
    loss_fn = "CrossEntropyLoss"

    if parameters:
        lr = str(parameters.learning_rate.value)
        batch_size = str(parameters.batch_size.value)
        optimizer = str(parameters.optimizer.value)
        loss_fn = str(parameters.loss_function.value)

    prompt = f"""You are a Machine Learning Systems Lead Architect. Compile a formal engineering specification blueprint for synthesizing this paper's codebase.

--- TARGET COMPONENTS ---
{json.dumps(comp_names, indent=2)}

--- TARGET FILE TREE ---
{json.dumps(file_tree, indent=2)}

--- PARAMETERS & TRAINING SETUP ---
- Learning Rate: {lr}
- Batch Size: {batch_size}
- Optimizer: {optimizer}
- Loss Function: {loss_fn}

INSTRUCTION:
Return ONLY a valid JSON object matching the following structure:
{{
  "project_name": "SynthexisAdaptedModel",
  "framework": "PyTorch 2.x",
  "requirements": "Python 3.10+, PyTorch 2.0+, CUDA 11.8+, NumPy, PyMuPDF",
  "architecture_overview": "Bi-temporal inputs ➔ Backbone feature extraction ➔ Feature fusion bottleneck ➔ Classifier decoder ➔ Output map",
  "components": {json.dumps(comp_names)},
  "file_tree": {json.dumps(file_tree)},
  "training_setup": "Optimizer: {optimizer} | LR: {lr} | Loss: {loss_fn} | Batch Size: {batch_size} | FP16 Mixed Precision",
  "evaluation_metrics": ["F1-Score", "IoU", "Accuracy", "FLOPs"],
  "hardware_assumptions": ["Host GPU VRAM target: 8.0 GB", "CUDA PyTorch acceleration active"]
}}
"""

    try:
        router = ModelRouter()
        raw_res, _ = router.generate(prompt, model_id=model_name)

        json_str = raw_res
        if "```json" in raw_res:
            json_str = raw_res.split("```json")[-1].split("```")[0]
        elif "```" in raw_res:
            json_str = raw_res.split("```")[1]

        spec_data = json.loads(json_str.strip())
        print(f"[Specification Agent] Successfully compiled project specification blueprint ({len(spec_data.get('components', []))} components).")
        return spec_data

    except Exception as e:
        print(f"[Specification Agent WARN] LLM call fallback ({e}). Using baseline specification blueprint.")
        return {
            "project_name": "SynthexisAdaptedModel",
            "framework": "PyTorch 2.x",
            "requirements": "Python 3.10+, PyTorch 2.0+, CUDA 11.8+, NumPy",
            "architecture_overview": "Bi-temporal input processing ➔ Visual backbone ➔ Cross-attention fusion ➔ Decoder mask",
            "components": comp_names,
            "file_tree": file_tree,
            "training_setup": f"Optimizer: {optimizer} | Base LR: {lr} | Loss: {loss_fn} | Batch Size: {batch_size} | FP16 Enabled",
            "evaluation_metrics": ["F1-Score", "IoU", "Precision", "Recall"],
            "hardware_assumptions": ["Host GPU CUDA PyTorch acceleration active"]
        }

