import os
import json
import torch
from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.pipeline import FeasibilityReport, ExtractedParameters, ComponentGraph
from app.core.model_router import ModelRouter


def detect_local_hardware_gpu() -> Dict[str, Any]:
    """Detects active GPU, available VRAM in GB, and system RAM bounds."""
    gpu_info = {
        "gpu_available": False,
        "device_name": "CPU Only",
        "total_vram_gb": 4.0,  # Default fallback 4GB
        "free_vram_gb": 4.0
    }
    
    try:
        if torch.cuda.is_available():
            gpu_info["gpu_available"] = True
            gpu_info["device_name"] = torch.cuda.get_device_name(0)
            total_bytes = torch.cuda.get_device_properties(0).total_memory
            gpu_info["total_vram_gb"] = round(total_bytes / (1024 ** 3), 2)
            gpu_info["free_vram_gb"] = round(torch.cuda.mem_get_info()[0] / (1024 ** 3), 2)
    except Exception as e:
        print(f"[Feasibility Agent WARN] PyTorch CUDA detection fallback ({e}).")
        
    return gpu_info


def calculate_estimated_vram(
    batch_size: int = 16, 
    input_resolution: int = 256, 
    num_components: int = 4
) -> float:
    """
    Computes mathematical VRAM memory footprint estimation in GB:
    VRAM = Model Weights (FP32/FP16) + Activation Tensors + Optimizer States (AdamW 8-bytes/param).
    """
    base_model_params_mb = num_components * 35.0  # Approx 35M parameters per component block
    bytes_per_param = 4  # FP32 precision
    
    # Activation Memory = Batch_Size * Channels * Height * Width * Num_Layers
    activation_memory_mb = (batch_size * 64 * input_resolution * input_resolution * 4) / (1024 * 1024)
    
    # Optimizer Memory (AdamW uses 8 bytes per parameter for momentum + variance)
    optimizer_memory_mb = base_model_params_mb * 8.0
    
    total_memory_mb = (base_model_params_mb * bytes_per_param) + activation_memory_mb + optimizer_memory_mb
    total_vram_gb = round(total_memory_mb / 1024.0, 2)
    
    return max(1.5, min(32.0, total_vram_gb))


def run_feasibility_agent(
    component_graph: Any = None, 
    constraints: Optional[Dict[str, Any]] = None, 
    parameters: Optional[ExtractedParameters] = None,
    model_name: str = settings.DEFAULT_MODEL
) -> FeasibilityReport:
    """
    Evaluates deep learning model feasibility, memory footprint, and hardware bounds
    against local GPU limitations and compute constraints.
    """
    if constraints is None:
        constraints = {}

    hw_info = detect_local_hardware_gpu()
    available_vram = float(constraints.get("max_vram_gb", hw_info["total_vram_gb"]))
    
    # Extract training batch size and spatial resolution
    batch_size = 16
    input_res = 256
    num_comps = 4
    
    if parameters:
        try:
            batch_size = int(str(parameters.batch_size.value).split()[0])
        except Exception:
            pass

    if isinstance(component_graph, ComponentGraph) and component_graph.components:
        num_comps = len(component_graph.components)
    elif isinstance(component_graph, dict) and "components" in component_graph:
        num_comps = len(component_graph.get("components", []))

    # Calculate real mathematical VRAM estimation
    estimated_vram = calculate_estimated_vram(batch_size=batch_size, input_resolution=input_res, num_components=num_comps)

    status = "FEASIBLE"
    bottlenecks = []
    adaptations = []

    if estimated_vram > available_vram:
        if estimated_vram > available_vram * 1.5:
            status = "NOT_FEASIBLE"
            bottlenecks.append(f"Model VRAM requirement ({estimated_vram} GB) severely exceeds GPU limit ({available_vram} GB).")
            adaptations.append(f"Reduce batch size from {batch_size} to {max(1, batch_size // 4)} and use FP16 mixed precision.")
            adaptations.append("Apply LoRA adapter fine-tuning to freeze visual backbone parameters.")
            adaptations.append("Offload model training to cloud GPU platforms (Google Colab T4 or Kaggle Kernels).")
        else:
            status = "FEASIBLE_WITH_MODIFICATION"
            bottlenecks.append(f"Peak VRAM ({estimated_vram} GB) approaches available GPU memory ({available_vram} GB).")
            adaptations.append(f"Reduce batch size to {max(2, batch_size // 2)} and enable gradient accumulation (4 steps).")
            adaptations.append("Enable PyTorch activation checkpointing (`torch.utils.checkpoint`).")

    else:
        bottlenecks.append(f"Estimated peak memory ({estimated_vram} GB) fits cleanly inside available GPU RAM ({available_vram} GB).")
        adaptations.append("Standard FP16 training with PyTorch Automatic Mixed Precision (`torch.cuda.amp`).")

    print(f"[Feasibility Agent] Evaluated VRAM: {estimated_vram} GB vs Available: {available_vram} GB -> Status: {status}")

    return FeasibilityReport(
        overall_status=status,
        estimated_vram_gb=estimated_vram,
        available_vram_gb=available_vram,
        bottlenecks=bottlenecks,
        suggested_adaptations=adaptations
    )

