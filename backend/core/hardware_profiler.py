import os
import sys
import platform
import subprocess
import re
import datetime
import multiprocessing
from typing import List, Dict

import psutil
from schemas import (
    CPUProfile,
    RAMProfile,
    GPUProfile,
    DiskProfile,
    OSProfile,
    PythonProfile,
    HardwareProfile
)

def get_cpu_name() -> str:
    """Returns the CPU name / processor model."""
    if platform.system() == "Windows":
        try:
            # Win32_Processor Name query via powershell
            cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"]
            name = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
            if name:
                return name
        except:
            pass
    elif platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
        except:
            pass
    elif platform.system() == "Darwin":
        try:
            cmd = ["sysctl", "-n", "machdep.cpu.brand_string"]
            return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        except:
            pass
    
    return platform.processor() or "Unknown CPU"

def get_cuda_version() -> str:
    """Detects system CUDA version."""
    cuda_version = "Unknown"
    # Try PyTorch
    try:
        import torch
        if torch.cuda.is_available() and torch.version.cuda:
            return torch.version.cuda
    except:
        pass

    # Try nvcc compiler version
    try:
        output = subprocess.check_output(["nvcc", "--version"], text=True, stderr=subprocess.DEVNULL)
        match = re.search(r"release (\d+\.\d+)", output)
        if match:
            cuda_version = match.group(1)
    except:
        pass
    
    return cuda_version

def get_driver_version() -> str:
    """Detects NVIDIA Driver Version."""
    try:
        cmd = ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"]
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip().splitlines()[0]
    except:
        pass
    return "Unknown"

def profile_gpus() -> List[GPUProfile]:
    """Profiles GPU hardware, parsing nvidia-smi if available, falling back to torch."""
    gpus = []
    cuda_ver = get_cuda_version()
    driver_ver = get_driver_version()

    # Tries nvidia-smi
    try:
        cmd = ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.free,memory.used,temperature.gpu", "--format=csv,noheader,nounits"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        for line in output.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                name, drv, tot, free, usd, temp = parts
                gpus.append(GPUProfile(
                    name=name,
                    driver_version=drv,
                    cuda_version=cuda_ver,
                    vram_total_gb=round(float(tot) / 1024.0, 2),
                    vram_free_gb=round(float(free) / 1024.0, 2),
                    vram_used_gb=round(float(usd) / 1024.0, 2),
                    temperature_c=float(temp)
                ))
    except:
        # Fallback to PyTorch
        try:
            import torch
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    tot_mem = torch.cuda.get_device_properties(i).total_memory / (1024 ** 3)
                    # Allocated by torch currently
                    used_mem = torch.cuda.memory_allocated(i) / (1024 ** 3)
                    gpus.append(GPUProfile(
                        name=torch.cuda.get_device_name(i),
                        driver_version=driver_ver,
                        cuda_version=torch.version.cuda or cuda_ver,
                        vram_total_gb=round(tot_mem, 2),
                        vram_free_gb=round(tot_mem - used_mem, 2),
                        vram_used_gb=round(used_mem, 2),
                        temperature_c=-1.0
                    ))
        except:
            pass
            
    return gpus

def profile_hardware() -> HardwareProfile:
    """Collects system specification statistics (CPU, RAM, GPU, Disk, OS, Python)."""
    # 1. Profile CPU
    logical_cores = psutil.cpu_count(logical=True) or multiprocessing.cpu_count()
    physical_cores = psutil.cpu_count(logical=False) or logical_cores
    
    cpu_freq_val = 0.0
    try:
        freq = psutil.cpu_freq()
        if freq:
            cpu_freq_val = float(freq.current)
    except:
        pass
        
    cpu_prof = CPUProfile(
        processor_name=get_cpu_name(),
        physical_cores=physical_cores,
        logical_cores=logical_cores,
        frequency_mhz=cpu_freq_val,
        usage_pct=psutil.cpu_percent(interval=0.1)
    )

    # 2. Profile RAM
    ram = psutil.virtual_memory()
    ram_prof = RAMProfile(
        total_gb=round(ram.total / (1024 ** 3), 2),
        available_gb=round(ram.available / (1024 ** 3), 2),
        used_gb=round(ram.used / (1024 ** 3), 2),
        usage_pct=ram.percent
    )

    # 3. Profile GPU & VRAM
    gpus_prof = profile_gpus()

    # 4. Profile Disk
    # Find active project root path
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    disk = psutil.disk_usage(backend_dir)
    disk_prof = DiskProfile(
        path=os.path.abspath(backend_dir),
        total_gb=round(disk.total / (1024 ** 3), 2),
        free_gb=round(disk.free / (1024 ** 3), 2),
        used_gb=round(disk.used / (1024 ** 3), 2),
        usage_pct=disk.percent
    )

    # 5. Profile OS
    os_prof = OSProfile(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine()
    )

    # 6. Profile Python Environment
    in_venv = sys.prefix != sys.base_prefix or "VIRTUAL_ENV" in os.environ
    
    target_pkgs = [
        "torch", "psutil", "langchain", "docling", "grobid-client", 
        "pydantic", "fastapi", "uvicorn", "langgraph", "langchain-ollama"
    ]
    pkg_versions = {}
    for pkg in target_pkgs:
        try:
            # Normalize import module name
            mod_name = pkg.replace("-", "_")
            mod = __import__(mod_name)
            if hasattr(mod, "__version__"):
                pkg_versions[pkg] = str(mod.__version__)
            elif hasattr(mod, "version"):
                pkg_versions[pkg] = str(mod.version)
            else:
                pkg_versions[pkg] = "Installed"
        except ImportError:
            pkg_versions[pkg] = "Not Installed"

    python_prof = PythonProfile(
        version=sys.version,
        executable=sys.executable,
        in_virtualenv=in_venv,
        package_versions=pkg_versions
    )

    return HardwareProfile(
        cpu=cpu_prof,
        ram=ram_prof,
        gpus=gpus_prof,
        disk=disk_prof,
        os=os_prof,
        python=python_prof,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z"
    )
