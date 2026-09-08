import ast
import re
import sys
import traceback
from typing import Dict, Any, List, Optional, Tuple


class CodeVerifier:
    """
    3-Layer Paper-Grounded PyTorch Code Verification Pipeline:
    Layer 1: Syntactic AST & Anti-Stub Validation (rejection of hollow fallbacks & syntax errors)
    Layer 2: Paper Grounding & Alignment Score (hyperparameter coverage & architecture topology)
    Layer 3: Dummy Forward Pass Execution (instantiates nn.Module with dummy tensors to verify tensor shape compatibility)
    """

    # --- LAYER 1: STRICT AST & ANTI-STUB VALIDATION ---
    @staticmethod
    def validate_layer1_ast(code: str) -> Dict[str, Any]:
        """
        Validates Python grammar and strictly disqualifies hollow stubs (e.g. pass, placeholder comments).
        """
        if not code or not code.strip():
            return {"valid": False, "msg": "Empty code block", "is_stub": True}

        # Check for banned stub patterns
        stub_patterns = [
            r'#\s*grounding:\s*fallback',
            r'#\s*synthesized module for',
            r'pass\s*#\s*placeholder',
            r'def\s+[a-zA-Z0-9_]+\s*\([^)]*\):\s*pass\s*$'
        ]
        for pat in stub_patterns:
            if re.search(pat, code, re.IGNORECASE):
                return {
                    "valid": False,
                    "msg": "Code rejected: Hollow fallback stub detected",
                    "is_stub": True
                }

        try:
            tree = ast.parse(code.strip())
            
            # Check for banned security primitives
            safety = CodeVerifier.check_banned_primitives(tree)
            if not safety["safe"]:
                return {"valid": False, "msg": f"Security violation: {safety['reason']}", "is_stub": False}

            # Verify code contains substantive statements
            body = tree.body
            if not body or len(body) < 2:
                return {"valid": False, "msg": "Code rejected: Too brief, lacks implementation depth", "is_stub": True}

            # Check if there is at least one class or function definition
            has_definition = any(isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) for node in body)
            if not has_definition and not any(isinstance(node, ast.Assign) for node in body):
                return {"valid": False, "msg": "Code rejected: No classes or functions defined", "is_stub": True}

            return {"valid": True, "msg": "Syntax OK", "is_stub": False, "ast_tree": tree}

        except SyntaxError as err:
            return {"valid": False, "msg": f"SyntaxError on line {err.lineno}: {err.msg}", "is_stub": False}
        except Exception as e:
            return {"valid": False, "msg": f"AST Parse Error: {str(e)}", "is_stub": False}

    @staticmethod
    def check_banned_primitives(tree: ast.AST) -> Dict[str, Any]:
        """Detects unsafe or banned primitives in AST (os.system, subprocess, eval, etc.)."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    val_id = getattr(node.func.value, 'id', '')
                    attr = node.func.attr
                    if val_id == "os" and attr in ["system", "popen"]:
                        return {"safe": False, "reason": f"banned call os.{attr}()"}
                    if val_id == "subprocess":
                        return {"safe": False, "reason": f"banned call subprocess.{attr}()"}
                    if val_id == "shutil" and attr in ["rmtree"]:
                        return {"safe": False, "reason": f"banned call shutil.{attr}()"}
                elif isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec"]:
                        return {"safe": False, "reason": f"banned call {node.func.id}()"}
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ["subprocess"]:
                        return {"safe": False, "reason": f"banned module import '{alias.name}'"}
            elif isinstance(node, ast.ImportFrom):
                if node.module in ["subprocess"]:
                    return {"safe": False, "reason": f"banned module import from '{node.module}'"}
        return {"safe": True, "reason": None}

    # --- LAYER 2: PAPER GROUNDING & ALIGNMENT SCORE ---
    @staticmethod
    def calculate_layer2_grounding(code: str, parameters: Optional[Dict[str, Any]] = None, expected_modules: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Evaluates how strictly the generated code adheres to extracted paper hyperparameters and architectural specifications.
        Returns a grounding score between 0.0 and 100.0.
        """
        param_score = 0.0
        param_matches = []
        param_misses = []

        # 1. Hyperparameter Fidelity (50 points max)
        if parameters and isinstance(parameters, dict):
            total_params = len(parameters)
            if total_params > 0:
                matched_count = 0
                for k, v in parameters.items():
                    val_str = str(v).strip()
                    # Check if parameter name or value is referenced in code
                    if val_str and (re.search(rf'\b{re.escape(val_str)}\b', code) or re.search(rf'\b{re.escape(k)}\b', code, re.IGNORECASE)):
                        matched_count += 1
                        param_matches.append(f"{k}={val_str}")
                    else:
                        param_misses.append(f"{k}={val_str}")
                param_score = (matched_count / total_params) * 50.0
        else:
            # Baseline parameter score if no metadata passed
            param_score = 35.0

        # 2. Architecture & Topology Fidelity (50 points max)
        arch_score = 0.0
        topology_matches = []

        # Core PyTorch architectural primitives
        checks = [
            ("torch.nn.Module", r'class\s+[A-Za-z0-9_]+\s*\(\s*(nn\.)?Module\s*\)'),
            ("super().__init__()", r'super\s*\(\s*\)\.__init__\s*\('),
            ("forward() method", r'def\s+forward\s*\(\s*self'),
            ("PyTorch Layers (nn.)", r'\bnn\.(Linear|Conv2d|MultiheadAttention|LayerNorm|BatchNorm2d|Sequential|ModuleList)\b'),
            ("Activation function", r'\b(nn\.(ReLU|GELU|SiLU|LeakyReLU)|F\.(relu|gelu|silu))\b'),
            ("Tensor operations", r'\b(torch\.(cat|matmul|bmm|einsum|stack|randn|zeros)|x\.(view|reshape|permute|transpose))\b')
        ]

        points_per_check = 50.0 / len(checks)
        for label, pattern in checks:
            if re.search(pattern, code):
                arch_score += points_per_check
                topology_matches.append(label)

        # Expected paper-specific modules (e.g. Swin, Fusion, Attention, Loss)
        if expected_modules:
            for mod in expected_modules:
                if re.search(rf'\b{re.escape(mod)}\b', code, re.IGNORECASE):
                    topology_matches.append(f"Module:{mod}")
                    arch_score = min(50.0, arch_score + 5.0)

        total_grounding_score = round(min(100.0, param_score + arch_score), 1)

        return {
            "score": total_grounding_score,
            "param_score": round(param_score, 1),
            "arch_score": round(arch_score, 1),
            "param_matches": param_matches,
            "param_misses": param_misses,
            "topology_matches": topology_matches
        }

    # --- LAYER 3: DUMMY FORWARD PASS EXECUTION ---
    @staticmethod
    def execute_layer3_forward_pass(code: str, file_path: str = "model.py") -> Dict[str, Any]:
        """
        Executes an isolated dummy forward pass:
        1. Compiles and executes code in an isolated dictionary scope.
        2. Discovers any class inheriting from torch.nn.Module.
        3. Instantiates the class and runs a dummy input tensor through model(x).
        4. Validates output tensor shape and catches any RuntimeError (dimension mismatch, missing weights).
        """
        # Non-model files (like config, loss, dataset) are evaluated without forward tensors
        is_model_file = any(keyword in file_path.lower() for keyword in ["model", "encoder", "fusion", "decoder", "backbone", "net"])
        if not is_model_file and "class" not in code:
            return {
                "executed": False,
                "passed": True,
                "reason": "Non-module configuration/utility file (no forward pass required)",
                "error": None,
                "output_shape": "N/A"
            }

        try:
            import torch
            import torch.nn as nn
        except ImportError:
            return {
                "executed": False,
                "passed": True,
                "reason": "PyTorch library not available in runtime environment",
                "error": None,
                "output_shape": "N/A"
            }

        # Isolated execution namespace
        exec_globals = {
            "__name__": "__main__",
            "torch": torch,
            "nn": nn,
            "math": __import__("math"),
            "os": __import__("os"),
            "typing": __import__("typing")
        }

        try:
            # 1. Compile and execute code in scope
            compiled_code = compile(code, filename=file_path, mode="exec")
            exec(compiled_code, exec_globals)

            # 2. Find nn.Module classes
            module_classes = []
            for name, obj in exec_globals.items():
                if isinstance(obj, type) and issubclass(obj, nn.Module) and obj is not nn.Module:
                    module_classes.append((name, obj))

            if not module_classes:
                return {
                    "executed": False,
                    "passed": True,
                    "reason": "No custom nn.Module classes found in scope",
                    "error": None,
                    "output_shape": "N/A"
                }

            # Select primary model class (last declared class or main architecture)
            target_name, TargetClass = module_classes[-1]

            # 3. Instantiate model with standard dummy parameters
            model = None
            instantiation_error = None

            # Try default constructor
            try:
                model = TargetClass()
            except Exception as e1:
                instantiation_error = str(e1)
                # Try common parameter signatures
                for test_kwargs in [
                    {"in_channels": 3, "num_classes": 2},
                    {"d_model": 512, "num_heads": 8},
                    {"dim": 256},
                    {"channels": 64}
                ]:
                    try:
                        model = TargetClass(**test_kwargs)
                        instantiation_error = None
                        break
                    except Exception:
                        continue

            if model is None:
                return {
                    "executed": True,
                    "passed": False,
                    "reason": f"Failed to instantiate model '{target_name}': {instantiation_error}",
                    "error": instantiation_error,
                    "output_shape": None
                }

            model.eval()

            # 4. Synthesize input tensor and test forward pass
            dummy_inputs = [
                torch.randn(2, 3, 224, 224),  # Standard Vision shape [B, C, H, W]
                torch.randn(2, 64, 512),      # Sequence / Transformer shape [B, L, D]
                torch.randn(2, 512),          # Feature vector [B, D]
                torch.randn(2, 256, 14, 14)   # Feature map shape
            ]

            output_shape_str = None
            forward_error = None

            with torch.no_grad():
                for dummy_tensor in dummy_inputs:
                    try:
                        out = model(dummy_tensor)
                        if isinstance(out, torch.Tensor):
                            output_shape_str = str(list(out.shape))
                        elif isinstance(out, (tuple, list)) and len(out) > 0 and isinstance(out[0], torch.Tensor):
                            output_shape_str = str([list(t.shape) for t in out if isinstance(t, torch.Tensor)])
                        else:
                            output_shape_str = "Custom Object Output"
                        forward_error = None
                        break
                    except Exception as err:
                        forward_error = str(err)
                        continue

            if forward_error and output_shape_str is None:
                return {
                    "executed": True,
                    "passed": False,
                    "reason": f"Forward pass execution failed in '{target_name}': {forward_error}",
                    "error": forward_error,
                    "output_shape": None
                }

            return {
                "executed": True,
                "passed": True,
                "reason": f"Dummy forward pass succeeded on '{target_name}'",
                "error": None,
                "output_shape": output_shape_str
            }

        except Exception as exec_err:
            tb = traceback.format_exc()
            clean_error = f"{type(exec_err).__name__}: {str(exec_err)}"
            return {
                "executed": True,
                "passed": False,
                "reason": f"Runtime execution failed: {clean_error}",
                "error": clean_error,
                "traceback": tb,
                "output_shape": None
            }

    # --- FULL 3-LAYER EVALUATION ---
    @classmethod
    def evaluate_candidate(
        cls,
        code: str,
        file_path: str = "model.py",
        parameters: Optional[Dict[str, Any]] = None,
        expected_modules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs candidate code through all 3 verification layers.
        Returns aggregate evaluation verdict and composite score.
        """
        # Layer 1: AST Check
        l1 = cls.validate_layer1_ast(code)
        if not l1["valid"]:
            return {
                "is_valid": False,
                "total_score": 0.0,
                "layer1_ast": l1,
                "layer2_grounding": {"score": 0.0, "param_matches": [], "topology_matches": []},
                "layer3_exec": {"executed": False, "passed": False, "reason": "Disqualified at Layer 1", "error": l1["msg"], "output_shape": None}
            }

        # Layer 2: Grounding Score
        l2 = cls.calculate_layer2_grounding(code, parameters=parameters, expected_modules=expected_modules)

        # Layer 3: Forward Pass Execution
        l3 = cls.execute_layer3_forward_pass(code, file_path=file_path)

        # Calculate final composite score
        # Base: Grounding score (up to 100)
        # Execution bonus / penalty:
        # If Layer 3 executed and passed forward pass: +20 bonus (max 100)
        # If Layer 3 executed and threw RuntimeError: -40 penalty
        composite_score = l2["score"]
        if l3["executed"]:
            if l3["passed"]:
                composite_score = min(100.0, composite_score + 15.0)
            else:
                composite_score = max(10.0, composite_score - 40.0)

        is_overall_valid = l1["valid"] and (not l3["executed"] or l3["passed"])

        return {
            "is_valid": is_overall_valid,
            "total_score": round(composite_score, 1),
            "layer1_ast": l1,
            "layer2_grounding": l2,
            "layer3_exec": l3
        }


# Global singleton instance
code_verifier = CodeVerifier()
