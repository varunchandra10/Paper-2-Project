"""
Execution abstraction and data models for isolated code execution environments.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ExecutionLimits:
    """Resource constraints imposed on code execution."""
    timeout_seconds: float = 5.0
    max_memory_mb: int = 512
    cpu_threads: int = 1
    allow_network: bool = False
    allow_filesystem_write: bool = False


@dataclass
class ExecutionResult:
    """Standardized result returned by any code execution backend."""
    executed: bool
    passed: bool
    reason: str
    output_shape: Optional[str] = None
    error: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    timed_out: bool = False
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    rungs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "executed": self.executed,
            "passed": self.passed,
            "reason": self.reason,
            "error": self.error,
            "output_shape": self.output_shape,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "duration_seconds": round(self.duration_seconds, 3),
            "metadata": self.metadata,
            "rungs": self.rungs
        }


class CodeExecutor(ABC):
    """Abstract base class for all code execution backends."""

    @abstractmethod
    def execute_forward_pass(
        self,
        code: str,
        file_path: str = "model.py",
        limits: Optional[ExecutionLimits] = None
    ) -> ExecutionResult:
        """
        Executes code in an isolated environment to verify module instantiation
        and dummy tensor forward pass without risking host process integrity.
        """
        pass

    def execute_verification_ladder(
        self,
        code: str,
        file_path: str = "model.py",
        limits: Optional[ExecutionLimits] = None
    ) -> ExecutionResult:
        """
        Executes the full runtime verification ladder:
        Initialization -> Forward Pass -> Loss -> Backward Pass -> Optimizer Step -> Tiny Loop.
        Defaults to execute_forward_pass if not overridden.
        """
        return self.execute_forward_pass(code, file_path=file_path, limits=limits)
