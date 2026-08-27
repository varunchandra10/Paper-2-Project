import os
import sys
import multiprocessing
from typing import Dict, Any
from utils import detect_gpu, detect_system_ram

class Settings:
    """Central configuration class mapping hardware profiles and default properties."""
    
    def __init__(self):
        # Default LLM configurations
        self.model_name: str = os.getenv("LLM_MODEL", "gpt-oss-120b")
        
        # Respect user permission for hardware diagnostics
        # Defaults to False to prevent unauthorized command execution on installation
        self.profiling_allowed: bool = os.getenv("ALLOW_HARDWARE_PROFILING", "false").lower() == "true"
        
        if self.profiling_allowed:
            detected_gpu_name, detected_vram_gb = detect_gpu()
            detected_ram_gb = detect_system_ram()
        else:
            # Safe default fallback constraints when permission is not yet granted
            detected_gpu_name = "CPU Only (Profiling Disabled)"
            detected_vram_gb = 0.0
            detected_ram_gb = 8.0  # Safe standard baseline
        
        # Respect environment overrides if specified, otherwise fall back to detected/safe values
        self.gpu_name: str = os.getenv("OVERRIDE_GPU_MODEL", detected_gpu_name)
        
        vram_override = os.getenv("OVERRIDE_VRAM_GB")
        self.vram_gb: float = float(vram_override) if vram_override else detected_vram_gb
        
        ram_override = os.getenv("OVERRIDE_SYSTEM_RAM_GB")
        self.ram_gb: float = float(ram_override) if ram_override else detected_ram_gb
        
        self.cpu_cores: int = multiprocessing.cpu_count()
        
        # Standard constraint defaults
        self.dataset_size_images: int = 20000
        self.timeline_weeks: int = 2
        
        # Base directories
        self.backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_dir = os.path.join(self.backend_dir, "storage")
        
        os.makedirs(self.storage_dir, exist_ok=True)

    @property
    def default_constraints(self) -> Dict[str, Any]:
        """Returns the hardware and project constraint dictionary for feasibility checks."""
        return {
            "available_vram_gb": self.vram_gb,
            "gpu_model": self.gpu_name,
            "system_ram_gb": self.ram_gb,
            "cpu_cores": self.cpu_cores,
            "dataset_size_images": self.dataset_size_images,
            "timeline_weeks": self.timeline_weeks
        }

settings = Settings()
