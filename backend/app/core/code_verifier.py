"""
3-Layer & 12-Rung Paper-Grounded PyTorch Code Verification Pipeline.
Orchestrates static AST, security analysis, bytecode compilation,
dynamic sandbox ladder execution, and paper fidelity evaluation.
"""

import ast
import re
import sys
import time
import traceback
from typing import Dict, Any, List, Optional, Tuple

from app.schemas.verification import (
    CodeLifecycleState,
    VerificationRung,
    RungResult,
    CodeVerificationReport,
)


class CodeVerifier:
    """
    Comprehensive Code Verification Ladder for Ruexis AI:
    - Rungs 1-4: Static Gates (AST, Security, Imports, Bytecode Compilation)
    - Rungs 5-11: Dynamic Gates (Init, Forward, Loss, Backward, Optimizer, Tiny Loop)
    - Rung 12: Functional & Paper Invariant Evaluation
    """

    # --- STATIC GATES ---
    @staticmethod
    def validate_layer1_ast(code: str) -> Dict[str, Any]:
        """Validates Python grammar and disqualifies hollow stubs."""
        if not code or not code.strip():
            return {"valid": False, "msg": "Empty code block", "is_stub": True}

        # Check for banned stub patterns
        stub_patterns = [
            r'#\s*grounding:\s*fallback',
            r'#\s*synthesized module for',
            r'pass\s*#\s*placeholder',
            r'def\s+[a-zA-Z0-9_]+\s*\([^)]*\):\s*pass\s*$',
            r'raise\s+NotImplementedError\b'
        ]
        for pat in stub_patterns:
            if re.search(pat, code, re.IGNORECASE):
                return {
                    "valid": False,
                    "msg": "Code rejected: Hollow fallback/NotImplemented stub detected",
                    "is_stub": True
                }

        try:
            tree = ast.parse(code.strip())

            # Check for banned security primitives
            safety = CodeVerifier.check_banned_primitives(tree)
            if not safety["safe"]:
                return {
                    "valid": False,
                    "msg": f"Security violation: {safety['reason']}",
                    "is_stub": False,
                    "security_violation": True,
                    "ast_tree": tree,
                    "safety": safety
                }

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
        """Detects unsafe or banned primitives in AST using SecurityPolicy."""
        from app.core.sandbox.policies import SecurityPolicy
        return SecurityPolicy.analyze(tree)

    @staticmethod
    def validate_bytecode_compilation(code: str, file_path: str = "model.py") -> Dict[str, Any]:
        """Compiles code into Python bytecode using compile() built-in."""
        try:
            compile(code.strip(), file_path, "exec")
            return {"valid": True, "msg": "Bytecode compilation succeeded"}
        except SyntaxError as e:
            return {"valid": False, "msg": f"Bytecode compile SyntaxError (line {e.lineno}): {e.msg}"}
        except Exception as e:
            return {"valid": False, "msg": f"Bytecode compilation failed: {str(e)}"}

    @staticmethod
    def validate_imports(tree: ast.AST) -> Dict[str, Any]:
        """Scans module imports to verify clean import declarations."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return {"valid": True, "imports": imports, "count": len(imports)}

    # --- PAPER GROUNDING & ALIGNMENT SCORE ---
    @staticmethod
    def calculate_layer2_grounding(
        code: str,
        parameters: Optional[Dict[str, Any]] = None,
        expected_modules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates adherence to extracted paper hyperparameters and architectural specifications.
        Returns grounding score between 0.0 and 100.0.
        """
        param_score = 0.0
        param_matches = []
        param_misses = []

        # 1. Hyperparameter Fidelity (50 points max)
        if parameters and isinstance(parameters, dict):
            verifiable_params = {}
            for k, v in parameters.items():
                val_str = str(v).strip()
                if val_str and val_str.lower() not in ["none", "null", "not specified", "unknown"]:
                    verifiable_params[k] = val_str

            total_params = len(verifiable_params)
            if total_params > 0:
                matched_count = 0
                for k, val_str in verifiable_params.items():
                    if re.search(rf'\b{re.escape(val_str)}\b', code) or re.search(rf'\b{re.escape(k)}\b', code, re.IGNORECASE):
                        matched_count += 1
                        param_matches.append(f"{k}={val_str}")
                    else:
                        param_misses.append(f"{k}={val_str}")
                param_score = (matched_count / total_params) * 50.0
            else:
                param_score = 40.0
        else:
            param_score = 35.0

        # 2. Architecture & Topology Fidelity (50 points max)
        arch_score = 0.0
        topology_matches = []

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

    # Isolated sandbox executor instance
    _executor = None

    @classmethod
    def get_executor(cls):
        if cls._executor is None:
            from app.core.sandbox.subprocess_runner import SubprocessCodeExecutor
            cls._executor = SubprocessCodeExecutor()
        return cls._executor

    @classmethod
    def set_executor(cls, executor):
        cls._executor = executor

    # --- DYNAMIC FORWARD PASS EXECUTION (BACKWARD COMPATIBLE) ---
    @classmethod
    def execute_layer3_forward_pass(
        cls,
        code: str,
        file_path: str = "model.py",
        limits: Optional[Any] = None
    ) -> Dict[str, Any]:
        executor = cls.get_executor()
        result = executor.execute_verification_ladder(code, file_path=file_path, limits=limits)
        return result.to_dict()

    # --- FULL 12-RUNG CODE VERIFICATION LADDER ---
    @classmethod
    def verify_code_ladder(
        cls,
        code: str,
        file_path: str = "model.py",
        parameters: Optional[Dict[str, Any]] = None,
        expected_modules: Optional[List[str]] = None,
        candidate_id: str = "candidate_model"
    ) -> CodeVerificationReport:
        """
        Executes the full 12-rung verification ladder and produces an independent,
        machine-readable CodeVerificationReport.
        """
        rungs_log: List[RungResult] = []
        highest_rung: Optional[VerificationRung] = None

        # ---------------------------------------------------------
        # RUNG 1: AST_VALIDATION
        # ---------------------------------------------------------
        t0 = time.time()
        l1 = cls.validate_layer1_ast(code)
        d_ast = round((time.time() - t0) * 1000, 2)
        if not l1["valid"]:
            if l1.get("security_violation"):
                rungs_log.append(RungResult(
                    rung=VerificationRung.AST_VALIDATION,
                    passed=True,
                    duration_ms=d_ast,
                    telemetry={"msg": "Syntax valid"}
                ))
                rungs_log.append(RungResult(
                    rung=VerificationRung.SECURITY_ANALYSIS,
                    passed=False,
                    duration_ms=0.5,
                    error=l1["msg"],
                    telemetry={"violations": l1.get("safety", {}).get("violations", [])}
                ))
                return CodeVerificationReport(
                    candidate_id=candidate_id,
                    file_path=file_path,
                    lifecycle_state=CodeLifecycleState.FAILED,
                    highest_rung_reached=VerificationRung.AST_VALIDATION,
                    all_rungs_passed=False,
                    rungs=rungs_log,
                    repair_feedback=f"Security analysis rejected code: {l1['msg']}"
                )

            rungs_log.append(RungResult(
                rung=VerificationRung.AST_VALIDATION,
                passed=False,
                duration_ms=d_ast,
                error=l1["msg"],
                telemetry={"is_stub": l1.get("is_stub", False)}
            ))
            return CodeVerificationReport(
                candidate_id=candidate_id,
                file_path=file_path,
                lifecycle_state=CodeLifecycleState.FAILED,
                highest_rung_reached=VerificationRung.AST_VALIDATION,
                all_rungs_passed=False,
                rungs=rungs_log,
                repair_feedback=f"AST Validation failed: {l1['msg']}"
            )

        rungs_log.append(RungResult(
            rung=VerificationRung.AST_VALIDATION,
            passed=True,
            duration_ms=d_ast,
            telemetry={"msg": "Syntax valid"}
        ))
        highest_rung = VerificationRung.AST_VALIDATION
        ast_tree = l1["ast_tree"]

        # ---------------------------------------------------------
        # RUNG 2: SECURITY_ANALYSIS
        # ---------------------------------------------------------
        t0 = time.time()
        safety = cls.check_banned_primitives(ast_tree)
        d_sec = round((time.time() - t0) * 1000, 2)
        if not safety["safe"]:
            rungs_log.append(RungResult(
                rung=VerificationRung.SECURITY_ANALYSIS,
                passed=False,
                duration_ms=d_sec,
                error=safety["reason"],
                telemetry={"violations": safety.get("violations", [])}
            ))
            return CodeVerificationReport(
                candidate_id=candidate_id,
                file_path=file_path,
                lifecycle_state=CodeLifecycleState.FAILED,
                highest_rung_reached=highest_rung,
                all_rungs_passed=False,
                rungs=rungs_log,
                repair_feedback=f"Security analysis rejected code: {safety['reason']}"
            )

        rungs_log.append(RungResult(
            rung=VerificationRung.SECURITY_ANALYSIS,
            passed=True,
            duration_ms=d_sec,
            telemetry={"violations_count": 0}
        ))
        highest_rung = VerificationRung.SECURITY_ANALYSIS

        # ---------------------------------------------------------
        # RUNG 3: IMPORT_VALIDATION
        # ---------------------------------------------------------
        t0 = time.time()
        imp_res = cls.validate_imports(ast_tree)
        d_imp = round((time.time() - t0) * 1000, 2)
        rungs_log.append(RungResult(
            rung=VerificationRung.IMPORT_VALIDATION,
            passed=True,
            duration_ms=d_imp,
            telemetry={"imports_scanned": imp_res["count"]}
        ))
        highest_rung = VerificationRung.IMPORT_VALIDATION

        # ---------------------------------------------------------
        # RUNG 4: BYTECODE_COMPILATION
        # ---------------------------------------------------------
        t0 = time.time()
        comp_res = cls.validate_bytecode_compilation(code, file_path)
        d_comp = round((time.time() - t0) * 1000, 2)
        if not comp_res["valid"]:
            rungs_log.append(RungResult(
                rung=VerificationRung.BYTECODE_COMPILATION,
                passed=False,
                duration_ms=d_comp,
                error=comp_res["msg"]
            ))
            return CodeVerificationReport(
                candidate_id=candidate_id,
                file_path=file_path,
                lifecycle_state=CodeLifecycleState.FAILED,
                highest_rung_reached=highest_rung,
                all_rungs_passed=False,
                rungs=rungs_log,
                repair_feedback=f"Bytecode compilation failed: {comp_res['msg']}"
            )

        rungs_log.append(RungResult(
            rung=VerificationRung.BYTECODE_COMPILATION,
            passed=True,
            duration_ms=d_comp,
            telemetry={"msg": comp_res["msg"]}
        ))
        highest_rung = VerificationRung.BYTECODE_COMPILATION

        # Static gates passed -> Current status: VALIDATED
        current_lifecycle = CodeLifecycleState.VALIDATED

        # ---------------------------------------------------------
        # DYNAMIC GATES (Rungs 5-11 executed in isolated sandbox)
        # ---------------------------------------------------------
        executor = cls.get_executor()
        exec_res = executor.execute_verification_ladder(code, file_path=file_path)
        sandbox_rungs = exec_res.rungs or {}

        # If file is a non-module utility or PyTorch is not needed
        if not exec_res.executed and exec_res.passed:
            grounding = cls.calculate_layer2_grounding(code, parameters=parameters, expected_modules=expected_modules)
            return CodeVerificationReport(
                candidate_id=candidate_id,
                file_path=file_path,
                lifecycle_state=CodeLifecycleState.VERIFIED,
                highest_rung_reached=highest_rung,
                all_rungs_passed=True,
                rungs=rungs_log,
                paper_fidelity_score=grounding["score"],
                fidelity_breakdown=grounding
            )

        # Dynamic Rung: MODEL_INITIALIZATION
        init_rung = sandbox_rungs.get("MODEL_INITIALIZATION")
        if init_rung:
            rungs_log.append(RungResult(
                rung=VerificationRung.MODEL_INITIALIZATION,
                passed=init_rung["passed"],
                duration_ms=init_rung.get("duration_ms", 0.0),
                error=init_rung.get("error"),
                telemetry=init_rung.get("telemetry", {})
            ))
            if not init_rung["passed"]:
                return CodeVerificationReport(
                    candidate_id=candidate_id,
                    file_path=file_path,
                    lifecycle_state=CodeLifecycleState.FAILED,
                    highest_rung_reached=highest_rung,
                    all_rungs_passed=False,
                    rungs=rungs_log,
                    repair_feedback=f"Model initialization failed: {init_rung.get('error')}"
                )
            highest_rung = VerificationRung.MODEL_INITIALIZATION

        # Dynamic Rung: FORWARD_PASS
        fwd_rung = sandbox_rungs.get("FORWARD_PASS")
        if fwd_rung:
            rungs_log.append(RungResult(
                rung=VerificationRung.FORWARD_PASS,
                passed=fwd_rung["passed"],
                duration_ms=fwd_rung.get("duration_ms", 0.0),
                error=fwd_rung.get("error"),
                telemetry=fwd_rung.get("telemetry", {})
            ))
            if not fwd_rung["passed"]:
                return CodeVerificationReport(
                    candidate_id=candidate_id,
                    file_path=file_path,
                    lifecycle_state=CodeLifecycleState.FAILED,
                    highest_rung_reached=highest_rung,
                    all_rungs_passed=False,
                    rungs=rungs_log,
                    repair_feedback=f"Forward pass failed (tensor shape mismatch): {fwd_rung.get('error')}"
                )
            highest_rung = VerificationRung.FORWARD_PASS
            current_lifecycle = CodeLifecycleState.EXECUTABLE

        # Dynamic Rung: LOSS_CALCULATION
        loss_rung = sandbox_rungs.get("LOSS_CALCULATION")
        if loss_rung:
            rungs_log.append(RungResult(
                rung=VerificationRung.LOSS_CALCULATION,
                passed=loss_rung["passed"],
                duration_ms=loss_rung.get("duration_ms", 0.0),
                error=loss_rung.get("error"),
                telemetry=loss_rung.get("telemetry", {})
            ))
            if not loss_rung["passed"]:
                return CodeVerificationReport(
                    candidate_id=candidate_id,
                    file_path=file_path,
                    lifecycle_state=CodeLifecycleState.FAILED,
                    highest_rung_reached=highest_rung,
                    all_rungs_passed=False,
                    rungs=rungs_log,
                    repair_feedback=f"Loss calculation error: {loss_rung.get('error')}"
                )
            highest_rung = VerificationRung.LOSS_CALCULATION

        # Dynamic Rung: BACKWARD_PASS (Gradient flow / Anti-stub)
        back_rung = sandbox_rungs.get("BACKWARD_PASS")
        if back_rung:
            rungs_log.append(RungResult(
                rung=VerificationRung.BACKWARD_PASS,
                passed=back_rung["passed"],
                duration_ms=back_rung.get("duration_ms", 0.0),
                error=back_rung.get("error"),
                telemetry=back_rung.get("telemetry", {})
            ))
            if not back_rung["passed"]:
                return CodeVerificationReport(
                    candidate_id=candidate_id,
                    file_path=file_path,
                    lifecycle_state=CodeLifecycleState.FAILED,
                    highest_rung_reached=highest_rung,
                    all_rungs_passed=False,
                    rungs=rungs_log,
                    repair_feedback=f"Backward pass gradient failure: {back_rung.get('error')}"
                )
            highest_rung = VerificationRung.BACKWARD_PASS

        # Dynamic Rung: OPTIMIZER_STEP (Weight mutation)
        opt_rung = sandbox_rungs.get("OPTIMIZER_STEP")
        if opt_rung:
            rungs_log.append(RungResult(
                rung=VerificationRung.OPTIMIZER_STEP,
                passed=opt_rung["passed"],
                duration_ms=opt_rung.get("duration_ms", 0.0),
                error=opt_rung.get("error"),
                telemetry=opt_rung.get("telemetry", {})
            ))
            if not opt_rung["passed"]:
                return CodeVerificationReport(
                    candidate_id=candidate_id,
                    file_path=file_path,
                    lifecycle_state=CodeLifecycleState.FAILED,
                    highest_rung_reached=highest_rung,
                    all_rungs_passed=False,
                    rungs=rungs_log,
                    repair_feedback=f"Optimizer step failure: {opt_rung.get('error')}"
                )
            highest_rung = VerificationRung.OPTIMIZER_STEP

        # Dynamic Rung: TINY_TRAINING_RUN
        tiny_rung = sandbox_rungs.get("TINY_TRAINING_RUN")
        if tiny_rung:
            rungs_log.append(RungResult(
                rung=VerificationRung.TINY_TRAINING_RUN,
                passed=tiny_rung["passed"],
                duration_ms=tiny_rung.get("duration_ms", 0.0),
                error=tiny_rung.get("error"),
                telemetry=tiny_rung.get("telemetry", {})
            ))
            if not tiny_rung["passed"]:
                return CodeVerificationReport(
                    candidate_id=candidate_id,
                    file_path=file_path,
                    lifecycle_state=CodeLifecycleState.FAILED,
                    highest_rung_reached=highest_rung,
                    all_rungs_passed=False,
                    rungs=rungs_log,
                    repair_feedback=f"Tiny training loop failure: {tiny_rung.get('error')}"
                )
            highest_rung = VerificationRung.TINY_TRAINING_RUN
            current_lifecycle = CodeLifecycleState.VERIFIED

        # General execution failure check (e.g. timeout or fatal crash)
        if not exec_res.passed:
            return CodeVerificationReport(
                candidate_id=candidate_id,
                file_path=file_path,
                lifecycle_state=CodeLifecycleState.FAILED,
                highest_rung_reached=highest_rung,
                all_rungs_passed=False,
                rungs=rungs_log,
                repair_feedback=f"Execution failed: {exec_res.error or exec_res.reason}"
            )

        # ---------------------------------------------------------
        # RUNG 12: FUNCTIONAL_EVALUATION & PAPER FIDELITY
        # ---------------------------------------------------------
        grounding = cls.calculate_layer2_grounding(code, parameters=parameters, expected_modules=expected_modules)
        fidelity_score = grounding["score"]

        # Functional invariant check: output shape must be non-empty and tensor-like
        func_passed = bool(exec_res.output_shape and exec_res.output_shape != "N/A")
        rungs_log.append(RungResult(
            rung=VerificationRung.FUNCTIONAL_EVALUATION,
            passed=func_passed,
            duration_ms=1.0,
            telemetry={"output_shape": exec_res.output_shape, "fidelity_score": fidelity_score}
        ))
        if func_passed:
            highest_rung = VerificationRung.FUNCTIONAL_EVALUATION

        # Status determination: if fidelity is very low (< 35) or missing critical topology, mark NEEDS_REVIEW
        if current_lifecycle == CodeLifecycleState.VERIFIED and fidelity_score < 35.0:
            current_lifecycle = CodeLifecycleState.NEEDS_REVIEW

        return CodeVerificationReport(
            candidate_id=candidate_id,
            file_path=file_path,
            lifecycle_state=current_lifecycle,
            highest_rung_reached=highest_rung,
            all_rungs_passed=(current_lifecycle == CodeLifecycleState.VERIFIED),
            rungs=rungs_log,
            paper_fidelity_score=fidelity_score,
            fidelity_breakdown=grounding
        )

    # --- BACKWARD COMPATIBLE EVALUATE CANDIDATE ---
    @classmethod
    def evaluate_candidate(
        cls,
        code: str,
        file_path: str = "model.py",
        parameters: Optional[Dict[str, Any]] = None,
        expected_modules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Runs candidate through ladder and returns backward-compatible dict."""
        report = cls.verify_code_ladder(
            code=code,
            file_path=file_path,
            parameters=parameters,
            expected_modules=expected_modules
        )

        l1_result = {
            "valid": report.get_rung_result(VerificationRung.AST_VALIDATION).passed if report.get_rung_result(VerificationRung.AST_VALIDATION) else False,
            "msg": report.repair_feedback or "Syntax OK",
            "is_stub": False
        }

        l2_result = report.fidelity_breakdown or {"score": report.paper_fidelity_score}

        fwd_rung = report.get_rung_result(VerificationRung.FORWARD_PASS)
        fwd_passed = fwd_rung.passed if fwd_rung else False
        exec_reason = "Verification ladder passed" if report.all_rungs_passed else (report.repair_feedback or "Forward pass failed")
        if not fwd_passed and "Forward pass failed" not in exec_reason and "Runtime execution failed" not in exec_reason:
            exec_reason = f"Forward pass failed: {exec_reason}"

        l3_result = {
            "executed": fwd_rung is not None,
            "passed": fwd_passed,
            "reason": exec_reason,
            "error": None if report.all_rungs_passed else report.repair_feedback,
            "output_shape": fwd_rung.telemetry.get("output_shape") if fwd_rung else None
        }

        composite_score = report.paper_fidelity_score
        if report.lifecycle_state in [CodeLifecycleState.VERIFIED, CodeLifecycleState.EXECUTABLE]:
            composite_score = min(100.0, composite_score + 15.0)
        else:
            composite_score = max(0.0, composite_score - 40.0)

        return {
            "is_valid": report.lifecycle_state in [CodeLifecycleState.VERIFIED, CodeLifecycleState.EXECUTABLE],
            "total_score": round(composite_score, 1),
            "layer1_ast": l1_result,
            "layer2_grounding": l2_result,
            "layer3_exec": l3_result,
            "verification_report": report.model_dump(),
            "lifecycle_state": report.lifecycle_state.value
        }


# Global singleton instance
code_verifier = CodeVerifier()
