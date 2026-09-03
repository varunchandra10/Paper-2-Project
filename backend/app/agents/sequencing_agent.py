import json
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.pipeline import BuildSequence, BuildSequenceStep, FeasibilityReport, ComponentGraph
from app.core.model_router import ModelRouter


def run_sequencing_agent(
    component_graph: Any = None, 
    feasibility_report: Optional[FeasibilityReport] = None, 
    model_name: str = settings.DEFAULT_MODEL
) -> BuildSequence:
    """
    Analyzes paper ComponentGraph and FeasibilityReport to construct a 
    dependency-ordered Directed Acyclic Graph (DAG) engineering build sequence.
    Rule: Cheap, low-risk modules (dataset loader, config) MUST precede compute-heavy layers.
    """
    comp_list = []
    if isinstance(component_graph, ComponentGraph) and component_graph.components:
        comp_list = [c.model_dump() if hasattr(c, "model_dump") else c for c in component_graph.components]
    elif isinstance(component_graph, dict):
        comp_list = component_graph.get("components", [])

    prompt = f"""You are a Principal AI Architect and Systems Optimization Lead. Construct a dependency-ordered Directed Acyclic Graph (DAG) build sequence for synthesizing a complete PyTorch codebase for this research paper architecture.

--- COMPONENT GRAPH ---
{json.dumps(comp_list, indent=2)}

INSTRUCTION:
Return ONLY a valid JSON object matching the following structure:
{{
  "steps": [
    {{
      "step_num": 1,
      "component_name": "config",
      "description": "Hyperparameter configuration and environment bounds",
      "dependencies": [],
      "file_path": "config.py"
    }},
    {{
      "step_num": 2,
      "component_name": "dataset",
      "description": "PyTorch dataset loader and spatial image transformations",
      "dependencies": ["config"],
      "file_path": "dataset.py"
    }},
    {{
      "step_num": 3,
      "component_name": "backbone_encoder",
      "description": "Visual feature extraction backbone encoder",
      "dependencies": ["config", "dataset"],
      "file_path": "models/backbone.py"
    }},
    {{
      "step_num": 4,
      "component_name": "attention_fusion",
      "description": "Feature fusion and cross-attention bottleneck",
      "dependencies": ["backbone_encoder"],
      "file_path": "models/fusion.py"
    }},
    {{
      "step_num": 5,
      "component_name": "loss_function",
      "description": "Loss calculation module",
      "dependencies": ["attention_fusion"],
      "file_path": "losses.py"
    }},
    {{
      "step_num": 6,
      "component_name": "trainer",
      "description": "PyTorch training, validation, and evaluation loop",
      "dependencies": ["dataset", "attention_fusion", "loss_function"],
      "file_path": "train.py"
    }}
  ]
}}

BUILD RULES:
1. Low-complexity, data-loading steps MUST precede compute-heavy model training steps.
2. File paths MUST reflect modular Python architecture (`config.py`, `dataset.py`, `models/`, `losses.py`, `train.py`).
"""

    try:
        router = ModelRouter()
        raw_res, _ = router.generate(prompt, model_id=model_name)

        json_str = raw_res
        if "```json" in raw_res:
            json_str = raw_res.split("```json")[-1].split("```")[0]
        elif "```" in raw_res:
            json_str = raw_res.split("```")[1]

        data = json.loads(json_str.strip())
        raw_steps = data.get("steps", [])

        steps = []
        for idx, s in enumerate(raw_steps, start=1):
            steps.append(BuildSequenceStep(
                step_num=s.get("step_num", idx),
                component_name=s.get("component_name", f"Module_{idx}"),
                description=s.get("description", "Codebase component step"),
                dependencies=s.get("dependencies", []),
                file_path=s.get("file_path", f"step_{idx}.py")
            ))

        print(f"[Sequencing Agent] Successfully constructed DAG build plan with {len(steps)} milestones.")
        return BuildSequence(steps=steps, total_steps=len(steps))

    except Exception as e:
        print(f"[Sequencing Agent WARN] LLM call fallback ({e}). Using baseline DAG sequence.")
        fallback_steps = [
            BuildSequenceStep(step_num=1, component_name="config", description="Hyperparameter configuration", file_path="config.py"),
            BuildSequenceStep(step_num=2, component_name="dataset", description="PyTorch Dataset Loader", dependencies=["config"], file_path="dataset.py"),
            BuildSequenceStep(step_num=3, component_name="encoder", description="Visual Feature Backbone", dependencies=["dataset"], file_path="models/encoder.py"),
            BuildSequenceStep(step_num=4, component_name="fusion", description="Feature Fusion Module", dependencies=["encoder"], file_path="models/fusion.py"),
            BuildSequenceStep(step_num=5, component_name="loss", description="Loss Function Module", dependencies=["fusion"], file_path="losses.py"),
            BuildSequenceStep(step_num=6, component_name="trainer", description="PyTorch Training Loop", dependencies=["dataset", "fusion", "loss"], file_path="train.py")
        ]
        return BuildSequence(steps=fallback_steps, total_steps=len(fallback_steps))

