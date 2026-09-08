"""
Autonomous Code Generation Agent for Paper-2-Project.

Executes the Dual-Engine Tournament & 3-Layer Verified Code Synthesizer:
1. Parallel synthesis via Google Gemini (deep context & math) and Hugging Face Qwen 2.5 Coder 32B.
2. 3-Layer Verification:
   - Layer 1: Strict AST syntax & rejection of hollow placeholder stubs.
   - Layer 2: Paper Grounding score (dynamically matched against extracted hyperparameters).
   - Layer 3: Dummy Forward Pass Execution (tensor dimension & shape compatibility).
3. Tournament winner selection + 1-pass Reflexion auto-repair on shape errors.
All prompts, constants, and fallback hyperparameters are dynamically imported.
"""

import ast
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings
from app.schemas.pipeline import ExtractedParameters, ComponentGraph
from app.core.model_router import ModelRouter
from app.core.dual_code_engine import dual_code_engine, extract_python_code
from app.core.code_verifier import code_verifier
from app.core.prompts import build_codegen_agent_prompt, build_reflexion_repair_prompt
from app.core.constants import DEFAULT_HYPERPARAMETERS, DEFAULT_PIPELINE_FILES


def validate_python_syntax(code: str) -> Tuple[bool, str]:
    """Validates PyTorch source code using Python's built-in AST parser."""
    clean_code = extract_python_code(code)
    try:
        ast.parse(clean_code.strip())
        return True, "Syntax OK"
    except SyntaxError as err:
        return False, f"SyntaxError on line {err.lineno}: {err.msg}"
    except Exception as e:
        return False, f"AST Parse Error: {str(e)}"


def validate_cross_file_imports(codebase_files: Dict[str, str]) -> Dict[str, Any]:
    """
    Whole-codebase cross-file import validation:
    Scans train.py and evaluate.py (and other pipeline scripts) using AST to
    verify that imported model classes match the symbols exported by models/*.py.
    """
    model_exports: Dict[str, set] = {}
    all_exported_symbols: set = set()

    for f_path, code in codebase_files.items():
        f_norm = f_path.replace("\\", "/").lower()
        if "model" in f_norm:
            exports = set()
            try:
                tree = ast.parse(code)
                for node in tree.body:
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        exports.add(node.name)
            except Exception:
                pass
            model_exports[f_path] = exports
            all_exported_symbols.update(exports)

    errors: List[str] = []
    scanned_files: List[str] = []

    target_scripts = [
        f for f in codebase_files.keys()
        if any(k in f.replace("\\", "/").lower() for k in ["train", "eval", "test", "main"])
    ]

    for script_name in target_scripts:
        code = codebase_files.get(script_name, "")
        if not code:
            continue
        scanned_files.append(script_name)
        try:
            tree = ast.parse(code)
        except Exception as e:
            errors.append(f"{script_name}: AST parse error: {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                # Check if this import refers to local models (e.g. models.xxx, model, models)
                is_local_model_import = (
                    mod.startswith("models.") or
                    mod == "models" or
                    mod.startswith("model.") or
                    mod == "model"
                )
                if is_local_model_import:
                    matching_exports = set()
                    specific_match = False
                    for m_path, m_symbols in model_exports.items():
                        clean_m = m_path.replace("\\", "/").replace("/", ".")
                        if clean_m.endswith(".py"):
                            clean_m = clean_m[:-3]
                        if mod == clean_m or mod.split(".")[-1] == clean_m.split(".")[-1]:
                            matching_exports.update(m_symbols)
                            specific_match = True

                    if not specific_match:
                        matching_exports = all_exported_symbols

                    for alias in node.names:
                        sym_name = alias.name
                        if sym_name == "*":
                            continue
                        if matching_exports and sym_name not in matching_exports:
                            errors.append(
                                f"{script_name} imports '{sym_name}' from '{mod}', but '{sym_name}' is not exported by {list(model_exports.keys())}. (Available: {sorted(list(matching_exports))})"
                            )

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "errors": errors,
        "scanned_files": scanned_files,
        "model_exports": {k: sorted(list(v)) for k, v in model_exports.items()}
    }


def run_code_gen_agent(
    component_name: str = "PaperModel",
    parameters: Optional[ExtractedParameters] = None,
    model_name: str = settings.DEFAULT_MODEL,
    paper_id: Optional[str] = None,
    component_graph: Any = None
) -> Dict[str, Any]:
    """
    Dual-Engine Tournament & 3-Layer Verified Code Synthesizer.
    Completely decoupled from hardcoded vision assumptions to handle any research paper.
    """
    # 1. Dynamic parameter initialization from generic defaults
    param_dict = dict(DEFAULT_HYPERPARAMETERS)

    if parameters:
        for attr in ["learning_rate", "batch_size", "optimizer", "backbone"]:
            val = getattr(parameters, attr, None)
            if val is not None:
                param_dict[attr] = str(getattr(val, "value", val))

    # 2. Dynamic Paper Context Enrichment: load real extracted paper metadata
    paper_title = component_name
    paper_abstract = ""
    if paper_id:
        clean_pid = paper_id.strip("[]")
        json_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{clean_pid}.json")
        if not os.path.exists(json_path):
            alt_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"paper_{clean_pid}.json")
            if os.path.exists(alt_path):
                json_path = alt_path

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    paper_data = json.load(jf)
                    meta = paper_data.get("metadata", {})
                    paper_title = meta.get("title") or paper_data.get("title") or paper_title
                    paper_abstract = meta.get("abstract") or paper_data.get("abstract") or ""

                    # Extract hyperparameters from both JSON schemas
                    raw_hyp = paper_data.get("hyperparameters", {})
                    for hk, hv in raw_hyp.items():
                        if hv:
                            param_dict[hk] = str(hv)

                    ext_params = paper_data.get("extracted_parameters", {})
                    for pk, pv in ext_params.items():
                        if isinstance(pv, dict) and "value" in pv:
                            param_dict[pk] = str(pv["value"])
                        elif isinstance(pv, (str, int, float)):
                            param_dict[pk] = str(pv)
            except Exception as e:
                print(f"[CodeGen Agent WARN] Failed to load extracted json for '{paper_id}': {e}")

    # 3. Dynamic File Topology: deduce files from component graph or modular pipeline
    if isinstance(component_graph, ComponentGraph) and component_graph.components:
        comp_types = [c.type for c in component_graph.components if c and c.type]
        files_to_generate = ["config.py", "dataset.py"]
        for c_type in comp_types:
            clean_c = c_type.lower().replace(" ", "_")
            f_target = f"models/{clean_c}.py"
            if f_target not in files_to_generate:
                files_to_generate.append(f_target)
        files_to_generate.extend(["losses.py", "train.py", "evaluate.py"])
    else:
        files_to_generate = list(DEFAULT_PIPELINE_FILES)

    codebase_files = {}
    code_evaluations = {}
    total_loc = 0

    gemini_engine_label = f"Google Gemini ({dual_code_engine.gemini_model})"
    hf_engine_label = f"Hugging Face ({dual_code_engine.hf_model})"

    print(f"[CodeGen Agent] Synthesizing {len(files_to_generate)} PyTorch files for '{paper_title}' using Dual Engine ({gemini_engine_label} + {hf_engine_label})...")

    for f_path in files_to_generate:
        # Include references to previously synthesized modules to ensure cross-file import harmony
        sibling_context = ""
        if codebase_files:
            recent_names = list(codebase_files.keys())[-3:]
            snippets = []
            for rk in recent_names:
                code_lines = codebase_files[rk].splitlines()
                defs = [line for line in code_lines if line.startswith("class ") or line.startswith("def ")]
                if defs:
                    snippets.append(f"File '{rk}' defines:\n" + "\n".join(defs[:4]))
            if snippets:
                sibling_context = "\nCROSS-FILE DEPENDENCY CONTEXT:\n" + "\n".join(snippets) + "\n"

        prompt = build_codegen_agent_prompt(
            component_name=component_name,
            file_path=f_path,
            paper_title=paper_title,
            paper_abstract=paper_abstract,
            param_dict=param_dict,
            sibling_context=sibling_context
        )
        winning_code = ""
        best_eval: Dict[str, Any] = {}
        engine_label = "Dual-Engine"

        # Dynamic expected modules based on target file and paper parameters
        expected_modules = [component_name]
        for pv in param_dict.values():
            if isinstance(pv, str) and len(pv) > 2 and not pv.replace(".", "").isdigit():
                expected_modules.append(pv)

        f_lower = f_path.lower()
        if "loss" in f_lower:
            expected_modules.extend(["loss", "criterion", "forward"])
        elif "dataset" in f_lower or "data" in f_lower:
            expected_modules.extend(["dataset", "__getitem__", "__len__"])
        elif "config" in f_lower:
            expected_modules.extend(["config", "learning_rate"])
        elif "train" in f_lower:
            expected_modules.extend(["train", "optimizer", "epoch"])
        elif "eval" in f_lower:
            expected_modules.extend(["eval", "metric"])
        else:
            expected_modules.extend(["nn.Module", "forward", "__init__"])

        try:
            # 1. Parallel Dual-Engine Generation (Gemini Flash + Hugging Face Qwen 2.5 Coder)
            candidates = dual_code_engine.generate_dual_candidates_sync(prompt)
            gemini_cand = candidates.get("gemini", {})
            hf_cand = candidates.get("huggingface", {})

            # 2. Evaluate Candidate A (Google Gemini)
            eval_gemini = None
            if gemini_cand.get("code"):
                eval_gemini = code_verifier.evaluate_candidate(
                    gemini_cand["code"],
                    file_path=f_path,
                    parameters=param_dict,
                    expected_modules=expected_modules
                )

            # 3. Evaluate Candidate B (Hugging Face Qwen 2.5 Coder 32B)
            eval_hf = None
            if hf_cand.get("code"):
                eval_hf = code_verifier.evaluate_candidate(
                    hf_cand["code"],
                    file_path=f_path,
                    parameters=param_dict,
                    expected_modules=expected_modules
                )

            # 4. Tournament Winner Selection
            if eval_gemini and eval_hf:
                gemini_exec_ok = eval_gemini["layer3_exec"]["passed"]
                hf_exec_ok = eval_hf["layer3_exec"]["passed"]

                if hf_exec_ok and not gemini_exec_ok:
                    winning_code = hf_cand["code"]
                    best_eval = eval_hf
                    engine_label = hf_engine_label
                elif gemini_exec_ok and not hf_exec_ok:
                    winning_code = gemini_cand["code"]
                    best_eval = eval_gemini
                    engine_label = gemini_engine_label
                else:
                    if eval_hf["total_score"] >= eval_gemini["total_score"]:
                        winning_code = hf_cand["code"]
                        best_eval = eval_hf
                        engine_label = hf_engine_label
                    else:
                        winning_code = gemini_cand["code"]
                        best_eval = eval_gemini
                        engine_label = gemini_engine_label

            elif eval_hf:
                winning_code = hf_cand["code"]
                best_eval = eval_hf
                engine_label = hf_engine_label
            elif eval_gemini:
                winning_code = gemini_cand["code"]
                best_eval = eval_gemini
                engine_label = gemini_engine_label
            else:
                # Fallback to standard ModelRouter if dual keys not active
                print(f"[CodeGen Agent] Dual engines unavailable for '{f_path}'. Falling back to standard router...")
                router = ModelRouter()
                raw_res, _ = router.generate(prompt, model_id=model_name)
                fallback_code = extract_python_code(raw_res)
                best_eval = code_verifier.evaluate_candidate(fallback_code, file_path=f_path, parameters=param_dict, expected_modules=expected_modules)
                winning_code = fallback_code
                engine_label = "Standard ModelRouter"

            # 5. Multi-Iteration Reflexion Self-Repair (max_retries=2)
            # Re-tests AST syntax and tensor forward pass execution using code_verifier.evaluate_candidate()
            retry_count = 0
            max_retries = 2
            while not best_eval.get("is_valid", False) and winning_code and retry_count < max_retries:
                error_detail = ""
                layer1 = best_eval.get("layer1_ast", {})
                layer3 = best_eval.get("layer3_exec", {})

                if not layer1.get("valid", True):
                    error_detail = f"Syntax Error: {layer1.get('msg', 'AST validation failed')}"
                elif not layer3.get("passed", True):
                    error_detail = f"Tensor Forward Pass Error: {layer3.get('error', 'Tensor execution failed')}"

                if not error_detail:
                    break

                retry_count += 1
                print(f"[CodeGen Reflexion] Iteration {retry_count}/{max_retries} healing '{f_path}' ({error_detail})...")
                reflexion_prompt = build_reflexion_repair_prompt(
                    file_path=f_path,
                    error_detail=error_detail,
                    original_code=winning_code
                )
                router = ModelRouter()
                repaired_raw, _ = router.generate(reflexion_prompt, model_id=model_name)
                repaired_code = extract_python_code(repaired_raw)
                repaired_eval = code_verifier.evaluate_candidate(
                    repaired_code,
                    file_path=f_path,
                    parameters=param_dict,
                    expected_modules=expected_modules
                )

                if repaired_eval.get("total_score", 0) > best_eval.get("total_score", 0) or repaired_eval.get("is_valid", False):
                    winning_code = repaired_code
                    best_eval = repaired_eval
                    repair_tag = f"(Reflexion Repaired - Iteration {retry_count})"
                    if "(Reflexion Repaired" in engine_label:
                        engine_label = re.sub(r"\(Reflexion Repaired.*?\)", repair_tag, engine_label)
                    else:
                        engine_label += f" {repair_tag}"

                if best_eval.get("is_valid", False):
                    break

        except Exception as e:
            print(f"[CodeGen Agent ERROR] Generation exception for '{f_path}': {e}")
            winning_code = f"# Error generating {f_path}: {e}\nimport torch\nimport torch.nn as nn\n"
            best_eval = code_verifier.evaluate_candidate(winning_code, file_path=f_path)
            engine_label = "Exception Handler"

        file_loc = len(winning_code.splitlines())
        total_loc += file_loc

        codebase_files[f_path] = winning_code
        code_evaluations[f_path] = {
            "is_valid": best_eval.get("is_valid", False),
            "total_score": best_eval.get("total_score", 0.0),
            "engine_used": engine_label,
            "grounding_score": best_eval.get("layer2_grounding", {}).get("score", 0.0),
            "forward_pass": best_eval.get("layer3_exec", {}).get("passed", False),
            "output_shape": best_eval.get("layer3_exec", {}).get("output_shape", "N/A"),
            "ast_msg": best_eval.get("layer1_ast", {}).get("msg", "OK"),
            "loc": file_loc
        }

    # 6. Whole-codebase cross-file import validation
    import_validation = validate_cross_file_imports(codebase_files)
    if not import_validation["valid"]:
        print(f"[CodeGen Agent WARN] Cross-file import discrepancies detected: {import_validation['errors']}")

    all_valid = all(v["is_valid"] for v in code_evaluations.values()) and import_validation["valid"]
    avg_score = round(sum(v["total_score"] for v in code_evaluations.values()) / max(1, len(code_evaluations)), 1)

    print(f"[CodeGen Agent] Completed synthesis: {len(codebase_files)} files | Total LOC: {total_loc} | Avg Quality: {avg_score}% | All Valid: {all_valid}")

    # Physical disk save: write synthesized Python files to storage/codes output directory
    clean_id = (paper_id or component_name).strip("[]")
    codes_base = getattr(settings, "CODES_DIR", os.path.join(settings.STORAGE_DIR, "codes"))
    out_codebase_dir = os.path.join(codes_base, f"paper_{clean_id}")
    saved_paths = []

    for rel_path, code_content in codebase_files.items():
        abs_file_path = os.path.join(out_codebase_dir, rel_path)
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
        with open(abs_file_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        saved_paths.append(abs_file_path)

    print(f"[CodeGen Agent] Saved {len(saved_paths)} codebase files to disk at: {out_codebase_dir}")

    # Primary code string for UI display: prioritize core model or network file
    primary_code = ""
    for cand in files_to_generate:
        if "model" in cand or "network" in cand or "encoder" in cand:
            primary_code = codebase_files.get(cand, "")
            if primary_code:
                break
    if not primary_code:
        primary_code = codebase_files.get("train.py", list(codebase_files.values())[0] if codebase_files else "")

    return {
        "component_name": component_name,
        "paper_id": paper_id,
        "is_valid": all_valid,
        "avg_quality_score": avg_score,
        "total_files": len(codebase_files),
        "total_loc": total_loc,
        "output_directory": out_codebase_dir,
        "saved_files": saved_paths,
        "primary_code": primary_code,
        "codebase_files": codebase_files,
        "code_evaluations": code_evaluations,
        "import_validation": import_validation,
        # Backward compatibility for ast_validations key
        "ast_validations": code_evaluations
    }
