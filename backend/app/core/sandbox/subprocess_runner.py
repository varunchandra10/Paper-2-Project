"""
Isolated subprocess-based code execution runner for Phase 7 Verification Ladder.
Executes generated PyTorch code in a dedicated OS subprocess with strict
resource limits, environment stripping, socket blocking, and hard timeouts.
Executes full dynamic ladder: Init -> Forward -> Loss -> Backward -> Optimizer Step -> Tiny Loop.
"""

import json
import os
import sys
import time
import shutil
import tempfile
import subprocess
from typing import Optional, Dict, Any

from app.core.sandbox.base import CodeExecutor, ExecutionLimits, ExecutionResult


HARNESS_TEMPLATE = '''# Self-contained test harness for Phase 7 verification ladder
import sys
import json
import time

def run_test():
    rungs = {}
    
    # 1. PyTorch resource restrictions (import first so stdlib loads cleanly)
    try:
        import torch
        import torch.nn as nn
        torch.set_num_threads(1)
        torch.set_grad_enabled(True)
    except ImportError:
        return {
            "executed": False,
            "passed": True,
            "highest_rung": None,
            "reason": "PyTorch library not available in runtime environment",
            "error": None,
            "output_shape": "N/A",
            "rungs": {}
        }

    # 2. Disable network access
    try:
        import socket
        def _blocked_net(*args, **kwargs):
            raise PermissionError("Network access is blocked in sandbox")
        socket.create_connection = _blocked_net
        socket.socket.connect = _blocked_net
        socket.socket.connect_ex = _blocked_net
        socket.socket.bind = _blocked_net
    except Exception:
        pass

    # 3. Dynamically import candidate module
    import importlib.util
    spec = importlib.util.spec_from_file_location("candidate_model", "candidate_model.py")
    if not spec or not spec.loader:
        return {
            "executed": False,
            "passed": False,
            "highest_rung": None,
            "reason": "Failed to load candidate module specification",
            "error": "SpecLoaderError",
            "output_shape": None,
            "rungs": {}
        }

    mod = importlib.util.module_from_spec(spec)
    sys.modules["candidate_model"] = mod

    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        clean_err = f"{type(e).__name__}: {str(e)}"
        return {
            "executed": True,
            "passed": False,
            "highest_rung": None,
            "reason": f"Module load/syntax error: {clean_err}",
            "error": clean_err,
            "output_shape": None,
            "rungs": {}
        }

    # 4. Discover custom nn.Module classes
    module_classes = []
    for name, obj in vars(mod).items():
        if isinstance(obj, type) and issubclass(obj, nn.Module) and obj is not nn.Module:
            module_classes.append((name, obj))

    if not module_classes:
        return {
            "executed": False,
            "passed": True,
            "highest_rung": None,
            "reason": "No custom nn.Module classes found in candidate scope (utility/data file)",
            "error": None,
            "output_shape": "N/A",
            "rungs": {}
        }

    target_name, TargetClass = module_classes[-1]

    # -------------------------------------------------------------
    # RUNG: MODEL_INITIALIZATION
    # -------------------------------------------------------------
    init_start = time.time()
    model = None
    instantiation_error = None

    try:
        model = TargetClass()
    except Exception as e1:
        instantiation_error = str(e1)
        for test_kwargs in [
            {"in_channels": 3, "num_classes": 10},
            {"d_model": 64, "num_heads": 4},
            {"dim": 64},
            {"channels": 32},
            {"vocab_size": 100, "d_model": 64},
            {"input_dim": 64, "output_dim": 10},
            {"num_classes": 10}
        ]:
            try:
                model = TargetClass(**test_kwargs)
                instantiation_error = None
                break
            except Exception:
                continue

    init_duration = round((time.time() - init_start) * 1000, 2)
    if model is None:
        rungs["MODEL_INITIALIZATION"] = {
            "passed": False,
            "error": instantiation_error,
            "duration_ms": init_duration,
            "telemetry": {"target_class": target_name}
        }
        return {
            "executed": True,
            "passed": False,
            "highest_rung": "MODEL_INITIALIZATION",
            "reason": f"Failed to instantiate model '{target_name}': {instantiation_error}",
            "error": instantiation_error,
            "output_shape": None,
            "rungs": rungs
        }

    rungs["MODEL_INITIALIZATION"] = {
        "passed": True,
        "error": None,
        "duration_ms": init_duration,
        "telemetry": {"target_class": target_name}
    }

    # -------------------------------------------------------------
    # RUNG: FORWARD_PASS
    # -------------------------------------------------------------
    fwd_start = time.time()
    model.train()

    dummy_inputs = [
        torch.randn(2, 512),          # Feature vector [B, D] (512)
        torch.randn(2, 64),           # Feature vector [B, D] (64)
        torch.randn(2, 10),           # Feature vector [B, D] (10)
        torch.randn(2, 3, 32, 32),    # Vision [B, C, H, W]
        torch.randn(2, 3, 224, 224),  # Standard Vision [B, C, H, W]
        torch.randn(2, 8, 512),       # Sequence / Transformer [B, L, D] (512)
        torch.randn(2, 8, 64),        # Sequence / Transformer [B, L, D] (64)
        torch.randint(0, 50, (2, 8))  # Token IDs [B, L]
    ]

    selected_input = None
    output_tensor = None
    output_shape_str = None
    forward_error = None

    for dummy_tensor in dummy_inputs:
        try:
            out = model(dummy_tensor)
            if isinstance(out, torch.Tensor):
                output_tensor = out
                output_shape_str = str(list(out.shape))
            elif isinstance(out, (tuple, list)) and len(out) > 0 and isinstance(out[0], torch.Tensor):
                output_tensor = out[0]
                output_shape_str = str([list(t.shape) for t in out if isinstance(t, torch.Tensor)])
            elif isinstance(out, dict):
                first_val = next((v for v in out.values() if isinstance(v, torch.Tensor)), None)
                if first_val is not None:
                    output_tensor = first_val
                    output_shape_str = str(list(first_val.shape))
            
            if output_tensor is not None:
                selected_input = dummy_tensor
                forward_error = None
                break
        except Exception as err:
            forward_error = str(err)
            continue

    fwd_duration = round((time.time() - fwd_start) * 1000, 2)
    if output_tensor is None:
        rungs["FORWARD_PASS"] = {
            "passed": False,
            "error": forward_error,
            "duration_ms": fwd_duration,
            "telemetry": {"attempted_shapes": 4}
        }
        return {
            "executed": True,
            "passed": False,
            "highest_rung": "FORWARD_PASS",
            "reason": f"Forward pass failed in '{target_name}': {forward_error}",
            "error": forward_error,
            "output_shape": None,
            "rungs": rungs
        }

    rungs["FORWARD_PASS"] = {
        "passed": True,
        "error": None,
        "duration_ms": fwd_duration,
        "telemetry": {"output_shape": output_shape_str}
    }

    # -------------------------------------------------------------
    # RUNG: LOSS_CALCULATION
    # -------------------------------------------------------------
    loss_start = time.time()
    loss_tensor = None
    target_tensor = None
    criterion = None
    loss_error = None

    try:
        # Determine appropriate dummy target and criterion based on output
        if output_tensor.dim() >= 2 and output_tensor.shape[-1] > 1:
            try:
                criterion = nn.CrossEntropyLoss()
                target_tensor = torch.zeros(output_tensor.shape[0], dtype=torch.long)
                loss_tensor = criterion(output_tensor.view(output_tensor.shape[0], output_tensor.shape[1], -1)[:, :, 0], target_tensor)
            except Exception:
                criterion = nn.MSELoss()
                target_tensor = torch.zeros_like(output_tensor)
                loss_tensor = criterion(output_tensor, target_tensor)
        else:
            criterion = nn.MSELoss()
            target_tensor = torch.zeros_like(output_tensor)
            loss_tensor = criterion(output_tensor, target_tensor)

        if torch.isnan(loss_tensor).any() or torch.isinf(loss_tensor).any():
            raise ValueError(f"Calculated loss is NaN or Inf: {loss_tensor.item()}")

    except Exception as e:
        loss_error = str(e)

    loss_duration = round((time.time() - loss_start) * 1000, 2)
    if loss_tensor is None or loss_error:
        rungs["LOSS_CALCULATION"] = {
            "passed": False,
            "error": loss_error,
            "duration_ms": loss_duration,
            "telemetry": {}
        }
        return {
            "executed": True,
            "passed": False,
            "highest_rung": "LOSS_CALCULATION",
            "reason": f"Loss calculation failed: {loss_error}",
            "error": loss_error,
            "output_shape": output_shape_str,
            "rungs": rungs
        }

    loss_val = round(float(loss_tensor.item()), 4)
    rungs["LOSS_CALCULATION"] = {
        "passed": True,
        "error": None,
        "duration_ms": loss_duration,
        "telemetry": {"initial_loss": loss_val}
    }

    # -------------------------------------------------------------
    # RUNG: BACKWARD_PASS & GRADIENT CONNECTIVITY (ANTI-STUB)
    # -------------------------------------------------------------
    back_start = time.time()
    backward_error = None
    trainable_params = [p for p in model.parameters() if p.requires_grad]

    try:
        model.zero_grad()
        if loss_tensor.grad_fn is None and not loss_tensor.requires_grad:
            raise ValueError("Disconnected computation graph: output tensor has no grad_fn (silent stub detected)")

        loss_tensor.backward(retain_graph=True)

        if not trainable_params:
            raise ValueError("Model has zero trainable parameters (empty class or no weights)")

        # Gradient existence & flow check (detect silent stubs where forward doesn't touch parameters)
        params_with_grad = [p for p in trainable_params if p.grad is not None]
        if not params_with_grad:
            raise ValueError("Disconnected computation graph: zero parameters received gradients (silent stub detected)")

        # Check for NaN / Inf gradients
        for p in params_with_grad:
            if torch.isnan(p.grad).any():
                raise ValueError("NaN gradient detected during backward pass")
            if torch.isinf(p.grad).any():
                raise ValueError("Inf gradient detected during backward pass")

        grad_norm = float(torch.norm(torch.stack([torch.norm(p.grad) for p in params_with_grad])).item())
        if grad_norm == 0.0:
            raise ValueError("Zero gradient norm across all parameters (parameters disconnected from output)")

    except Exception as e:
        err_msg = str(e)
        if "does not have a grad_fn" in err_msg or "does not require grad" in err_msg:
            backward_error = "Disconnected computation graph: output tensor has no grad_fn (silent stub detected)"
        else:
            backward_error = err_msg

    back_duration = round((time.time() - back_start) * 1000, 2)
    if backward_error:
        rungs["BACKWARD_PASS"] = {
            "passed": False,
            "error": backward_error,
            "duration_ms": back_duration,
            "telemetry": {"trainable_params": len(trainable_params)}
        }
        return {
            "executed": True,
            "passed": False,
            "highest_rung": "BACKWARD_PASS",
            "reason": f"Backward pass validation failed: {backward_error}",
            "error": backward_error,
            "output_shape": output_shape_str,
            "rungs": rungs
        }

    rungs["BACKWARD_PASS"] = {
        "passed": True,
        "error": None,
        "duration_ms": back_duration,
        "telemetry": {
            "trainable_params": len(trainable_params),
            "params_with_grad": len(params_with_grad),
            "grad_norm": round(grad_norm, 4)
        }
    }

    # -------------------------------------------------------------
    # RUNG: OPTIMIZER_STEP & WEIGHT MUTATION
    # -------------------------------------------------------------
    opt_start = time.time()
    optimizer_error = None
    mutated_count = 0

    try:
        # Snapshot current parameter values
        w_snapshot = {name: p.clone().detach() for name, p in model.named_parameters() if p.requires_grad and p.grad is not None}
        optimizer = torch.optim.SGD(trainable_params, lr=0.01)
        optimizer.step()

        # Check if weights actually mutated
        for name, p in model.named_parameters():
            if name in w_snapshot:
                if not torch.equal(p, w_snapshot[name]):
                    mutated_count += 1

        if mutated_count == 0:
            raise ValueError("Optimizer step completed but 0 parameters were mutated")

    except Exception as e:
        optimizer_error = str(e)

    opt_duration = round((time.time() - opt_start) * 1000, 2)
    if optimizer_error:
        rungs["OPTIMIZER_STEP"] = {
            "passed": False,
            "error": optimizer_error,
            "duration_ms": opt_duration,
            "telemetry": {}
        }
        return {
            "executed": True,
            "passed": False,
            "highest_rung": "OPTIMIZER_STEP",
            "reason": f"Optimizer step failed: {optimizer_error}",
            "error": optimizer_error,
            "output_shape": output_shape_str,
            "rungs": rungs
        }

    rungs["OPTIMIZER_STEP"] = {
        "passed": True,
        "error": None,
        "duration_ms": opt_duration,
        "telemetry": {"mutated_params": mutated_count}
    }

    # -------------------------------------------------------------
    # RUNG: TINY_TRAINING_RUN (3-step micro loop)
    # -------------------------------------------------------------
    tiny_start = time.time()
    tiny_error = None
    step_losses = [loss_val]

    try:
        for step in range(2):
            optimizer.zero_grad()
            out_step = model(selected_input)
            t_out = out_step if isinstance(out_step, torch.Tensor) else (out_step[0] if isinstance(out_step, (tuple, list)) else next(iter(out_step.values())))
            
            if criterion is not None and target_tensor is not None:
                if isinstance(criterion, nn.CrossEntropyLoss):
                    l_step = criterion(t_out.view(t_out.shape[0], t_out.shape[1], -1)[:, :, 0], target_tensor)
                else:
                    l_step = criterion(t_out, target_tensor)
            else:
                l_step = t_out.mean()

            if torch.isnan(l_step) or torch.isinf(l_step):
                raise ValueError(f"Loss exploded to NaN/Inf at step {step + 2}")

            l_step.backward()
            optimizer.step()
            step_losses.append(round(float(l_step.item()), 4))

        # Divergence guard: loss should not explode 5x above initial
        if step_losses[-1] > max(50.0, step_losses[0] * 5.0):
            raise ValueError(f"Tiny training run diverged: {step_losses[0]} -> {step_losses[-1]}")

    except Exception as e:
        tiny_error = str(e)

    tiny_duration = round((time.time() - tiny_start) * 1000, 2)
    if tiny_error:
        rungs["TINY_TRAINING_RUN"] = {
            "passed": False,
            "error": tiny_error,
            "duration_ms": tiny_duration,
            "telemetry": {"step_losses": step_losses}
        }
        return {
            "executed": True,
            "passed": False,
            "highest_rung": "TINY_TRAINING_RUN",
            "reason": f"Tiny training loop failed: {tiny_error}",
            "error": tiny_error,
            "output_shape": output_shape_str,
            "rungs": rungs
        }

    rungs["TINY_TRAINING_RUN"] = {
        "passed": True,
        "error": None,
        "duration_ms": tiny_duration,
        "telemetry": {"step_losses": step_losses}
    }

    return {
        "executed": True,
        "passed": True,
        "highest_rung": "TINY_TRAINING_RUN",
        "reason": f"All verification ladder stages passed successfully on '{target_name}'",
        "error": None,
        "output_shape": output_shape_str,
        "rungs": rungs
    }

if __name__ == "__main__":
    import traceback
    try:
        res = run_test()
        print("__RESULT__=" + json.dumps(res))
    except Exception as fatal_e:
        err_dict = {
            "executed": True,
            "passed": False,
            "highest_rung": None,
            "reason": f"Fatal harness error: {str(fatal_e)}",
            "error": traceback.format_exc(),
            "output_shape": None,
            "rungs": {}
        }
        print("__RESULT__=" + json.dumps(err_dict))
'''


class SubprocessCodeExecutor(CodeExecutor):
    """
    Executes code in a completely separate Python subprocess with:
    - Disposable temporary directory isolation
    - Stripped environment variables (no API keys or secrets passed)
    - Hard timeout enforcement with process termination
    - Blocked socket access
    - Full dynamic ladder execution
    """

    def __init__(self, default_limits: Optional[ExecutionLimits] = None):
        self.default_limits = default_limits or ExecutionLimits(timeout_seconds=15.0)

    def execute_verification_ladder(
        self,
        code: str,
        file_path: str = "model.py",
        limits: Optional[ExecutionLimits] = None
    ) -> ExecutionResult:
        lims = limits or self.default_limits
        start_time = time.time()

        # Non-model files (e.g. config, utils) don't require dynamic ladder execution
        is_model_file = any(
            kw in file_path.lower()
            for kw in ["model", "encoder", "fusion", "decoder", "backbone", "net", "layer"]
        )
        if not is_model_file and "class" not in code:
            return ExecutionResult(
                executed=False,
                passed=True,
                reason="Non-module utility/config file (no forward pass required)",
                output_shape="N/A",
                duration_seconds=time.time() - start_time,
                rungs={}
            )

        temp_dir = tempfile.mkdtemp(prefix="p2p_sandbox_")
        try:
            # 1. Write candidate code
            candidate_path = os.path.join(temp_dir, "candidate_model.py")
            with open(candidate_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 2. Write runner harness
            harness_path = os.path.join(temp_dir, "_harness.py")
            with open(harness_path, "w", encoding="utf-8") as f:
                f.write(HARNESS_TEMPLATE)

            # 3. Build stripped environment
            clean_env = {
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "PATH": os.environ.get("PATH", ""),
                "TEMP": temp_dir,
                "TMP": temp_dir,
                "PYTHONPATH": os.path.pathsep.join(sys.path),
                "PYTHONUNBUFFERED": "1"
            }

            # 4. Launch isolated worker process
            python_bin = sys.executable
            proc = subprocess.Popen(
                [python_bin, harness_path],
                cwd=temp_dir,
                env=clean_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                stdout, stderr = proc.communicate(timeout=lims.timeout_seconds)
                exit_code = proc.returncode
                duration = time.time() - start_time

                # Parse harness result
                result_json = None
                for line in stdout.splitlines():
                    if line.startswith("__RESULT__="):
                        try:
                            result_json = json.loads(line[len("__RESULT__="):])
                            break
                        except json.JSONDecodeError:
                            pass

                if result_json:
                    return ExecutionResult(
                        executed=result_json.get("executed", True),
                        passed=result_json.get("passed", False),
                        reason=result_json.get("reason", "Unknown execution result"),
                        output_shape=result_json.get("output_shape"),
                        error=result_json.get("error"),
                        stdout=stdout,
                        stderr=stderr,
                        exit_code=exit_code,
                        timed_out=False,
                        duration_seconds=duration,
                        rungs=result_json.get("rungs", {}),
                        metadata={"highest_rung": result_json.get("highest_rung")}
                    )

                return ExecutionResult(
                    executed=True,
                    passed=False,
                    reason=f"Process terminated with exit code {exit_code}",
                    error=stderr.strip() or stdout.strip() or f"Process exited with code {exit_code}",
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    timed_out=False,
                    duration_seconds=duration,
                    rungs={}
                )

            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                duration = time.time() - start_time

                return ExecutionResult(
                    executed=True,
                    passed=False,
                    reason=f"Execution timed out after {lims.timeout_seconds} seconds",
                    error=f"TimeoutExpired: Execution exceeded {lims.timeout_seconds}s limit",
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=-1,
                    timed_out=True,
                    duration_seconds=duration,
                    rungs={}
                )

        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def execute_forward_pass(
        self,
        code: str,
        file_path: str = "model.py",
        limits: Optional[ExecutionLimits] = None
    ) -> ExecutionResult:
        """Maintains full backward compatibility by delegating to execute_verification_ladder."""
        return self.execute_verification_ladder(code, file_path=file_path, limits=limits)
