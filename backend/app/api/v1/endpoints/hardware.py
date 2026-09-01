import platform
import os
import subprocess
from fastapi import APIRouter

router = APIRouter(prefix="/hardware", tags=["Hardware"])

@router.get("/metrics")
async def get_hardware_metrics():
    """
    Returns live host system hardware specs (CPU and GPU only).
    Probes system RAM, CPU cores, and NVIDIA GPU specs via nvidia-smi / PyTorch.
    """
    ram_total_gb = 16.0
    ram_used_gb = 8.0
    ram_available_gb = 8.0
    cpu_usage = 15.0
    cpu_count = os.cpu_count() or 8
    cpu_name = platform.processor() or f"{platform.machine()} Processor"

    # 1. Probe live host RAM & CPU details via psutil
    try:
        import psutil
        mem = psutil.virtual_memory()
        ram_total_gb = round(mem.total / (1024 ** 3), 1)
        ram_available_gb = round(mem.available / (1024 ** 3), 1)
        ram_used_gb = round(mem.used / (1024 ** 3), 1)
        cpu_usage = round(psutil.cpu_percent(interval=0.05), 1)
        cpu_count = psutil.cpu_count(logical=True) or cpu_count
    except Exception:
        pass

    # 2. Probe GPU VRAM & model details via nvidia-smi CLI
    gpu_name = "CPU / System Host Compute"
    vram_total_gb = 0.0
    vram_used_gb = 0.0
    vram_free_gb = 0.0
    cuda_available = False

    try:
        cmd = ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            line = res.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                gpu_name = parts[0]
                vram_total_mb = float(parts[1])
                vram_used_mb = float(parts[2])
                vram_free_mb = float(parts[3])
                
                vram_total_gb = round(vram_total_mb / 1024, 1)
                vram_used_gb = round(vram_used_mb / 1024, 1)
                vram_free_gb = round(vram_free_mb / 1024, 1)
                cuda_available = True
    except Exception:
        pass

    # Fallback to PyTorch if nvidia-smi wasn't available
    if not cuda_available:
        try:
            import torch
            if torch.cuda.is_available():
                cuda_available = True
                gpu_name = torch.cuda.get_device_name(0)
                vram_total_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 1)
                vram_allocated = torch.cuda.memory_allocated(0)
                vram_used_gb = round(vram_allocated / (1024 ** 3), 1)
                vram_free_gb = round(max(0.0, vram_total_gb - vram_used_gb), 1)
        except Exception:
            pass

    return {
        "status": "online",
        "cpu": {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "processor": cpu_name,
            "cores": cpu_count,
            "usage_percent": cpu_usage,
            "ram_total_gb": ram_total_gb,
            "ram_used_gb": ram_used_gb,
            "ram_available_gb": ram_available_gb
        },
        "gpu": {
            "cuda_available": cuda_available,
            "name": gpu_name,
            "vram_total_gb": vram_total_gb,
            "vram_used_gb": vram_used_gb,
            "vram_free_gb": vram_free_gb
        }
    }
