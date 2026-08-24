import os
import subprocess
import re
import multiprocessing

def detect_gpu_nvismi():
    """Detects NVIDIA GPU details using nvidia-smi utility."""
    try:
        cmd = ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        line = output.strip().split('\n')[0]
        if ',' in line:
            name, mem_str = line.split(',', 1)
            vram_gb = float(mem_str.strip()) / 1024.0
            return name.strip(), round(vram_gb, 1)
    except:
        pass
    
    try:
        abs_path = r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"
        if os.path.exists(abs_path):
            cmd = [abs_path, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            line = output.strip().split('\n')[0]
            if ',' in line:
                name, mem_str = line.split(',', 1)
                vram_gb = float(mem_str.strip()) / 1024.0
                return name.strip(), round(vram_gb, 1)
    except:
        pass
    return None, None

def detect_gpu():
    """Tries to query PyTorch for GPU details, falls back to nvidia-smi."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return gpu_name, round(vram_gb, 1)
    except:
        pass
    
    name, vram = detect_gpu_nvismi()
    if name:
        return name, round(vram, 1)
    return "CPU Only / Integrated Graphics", 0.0

def detect_system_ram():
    """Detects physical system RAM in GB using PowerShell CIM query (Windows 11 compliant)."""
    try:
        cmd = ["powershell", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        ram_bytes = float(output.strip())
        return round(ram_bytes / (1024**3), 1)
    except:
        pass
    return 16.0

# Phase 6 Day 23 integrated hardware profiler
from core.hardware_profiler import profile_hardware

