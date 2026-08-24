import os
import sys
import json

# Set up backend directory import path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core.hardware_profiler import profile_hardware

def test_hardware_profiler():
    print("==========================================================")
    print("RUNNING DAY 23 HARDWARE PROFILER VERIFICATION TEST")
    print("==========================================================")
    
    # 1. Profile system hardware
    profile = profile_hardware()
    
    # 2. Serialize profile to JSON dict for structural validation
    profile_dict = profile.model_dump()
    
    print("\n--- DETECTED CPU PROFILE ---")
    print(json.dumps(profile_dict["cpu"], indent=2))
    
    print("\n--- DETECTED RAM PROFILE ---")
    print(json.dumps(profile_dict["ram"], indent=2))
    
    print("\n--- DETECTED GPU PROFILE(S) ---")
    print(json.dumps(profile_dict["gpus"], indent=2))
    
    print("\n--- DETECTED DISK PROFILE ---")
    print(json.dumps(profile_dict["disk"], indent=2))
    
    print("\n--- DETECTED OS PROFILE ---")
    print(json.dumps(profile_dict["os"], indent=2))
    
    print("\n--- DETECTED PYTHON PROFILE ---")
    print(json.dumps(profile_dict["python"], indent=2))
    
    # 3. Assertions to verify correctness
    assert profile.cpu.processor_name, "CPU processor name must be populated"
    assert profile.cpu.logical_cores > 0, "Logical cores must be greater than 0"
    assert profile.ram.total_gb > 0.0, "Total system RAM must be greater than 0"
    assert profile.disk.total_gb > 0.0, "Total disk space must be greater than 0"
    assert profile.os.system, "OS system platform must be populated"
    assert profile.python.version, "Python version must be populated"
    assert profile.timestamp.endswith("Z"), "Timestamp must be ISO-formatted and UTC (Z)"
    
    print("\n==========================================================")
    print("[OK] SUCCESS: DAY 23 HARDWARE PROFILER VERIFIED AND PASSED!")
    print("==========================================================")

if __name__ == "__main__":
    test_hardware_profiler()
