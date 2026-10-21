import json
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.pipeline import BuildSequence, BuildSequenceStep, FeasibilityReport, ComponentGraph
from app.core.model_router import ModelRouter
from app.core.dag_validator import DAGValidator, DAGValidationResult


def _parse_steps_from_json(json_str: str) -> List[BuildSequenceStep]:
    """Extracts BuildSequenceStep models from raw JSON string."""
    clean_str = json_str.strip()
    if "```json" in clean_str:
        clean_str = clean_str.split("```json")[-1].split("```")[0].strip()
    elif "```" in clean_str:
        clean_str = clean_str.split("```")[1].strip()

    data = json.loads(clean_str)
    raw_steps = data.get("steps", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    steps = []
    for idx, s in enumerate(raw_steps, start=1):
        if not isinstance(s, dict):
            continue
        steps.append(BuildSequenceStep(
            step_num=s.get("step_num", idx),
            component_name=s.get("component_name", f"module_{idx}").strip(),
            description=s.get("description", "Codebase component step"),
            dependencies=s.get("dependencies", []),
            file_path=s.get("file_path", f"step_{idx}.py")
        ))
    return steps


def _order_steps_topologically(steps: List[BuildSequenceStep], execution_order: List[str]) -> List[BuildSequenceStep]:
    """Orders steps strictly according to deterministic topological order and assigns clean sequential step_num."""
    step_by_name = {s.component_name: s for s in steps}
    ordered = []
    for idx, name in enumerate(execution_order, start=1):
        if name in step_by_name:
            s = step_by_name[name]
            s.step_num = idx
            ordered.append(s)
    return ordered


def run_sequencing_agent(
    component_graph: Any = None, 
    feasibility_report: Optional[FeasibilityReport] = None, 
    model_name: str = settings.DEFAULT_MODEL,
    max_repair_retries: int = 2
) -> BuildSequence:
    """
    Analyzes paper ComponentGraph and FeasibilityReport to construct a 
    dependency-ordered Directed Acyclic Graph (DAG) engineering build sequence.
    Guarantees deterministic topological ordering and validates DAG properties
    with bounded LLM self-correction.
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
2. Dependencies must form a strict Directed Acyclic Graph (DAG) with NO circular dependencies.
3. Every declared dependency must correspond to a valid component_name defined in the steps.
4. File paths MUST reflect modular Python architecture (`config.py`, `dataset.py`, `models/`, `losses.py`, `train.py`).
"""

    router = ModelRouter()
    current_prompt = prompt

    for attempt in range(max_repair_retries + 1):
        try:
            raw_res, _ = router.generate(current_prompt, model_id=model_name)
            steps = _parse_steps_from_json(raw_res)

            # Deterministic DAG validation
            val_result = DAGValidator.validate(steps)

            if val_result.is_valid:
                ordered_steps = _order_steps_topologically(steps, val_result.execution_order)
                print(f"[Sequencing Agent] Validated DAG build plan: {len(ordered_steps)} milestones (Topological order: {' -> '.join(val_result.execution_order)}).")
                return BuildSequence(steps=ordered_steps, total_steps=len(ordered_steps))

            # If invalid and retries remain, feed errors back into bounded repair prompt
            print(f"[Sequencing Agent WARN] DAG validation failed on attempt {attempt + 1}: {[i.code for i in val_result.issues]}")
            if attempt < max_repair_retries:
                error_feedback = DAGValidator.format_error_feedback(val_result)
                current_prompt = (
                    f"{prompt}\n\n"
                    f"--- PREVIOUS GENERATION ERROR FEEDBACK ---\n"
                    f"{error_feedback}\n\n"
                    f"Please regenerate the complete JSON plan fixing all listed errors."
                )

        except Exception as e:
            print(f"[Sequencing Agent WARN] Generation/parsing error on attempt {attempt + 1}: {e}")

    # Fallback to verified baseline DAG sequence if all attempts fail
    print("[Sequencing Agent WARN] Max repair retries exhausted or LLM unavailable. Using verified baseline DAG.")
    fallback_steps = [
        BuildSequenceStep(step_num=1, component_name="config", description="Hyperparameter configuration", file_path="config.py"),
        BuildSequenceStep(step_num=2, component_name="dataset", description="PyTorch Dataset Loader", dependencies=["config"], file_path="dataset.py"),
        BuildSequenceStep(step_num=3, component_name="encoder", description="Visual Feature Backbone", dependencies=["dataset"], file_path="models/encoder.py"),
        BuildSequenceStep(step_num=4, component_name="fusion", description="Feature Fusion Module", dependencies=["encoder"], file_path="models/fusion.py"),
        BuildSequenceStep(step_num=5, component_name="loss", description="Loss Function Module", dependencies=["fusion"], file_path="losses.py"),
        BuildSequenceStep(step_num=6, component_name="trainer", description="PyTorch Training Loop", dependencies=["dataset", "fusion", "loss"], file_path="train.py")
    ]
    fb_val = DAGValidator.validate(fallback_steps)
    ordered_fb = _order_steps_topologically(fallback_steps, fb_val.execution_order)
    return BuildSequence(steps=ordered_fb, total_steps=len(ordered_fb))
