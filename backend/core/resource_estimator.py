import os
import sys
import json
from langchain_ollama import ChatOllama
from schemas import (
    ExtractedParameters,
    HardwareProfile,
    ModelResourceRequirement,
    DatasetResourceRequirement,
    TrainingResourceRequirement,
    InferenceResourceRequirement,
    StorageResourceRequirement,
    ResourceEstimationReport
)

def parse_numeric(val_str: str, default: float) -> float:
    """Safely extracts the first numeric value from a string."""
    if not val_str or val_str.lower() == "not specified":
        return default
    try:
        # Extract digits, dots, or scientific notation
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", val_str)
        if nums:
            return float(nums[0])
    except:
        pass
    return default

def estimate_resources(
    extracted_parameters: ExtractedParameters,
    hardware_profile: HardwareProfile,
    model_name: str = "qwen2.5-coder:1.5b"
) -> ResourceEstimationReport:
    """
    Computes mathematical allocations for deep learning resource footprint
    and uses Ollama to synthesize principal engineering descriptions.
    """
    import re
    
    # 1. Resolve Extracted Parameters with reasonable defaults
    model_val = extracted_parameters.model.value if extracted_parameters.model else "VLCD"
    dataset_val = extracted_parameters.dataset.value if extracted_parameters.dataset else "LEVIR-CD"
    optimizer_val = extracted_parameters.optimizer.value if extracted_parameters.optimizer else "AdamW"
    
    batch_size = int(parse_numeric(extracted_parameters.batch_size.value if extracted_parameters.batch_size else "", 16))
    epochs = int(parse_numeric(extracted_parameters.epochs.value if extracted_parameters.epochs else "", 50))
    
    input_size_str = extracted_parameters.input_size.value if extracted_parameters.input_size else "256x256"
    input_size_w = 256
    input_size_h = 256
    try:
        dims = [int(s) for s in re.findall(r"\d+", input_size_str)]
        if len(dims) >= 2:
            input_size_w, input_size_h = dims[0], dims[1]
    except:
        pass

    # 2. Mathematical Calculations
    
    # Model Weights Estimation (based on backbone)
    # CLIP Vit-B: ~86M, Swin-T: ~28M, ResNet-18: ~11M
    model_clean = model_val.lower()
    if "clip" in model_clean or "vit" in model_clean:
        param_count_m = 86.0
    elif "swin" in model_clean or "rfn" in model_clean:
        param_count_m = 28.0
    elif "resnet-18" in model_clean or "resnet18" in model_clean:
        param_count_m = 11.7
    elif "resnet-50" in model_clean or "resnet50" in model_clean:
        param_count_m = 25.6
    else:
        param_count_m = 25.0 # fallback default for general CD models

    model_weights_mb = param_count_m * 4.0 # float32 weights
    vram_minimum_gb = model_weights_mb / 1024.0

    # Dataset Footprint
    dataset_clean = dataset_val.lower()
    if "levir" in dataset_clean:
        raw_size_gb = 1.5
        sample_count = 10120
    elif "whu" in dataset_clean:
        raw_size_gb = 1.0
        sample_count = 7400
    elif "cdd" in dataset_clean:
        raw_size_gb = 1.2
        sample_count = 10000
    else:
        raw_size_gb = 2.0
        sample_count = 5000

    # Training VRAM Requirements
    # VRAM = weights + gradients + optimizer_state + activations
    weights_mem_gb = (param_count_m * 4) / 1024.0
    gradients_mem_gb = (param_count_m * 4) / 1024.0
    # Adam holds momentum + variance (8 bytes per param)
    opt_bytes_per_param = 8.0 if "adam" in optimizer_val.lower() else 4.0
    optimizer_mem_gb = (param_count_m * opt_bytes_per_param) / 1024.0
    
    # Approx activations footprint per batch: batch * w * h * channels * layers * 4 bytes
    activations_mem_gb = (batch_size * input_size_w * input_size_h * 64 * 12 * 4) / (1024 ** 3)
    
    vram_recommended_gb = round(weights_mem_gb + gradients_mem_gb + optimizer_mem_gb + activations_mem_gb, 2)
    ram_recommended_gb = round(max(16.0, vram_recommended_gb * 1.5), 1)

    # Training Time Estimation on System GPU
    # Baseline sample processing time per batch item = 0.004 seconds on RTX 4090
    gpu_factor = 1.0
    has_gpu = False
    if hardware_profile.gpus:
        has_gpu = True
        local_gpu = hardware_profile.gpus[0]
        # RTX 5050 / RTX 3050 factor = 3.5x slower
        if local_gpu.vram_total_gb < 10.0:
            gpu_factor = 3.5
    else:
        # CPU only is 45x slower
        gpu_factor = 45.0

    sample_sec = 0.004 * gpu_factor
    total_samples = sample_count * epochs
    estimated_time_hours = round((total_samples * sample_sec) / 3600.0, 2)

    # Inference Requirements
    inference_vram_gb = round(weights_mem_gb + (1 * input_size_w * input_size_h * 64 * 12 * 4) / (1024 ** 3), 2)
    inference_ram_gb = round(max(4.0, weights_mem_gb * 2.0), 1)
    # Inference latency estimation per batch
    latency_ms = round(15.0 * gpu_factor, 1)

    # Storage Footprint
    # Raw dataset + 10 saved checkpoints
    storage_required_gb = round(raw_size_gb + (vram_minimum_gb * 10), 2)

    # Resource tier
    if vram_recommended_gb > 16.0:
        overall_resource_tier = "EXTREME"
    elif vram_recommended_gb > 10.0:
        overall_resource_tier = "HIGH"
    elif vram_recommended_gb > 4.0:
        overall_resource_tier = "MEDIUM"
    else:
        overall_resource_tier = "LOW"

    # 3. LLM Description Synthesis (No placeholders!)
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=2048, num_predict=512)
    
    prompt = (
        "You are a Senior Deep Learning Platform Architect. Write short, precise, professional description sentences "
        "documenting system resource requirements for this project adaptation. Write exactly 1 paragraph (2-3 sentences) per description.\n\n"
        "--- CALCULATION SPECS ---\n"
        f"- Model: {model_val} ({param_count_m}M params, weights {model_weights_mb}MB)\n"
        f"- Dataset: {dataset_val} ({sample_count} samples, {raw_size_gb}GB raw)\n"
        f"- Training recommendation: {vram_recommended_gb}GB VRAM, {ram_recommended_gb}GB system RAM, estimated time {estimated_time_hours} hours\n"
        f"- Inference recommendation: {inference_vram_gb}GB VRAM, {inference_ram_gb}GB RAM, {latency_ms}ms latency\n"
        f"- Disk Storage: {storage_required_gb}GB total\n\n"
        "Write a JSON response matching exactly this key structure (do NOT include markdown code blocks or formatting, output raw JSON only):\n"
        "{\n"
        "  \"model_desc\": \"...\",\n"
        "  \"dataset_desc\": \"...\",\n"
        "  \"training_desc\": \"...\",\n"
        "  \"inference_desc\": \"...\",\n"
        "  \"storage_desc\": \"...\"\n"
        "}"
    )

    model_desc = f"Model parameters estimated at {param_count_m} million with weights footprint of {model_weights_mb}MB."
    dataset_desc = f"Dataset raw space is {raw_size_gb}GB, with {sample_count} sample patches."
    training_desc = f"Recommended training environment requires {vram_recommended_gb}GB of VRAM and {ram_recommended_gb}GB system RAM."
    inference_desc = f"Inference requires {inference_vram_gb}GB VRAM and is estimated at {latency_ms}ms batch latency."
    storage_desc = f"Total project footprint on disk requires {storage_required_gb}GB storage space."

    try:
        resp = llm.invoke(prompt).content.strip()
        # Clean potential markdown wrapping if returned
        if resp.startswith("```"):
            resp = resp.split("```")[1]
            if resp.startswith("json"):
                resp = resp[4:]
        data = json.loads(resp.strip())
        model_desc = data.get("model_desc", model_desc)
        dataset_desc = data.get("dataset_desc", dataset_desc)
        training_desc = data.get("training_desc", training_desc)
        inference_desc = data.get("inference_desc", inference_desc)
        storage_desc = data.get("storage_desc", storage_desc)
    except Exception as e:
        print(f"[WARN] Resource estimation LLM description synthesis failed ({e}). Using default templates.")

    # 4. Compile Pydantic structures
    return ResourceEstimationReport(
        model=ModelResourceRequirement(
            param_count_millions=param_count_m,
            model_weights_mb=model_weights_mb,
            vram_minimum_gb=vram_minimum_gb,
            description=model_desc
        ),
        dataset=DatasetResourceRequirement(
            raw_size_gb=raw_size_gb,
            sample_count=sample_count,
            description=dataset_desc
        ),
        training=TrainingResourceRequirement(
            vram_recommended_gb=vram_recommended_gb,
            ram_recommended_gb=ram_recommended_gb,
            estimated_time_hours=estimated_time_hours,
            description=training_desc
        ),
        inference=InferenceResourceRequirement(
            vram_gb=inference_vram_gb,
            ram_gb=inference_ram_gb,
            latency_ms=latency_ms,
            description=inference_desc
        ),
        storage=StorageResourceRequirement(
            required_disk_gb=storage_required_gb,
            description=storage_desc
        ),
        overall_resource_tier=overall_resource_tier
    )
