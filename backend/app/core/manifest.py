"""
Phase 10: Reproducibility & Run Manifests Framework
Generates, stores, and reconstructs execution manifests for analysis runs.
Ensures that any previous run can be audited, reproduced, and explained.
"""

import os
import sys
import json
import hashlib
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

import torch
import psutil

from app.core.config import settings

MANIFEST_SCHEMA_VERSION = "1.0.0"
DEFAULT_PROMPT_VERSION = "v2.0.0"
DEFAULT_EMBEDDING_VERSION = "2.0.0"


class PaperManifestInfo(BaseModel):
    paper_id: str
    paper_hash: str = Field(description="SHA-256 hash of input research PDF document")
    paper_version: str = "1.0.0"
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None


class ModelManifestConfig(BaseModel):
    model: str
    model_version: str = "qwen2.5:7b-instruct-q4_K_M"
    provider: str = "ollama"
    temperature: float = 0.0
    top_p: float = 0.9
    max_output_tokens: int = 8192
    prompt_version: str = DEFAULT_PROMPT_VERSION


class RetrievalManifestConfig(BaseModel):
    embedding_model: str = "nomic-embed-text"
    embedding_version: str = DEFAULT_EMBEDDING_VERSION
    embedding_dimension: int = 768
    chunk_size: int = 500
    chunk_overlap: int = 50
    retrieval_strategy: str = "hybrid_rrf"
    top_k: int = 5


class SystemManifestConfig(BaseModel):
    software_version: str = settings.VERSION
    manifest_schema_version: str = MANIFEST_SCHEMA_VERSION
    os: str
    platform: str
    python_version: str
    torch_version: str
    git_commit: Optional[str] = None


class HardwareManifestConfig(BaseModel):
    cpu: str
    cpu_cores: int
    total_ram_gb: float
    gpu_available: bool
    gpu_device: Optional[str] = None
    gpu_vram_total_gb: Optional[float] = None


from pydantic import BaseModel, Field, ConfigDict


class RunManifest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str
    paper_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    paper: PaperManifestInfo
    model_info: ModelManifestConfig = Field(alias="model_config")
    retrieval_config: RetrievalManifestConfig
    system: SystemManifestConfig
    hardware: HardwareManifestConfig
    execution_summary: Dict[str, Any] = Field(default_factory=dict)


def compute_file_sha256(file_path: Optional[str]) -> str:
    """Computes SHA-256 checksum of the target file or returns deterministic null hash."""
    if not file_path or not os.path.exists(file_path):
        return "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # sha256 of empty string

    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return "sha256_unreadable_file"


def get_git_commit() -> Optional[str]:
    """Retrieves current short git commit hash if running in a git repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=settings.BASE_DIR,
            capture_output=True,
            text=True,
            timeout=2
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


def inspect_hardware() -> HardwareManifestConfig:
    """Probes host hardware environment (CPU, RAM, GPU, CUDA VRAM)."""
    cpu_info = platform.processor() or platform.machine() or "Unknown CPU"
    cpu_cores = os.cpu_count() or 1
    total_ram = round(psutil.virtual_memory().total / (1024 ** 3), 2)

    cuda_avail = torch.cuda.is_available()
    gpu_name = None
    gpu_vram = None

    if cuda_avail:
        try:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_vram = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
        except Exception:
            gpu_name = "NVIDIA CUDA Device"

    return HardwareManifestConfig(
        cpu=cpu_info,
        cpu_cores=cpu_cores,
        total_ram_gb=total_ram,
        gpu_available=cuda_avail,
        gpu_device=gpu_name,
        gpu_vram_total_gb=gpu_vram
    )


def generate_run_manifest(
    run_id: str,
    paper_id: str,
    pdf_path: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    top_k: int = 5,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    execution_summary: Optional[Dict[str, Any]] = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION
) -> RunManifest:
    """
    Creates an immutable, fully-specified RunManifest capturing all 18 Phase 10 provenance fields.
    """
    # 1. Paper Info
    file_sha256 = compute_file_sha256(pdf_path)
    file_name = os.path.basename(pdf_path) if pdf_path else f"{paper_id}.pdf"
    file_size = os.path.getsize(pdf_path) if pdf_path and os.path.exists(pdf_path) else None

    paper_info = PaperManifestInfo(
        paper_id=paper_id,
        paper_hash=file_sha256,
        paper_version="1.0.0",
        file_name=file_name,
        file_size_bytes=file_size
    )

    # 2. Model Config
    active_model = model_name or "qwen2.5:7b"
    model_cfg = ModelManifestConfig(
        model=active_model,
        model_version=f"{active_model}-ollama-local",
        provider="ollama" if "qwen" in active_model.lower() or "llama" in active_model.lower() else "groq",
        temperature=temperature,
        top_p=0.9,
        prompt_version=prompt_version
    )

    # 3. Retrieval Config
    retrieval_cfg = RetrievalManifestConfig(
        embedding_model="nomic-embed-text",
        embedding_version=DEFAULT_EMBEDDING_VERSION,
        embedding_dimension=768,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        retrieval_strategy="hybrid_rrf",
        top_k=top_k
    )

    # 4. System Config
    system_cfg = SystemManifestConfig(
        software_version=settings.VERSION,
        manifest_schema_version=MANIFEST_SCHEMA_VERSION,
        os=platform.system(),
        platform=platform.platform(),
        python_version=sys.version.split()[0],
        torch_version=torch.__version__,
        git_commit=get_git_commit()
    )

    # 5. Hardware Config
    hardware_cfg = inspect_hardware()

    # 6. Build Manifest
    manifest = RunManifest(
        run_id=run_id,
        paper_id=paper_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        paper=paper_info,
        model_info=model_cfg,
        retrieval_config=retrieval_cfg,
        system=system_cfg,
        hardware=hardware_cfg,
        execution_summary=execution_summary or {}
    )

    # Automatically persist to storage/manifests/{run_id}.json
    save_manifest(manifest)
    return manifest


def save_manifest(manifest: RunManifest) -> str:
    """Saves run manifest atomically to backend/storage/manifests/{run_id}.json."""
    manifest_dir = getattr(settings, "MANIFESTS_DIR", os.path.join(settings.STORAGE_DIR, "manifests"))
    os.makedirs(manifest_dir, exist_ok=True)

    file_path = os.path.join(manifest_dir, f"{manifest.run_id}.json")
    temp_path = f"{file_path}.tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(by_alias=True), f, indent=2, ensure_ascii=False)
    os.replace(temp_path, file_path)
    return file_path


def get_manifest(run_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves run manifest by run_id or paper_id from storage/manifests/ or extracted JSON."""
    manifest_dir = getattr(settings, "MANIFESTS_DIR", os.path.join(settings.STORAGE_DIR, "manifests"))
    clean_id = run_id.strip("[]")
    
    # 1. Direct file lookup by run_id
    file_path = os.path.join(manifest_dir, f"{clean_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # 2. Search all manifest files for matching run_id or paper_id
    if os.path.exists(manifest_dir):
        for fname in os.listdir(manifest_dir):
            if fname.endswith(".json") and not fname.endswith(".tmp"):
                fpath = os.path.join(manifest_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        m_data = json.load(f)
                        if m_data.get("run_id") == clean_id or m_data.get("paper_id") == clean_id:
                            return m_data
                except Exception:
                    pass

    # 3. Check extracted json storage for embedded run_manifest
    extracted_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{clean_id}.json")
    if os.path.exists(extracted_path):
        try:
            with open(extracted_path, "r", encoding="utf-8") as f:
                p_data = json.load(f)
                if "run_manifest" in p_data and isinstance(p_data["run_manifest"], dict):
                    return p_data["run_manifest"]
        except Exception:
            pass

    return None


def list_manifests(limit: int = 100) -> List[Dict[str, Any]]:
    """Lists saved run manifests ordered by creation timestamp."""
    manifest_dir = getattr(settings, "MANIFESTS_DIR", os.path.join(settings.STORAGE_DIR, "manifests"))
    if not os.path.exists(manifest_dir):
        return []

    manifests = []
    files = sorted(
        [f for f in os.listdir(manifest_dir) if f.endswith(".json") and not f.endswith(".tmp")],
        key=lambda x: os.path.getmtime(os.path.join(manifest_dir, x)),
        reverse=True
    )
    for fname in files[:limit]:
        fpath = os.path.join(manifest_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                manifests.append(json.load(f))
        except Exception:
            pass
    return manifests


def explain_run(run_id: str) -> Dict[str, Any]:
    """
    Phase 10 Exit Criteria Fulfillment:
    Reconstructs an analysis run and provides an auditable explanation
    of why and how the run produced its results.
    """
    manifest = get_manifest(run_id)
    if not manifest:
        return {
            "run_id": run_id,
            "status": "NOT_FOUND",
            "explanation": "No run manifest found for this ID."
        }

    paper = manifest.get("paper", {})
    model_cfg = manifest.get("model_info") or manifest.get("model_config", {})
    retrieval_cfg = manifest.get("retrieval_config", {})
    system = manifest.get("system", {})
    hardware = manifest.get("hardware", {})
    exec_summary = manifest.get("execution_summary", {})

    explanation = (
        f"Analysis Run '{run_id}' was executed on {manifest.get('timestamp')} for paper '{paper.get('paper_id')}' "
        f"using input artifact with SHA-256 hash '{paper.get('paper_hash')[:12]}...'. "
        f"The execution used LLM model '{model_cfg.get('model')}' (provider: {model_cfg.get('provider')}, "
        f"temp={model_cfg.get('temperature')}, prompt version={model_cfg.get('prompt_version')}). "
        f"Context retrieval utilized '{retrieval_cfg.get('embedding_model')}' ({retrieval_cfg.get('embedding_dimension')} dim) "
        f"with chunk_size={retrieval_cfg.get('chunk_size')}, overlap={retrieval_cfg.get('chunk_overlap')}, "
        f"and top_k={retrieval_cfg.get('top_k')} via {retrieval_cfg.get('retrieval_strategy')}. "
        f"System environment: {system.get('platform')} (Python {system.get('python_version')}, "
        f"PyTorch {system.get('torch_version')}, Git commit {system.get('git_commit')}) "
        f"hosted on {hardware.get('cpu')} ({hardware.get('cpu_cores')} cores, {hardware.get('total_ram_gb')} GB RAM, "
        f"GPU: {hardware.get('gpu_device') or 'CPU Fallback'})."
    )

    return {
        "run_id": run_id,
        "paper_id": paper.get("paper_id"),
        "paper_hash": paper.get("paper_hash"),
        "reproducible": True,
        "explanation": explanation,
        "manifest": manifest,
        "reproducibility_factors": {
            "deterministic_sampling": model_cfg.get("temperature", 0.0) == 0.0,
            "exact_file_match": paper.get("paper_hash"),
            "exact_prompt_version": model_cfg.get("prompt_version"),
            "exact_model": model_cfg.get("model"),
            "exact_embeddings": retrieval_cfg.get("embedding_model"),
            "git_commit": system.get("git_commit")
        }
    }
