import os
import sys
import importlib
import torch
from typing import List
from schemas import AutomatedTestReport

def find_class_by_base_or_keyword(module, base_keyword: str, fallback_name: str):
    """Utility to dynamically find the correct class inside a loaded module

    based on inheritance base names or string keywords.
    """
    # 1. Look for explicit matches in class names or bases
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type):
            # Direct match
            if name == fallback_name:
                return obj
            # Check class bases for keyword (e.g. Dataset or Module)
            for base in obj.__bases__:
                if base_keyword.lower() in base.__name__.lower():
                    return obj
                    
    # 2. Case-insensitive name match lookup
    for name in dir(module):
        if base_keyword.lower() in name.lower():
            obj = getattr(module, name)
            if isinstance(obj, type):
                return obj
                
    # 3. Return fallback if name exists in module
    if hasattr(module, fallback_name):
        return getattr(module, fallback_name)
        
    return None

def run_automated_tests(generated_project_dir: str) -> AutomatedTestReport:
    """Dynamically loads and executes unit, shape, and forward pass verification tests

    across all synthesized project components.
    """
    details = []
    dataset_check = False
    backbone_check = False
    fusion_check = False
    decoder_check = False
    loss_check = False

    # Insert generated project path to Python sys.path
    if generated_project_dir not in sys.path:
        sys.path.insert(0, generated_project_dir)

    # Force unload any previously cached generated modules to ensure clean test runs
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("data.") or mod_name.startswith("models.") or mod_name.startswith("training.") or mod_name.startswith("evaluation."):
            sys.modules.pop(mod_name, None)

    try:
        # 1. Dataset Verification
        details.append("[1/5] Verifying Dataset class...")
        dataset_module = importlib.import_module("data.dataset")
        DatasetClass = find_class_by_base_or_keyword(dataset_module, "Dataset", "LEVIRCDDataset")
        
        if not DatasetClass:
            raise ImportError("Could not locate a Dataset subclass in data/dataset.py")
            
        dataset = DatasetClass()
        img1, img2, mask = dataset[0]
        
        # Validate shapes
        details.append(f"  - Loaded sample shapes: img1={list(img1.shape)}, img2={list(img2.shape)}, mask={list(mask.shape)}")
        assert len(img1.shape) == 3, "Image 1 must be (C, H, W)"
        assert len(img2.shape) == 3, "Image 2 must be (C, H, W)"
        assert len(mask.shape) == 3, "Mask must be (1, H, W)"
        dataset_check = True
        details.append("  [OK] Dataset sample validation passed.")

        # 2. Backbone Encoder Verification
        details.append("[2/5] Verifying Backbone Feature Extractor module...")
        backbone_module = importlib.import_module("models.backbone")
        BackboneClass = find_class_by_base_or_keyword(backbone_module, "Module", "FeatureExtractorBackbone")
        
        if not BackboneClass:
            raise ImportError("Could not locate Backbone Module class in models/backbone.py")
            
        backbone = BackboneClass()
        dummy_input = torch.randn(2, 3, 128, 128)
        feat1 = backbone(dummy_input)
        details.append(f"  - Backbone forward pass output channels: {feat1.shape[1]} (Shape: {list(feat1.shape)})")
        assert len(feat1.shape) == 4, "Backbone output must have 4 dimensions (B, C, H, W)"
        backbone_check = True
        details.append("  [OK] Backbone forward pass checks passed.")

        # 3. Temporal Fusion Module Verification
        details.append("[3/5] Verifying Temporal Fusion adapter module...")
        fusion_module = importlib.import_module("models.fusion")
        FusionClass = find_class_by_base_or_keyword(fusion_module, "Module", "TemporalFusionAdapter")
        
        if not FusionClass:
            raise ImportError("Could not locate Fusion Module class in models/fusion.py")
            
        # Instantiate with backbone output channels
        in_channels = feat1.shape[1]
        try:
            fusion = FusionClass(in_channels=in_channels)
        except TypeError:
            # Fallback for LLMs that did not specify custom constructor channels
            fusion = FusionClass()
            
        feat2 = backbone(torch.randn(2, 3, 128, 128))
        fused = fusion(feat1, feat2)
        details.append(f"  - Fusion adapter output shape: {list(fused.shape)}")
        assert len(fused.shape) == 4, "Fused output must have 4 dimensions (B, C, H, W)"
        fusion_check = True
        details.append("  [OK] Temporal Fusion adapter forward pass checks passed.")

        # 4. Decoder Verification
        details.append("[4/5] Verifying Change Detection Decoder module...")
        decoder_module = importlib.import_module("models.decoder")
        DecoderClass = find_class_by_base_or_keyword(decoder_module, "Module", "ChangeDetectionDecoder")
        
        if not DecoderClass:
            raise ImportError("Could not locate Decoder Module class in models/decoder.py")
            
        fused_channels = fused.shape[1]
        try:
            decoder = DecoderClass(in_channels=fused_channels)
        except TypeError:
            decoder = DecoderClass()
            
        preds = decoder(fused)
        details.append(f"  - Decoder predictions output mask shape: {list(preds.shape)}")
        assert len(preds.shape) == 4, "Predictions must have 4 dimensions (B, 1, H, W)"
        assert preds.shape[1] == 1, "Predictions must have 1 channel (binary change map)"
        decoder_check = True
        details.append("  [OK] Change Decoder forward pass checks passed.")

        # 5. Loss Evaluation Verification
        details.append("[5/5] Verifying BCE-Dice Loss modules evaluation...")
        loss_module = importlib.import_module("training.loss")
        LossClass = find_class_by_base_or_keyword(loss_module, "Loss", "BCEDiceLoss")
        
        if not LossClass:
            # Fallback keyword lookup
            LossClass = find_class_by_base_or_keyword(loss_module, "Module", "BCEDiceLoss")
            
        if not LossClass:
            raise ImportError("Could not locate loss function in training/loss.py")
            
        loss_fn = LossClass()
        dummy_targets = torch.randint(0, 2, (2, 1, 128, 128)).float()
        loss_val = loss_fn(preds, dummy_targets)
        details.append(f"  - Loss evaluation scalar value: {loss_val.item():.4f}")
        assert isinstance(loss_val, torch.Tensor), "Loss output must be a PyTorch Tensor"
        loss_check = True
        details.append("  [OK] Loss evaluation checks passed.")

    except Exception as e:
        details.append(f"[FAIL] Automated verification test failed: {e}")

    # Remove generated path from sys.path
    if generated_project_dir in sys.path:
        sys.path.remove(generated_project_dir)

    return AutomatedTestReport(
        dataset_check=dataset_check,
        backbone_check=backbone_check,
        fusion_check=fusion_check,
        decoder_check=decoder_check,
        loss_check=loss_check,
        details=details
    )
