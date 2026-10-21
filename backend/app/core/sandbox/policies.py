"""
Security policies and AST visitors for vetting generated code prior to execution.
"""

import ast
from typing import Dict, Any, Set, List


class SecurityPolicy:
    """
    AST-level static security scanner designed to detect malicious constructs,
    unauthorized system calls, secret exfiltration vectors, and unsafe imports.
    """

    BANNED_MODULES: Set[str] = {
        "os", "sys", "subprocess", "shutil", "socket", "http",
        "urllib", "requests", "multiprocessing", "threading",
        "ctypes", "builtins", "importlib", "signal", "pty",
        "posix", "winreg", "webbrowser", "ftplib", "smtplib"
    }

    BANNED_CALLS: Set[str] = {
        "eval", "exec", "compile", "__import__",
        "globals", "locals", "getattr", "setattr", "delattr",
        "open", "breakpoint"
    }

    BANNED_ATTRS: Set[str] = {
        "__builtins__", "__subclasses__", "__bases__", "__class__",
        "system", "popen", "spawn", "fork", "kill", "remove", "rmdir", "unlink"
    }

    @classmethod
    def analyze(cls, tree: ast.AST) -> Dict[str, Any]:
        """
        Inspects an AST tree against banned primitives, imports, and calls.
        Returns {"safe": bool, "violations": List[str]}.
        """
        violations: List[str] = []

        for node in ast.walk(tree):
            # 1. Check direct imports: import os, import subprocess
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split('.')[0]
                    if root_mod in cls.BANNED_MODULES:
                        violations.append(f"Banned module import: '{alias.name}'")

            # 2. Check from imports: from os import path, from subprocess import Popen
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split('.')[0]
                    if root_mod in cls.BANNED_MODULES:
                        violations.append(f"Banned module import: '{node.module}'")

            # 3. Check function / method calls
            elif isinstance(node, ast.Call):
                # Simple function calls: eval(...), exec(...), open(...)
                if isinstance(node.func, ast.Name):
                    if node.func.id in cls.BANNED_CALLS:
                        violations.append(f"Banned function call: '{node.func.id}()'")

                # Attribute calls: os.system(...), subprocess.run(...)
                elif isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    # Check if attribute itself is dangerous
                    if attr_name in cls.BANNED_ATTRS:
                        violations.append(f"Banned attribute access/call: '.{attr_name}()'")

                    # Check parent module/variable name if static
                    if isinstance(node.func.value, ast.Name):
                        val_name = node.func.value.id
                        if val_name in cls.BANNED_MODULES:
                            violations.append(f"Banned method call on module: '{val_name}.{attr_name}()'")

            # 4. Check attribute access (e.g. obj.__subclasses__, obj.__builtins__)
            elif isinstance(node, ast.Attribute):
                if node.attr in cls.BANNED_ATTRS:
                    violations.append(f"Banned security attribute access: '{node.attr}'")

        if violations:
            return {
                "safe": False,
                "reason": "; ".join(violations),
                "violations": violations
            }

        return {
            "safe": True,
            "reason": None,
            "violations": []
        }
