import os
import ast
import re
import sys
from typing import List, Dict, Set
from schemas import StaticCheckReport

def run_static_checks(generated_project_dir: str) -> StaticCheckReport:
    """Performs static code checks (syntax, imports, dependencies)

    on synthesized modules in the generated project directory.
    """
    errors = []
    syntax_valid = True
    imports_valid = True
    dependencies_valid = True

    # 1. Discover all Python files
    py_files = []
    for root, _, files in os.walk(generated_project_dir):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    if not py_files:
        return StaticCheckReport(
            syntax_valid=False,
            imports_valid=False,
            dependencies_valid=False,
            errors=["No generated Python files found to validate."]
        )

    # Standard python built-in modules to ignore in dependency checks
    stdlib_modules = set(sys.builtin_module_names) | {
        "os", "sys", "time", "datetime", "json", "math", "re", "collections", 
        "typing", "argparse", "traceback", "logging", "shutil", "tempfile"
    }

    # 2. Parse requirements.txt if present
    req_path = os.path.join(generated_project_dir, "requirements.txt")
    declared_deps = set()
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract base package name (e.g. torch>=2.0 -> torch)
                    dep = re.split(r'[<>=~]', line)[0].strip().lower()
                    declared_deps.add(dep)

    # 3. Analyze each Python file
    imported_third_party = set()

    for py_filepath in py_files:
        rel_path = os.path.relpath(py_filepath, generated_project_dir).replace(os.sep, "/")
        
        # Read file source
        with open(py_filepath, "r", encoding="utf-8") as f:
            source = f.read()

        # A. Syntax Check
        try:
            tree = ast.parse(source, filename=py_filepath)
        except SyntaxError as se:
            syntax_valid = False
            errors.append(f"SyntaxError in {rel_path} at line {se.lineno}: {se.msg}")
            continue

        # B. Imports Walk
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split('.')[0]
                    if name not in stdlib_modules:
                        imported_third_party.add(name.lower())
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    # Relative import (e.g., from ..models import backbone)
                    # We consider it valid as it is internal
                    continue
                if not node.module:
                    continue
                    
                first_part = node.module.split('.')[0]
                
                # Check if it is a local module within the project (e.g. from models.backbone import FeatureExtractor)
                local_mod_path = os.path.join(generated_project_dir, first_part)
                # Check if it is a directory (package) or a python file (module)
                is_local = os.path.exists(local_mod_path) or os.path.exists(local_mod_path + ".py")
                
                if is_local:
                    # Verify imports resolve to actual subfiles
                    module_rel_path = node.module.replace(".", os.sep)
                    subfile_path = os.path.join(generated_project_dir, module_rel_path + ".py")
                    subdir_path = os.path.join(generated_project_dir, module_rel_path)
                    
                    if not (os.path.exists(subfile_path) or os.path.exists(subdir_path)):
                        imports_valid = False
                        errors.append(f"ImportError in {rel_path}: Local module '{node.module}' does not exist on disk.")
                else:
                    if first_part not in stdlib_modules:
                        imported_third_party.add(first_part.lower())

    # C. Dependencies match check
    pypi_mapping = {
        "pil": "pillow",
        "sklearn": "scikit-learn",
        "skimage": "scikit-image"
    }
    
    for dep in imported_third_party:
        mapped_dep = pypi_mapping.get(dep, dep)
        if mapped_dep not in declared_deps:
            dependencies_valid = False
            errors.append(f"DependencyWarning: Package '{dep}' is imported but not declared in requirements.txt")

    return StaticCheckReport(
        syntax_valid=syntax_valid,
        imports_valid=imports_valid,
        dependencies_valid=dependencies_valid,
        errors=errors
    )
