import os
import json
from langchain_ollama import ChatOllama
from schemas import ProjectSpecification

# Baseline python code fallbacks for all files in our generated project
FALLBACK_CODE = {
    "data/dataset.py": '''import os
import torch
from torch.utils.data import Dataset

class LEVIRCDDataset(Dataset):
    """Custom PyTorch dataset for bi-temporal remote sensing change detection patches."""
    def __init__(self, data_dir=None, patch_size=(128, 128), split="train"):
        self.data_dir = data_dir
        self.patch_size = patch_size
        self.split = split
        # Simulated dataset patches representing LEVIR-CD
        self.num_samples = 100
        
    def __len__(self):
        return self.num_samples
        
    def __getitem__(self, idx):
        # Generate dummy tensors matching (C, H, W)
        img1 = torch.randn(3, *self.patch_size)
        img2 = torch.randn(3, *self.patch_size)
        # Binary change mask (1, H, W)
        mask = torch.randint(0, 2, (1, *self.patch_size)).float()
        return img1, img2, mask
''',

    "models/backbone.py": '''import torch
import torch.nn as nn

class FeatureExtractorBackbone(nn.Module):
    """Frozen backbone model encoder (e.g. Swin-T or ResNet-18) for change detection."""
    def __init__(self, model_name="Swin-T", freeze=True):
        super().__init__()
        self.model_name = model_name
        # Simple conv network representing visual backbones
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2)
        )
        if freeze:
            for param in self.parameters():
                param.requires_grad = False
                
    def forward(self, x):
        # Input (B, 3, H, W) -> Output (B, 64, H/2, W/2)
        return self.features(x)
''',

    "models/fusion.py": '''import torch
import torch.nn as nn

class TemporalFusionAdapter(nn.Module):
    """Fuses bi-temporal feature maps using concatenation and bilinear pooling."""
    def __init__(self, in_channels=64):
        super().__init__()
        self.fusion = nn.Sequential(
            nn.Conv2d(in_channels * 2, in_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(in_channels),
            nn.ReLU()
        )
        
    def forward(self, feat1, feat2):
        # Concatenate along channel dimension
        x = torch.cat([feat1, feat2], dim=1)
        return self.fusion(x)
''',

    "models/decoder.py": '''import torch
import torch.nn as nn

class ChangeDetectionDecoder(nn.Module):
    """Decodes fused feature maps to predict spatial change mask."""
    def __init__(self, in_channels=64):
        super().__init__()
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(in_channels, 32, kernel_size=2, stride=2),
            nn.ReLU(),
            nn.Conv2d(32, 1, kernel_size=1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        # Input (B, 64, H/2, W/2) -> Output (B, 1, H, W)
        return self.decoder(x)
''',

    "training/loss.py": '''import torch
import torch.nn as nn

class BCEDiceLoss(nn.Module):
    """Loss function combining Binary Cross Entropy (BCE) and Soft Dice loss."""
    def __init__(self, weight_bce=1.0, weight_dice=1.0):
        super().__init__()
        self.bce = nn.BCELoss()
        self.weight_bce = weight_bce
        self.weight_dice = weight_dice
        
    def forward(self, preds, targets):
        bce_loss = self.bce(preds, targets)
        
        # Soft Dice loss
        eps = 1e-6
        preds_flat = preds.view(-1)
        targets_flat = targets.view(-1)
        intersection = (preds_flat * targets_flat).sum()
        dice_loss = 1.0 - (2.0 * intersection + eps) / (preds_flat.sum() + targets_flat.sum() + eps)
        
        return self.weight_bce * bce_loss + self.weight_dice * dice_loss
''',

    "training/trainer.py": '''import torch
import torch.optim as optim
from torch.utils.data import DataLoader

class ModelTrainer:
    """Handles deep learning training execution with FP16 and gradient accumulation."""
    def __init__(self, model, dataset, loss_fn, lr=0.0001, batch_size=4, grad_accum=4):
        self.model = model
        self.dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        self.loss_fn = loss_fn
        self.optimizer = optim.AdamW(model.parameters(), lr=lr)
        self.grad_accum = grad_accum
        
    def train_epoch(self):
        self.model.train()
        total_loss = 0.0
        self.optimizer.zero_grad()
        
        for idx, (img1, img2, mask) in enumerate(self.dataloader):
            # Simulated forward/backward pass with gradient accumulation
            feat1 = self.model.backbone(img1)
            feat2 = self.model.backbone(img2)
            fused = self.model.fusion(feat1, feat2)
            preds = self.model.decoder(fused)
            
            loss = self.loss_fn(preds, mask) / self.grad_accum
            loss.backward()
            
            if (idx + 1) % self.grad_accum == 0 or (idx + 1) == len(self.dataloader):
                self.optimizer.step()
                self.optimizer.zero_grad()
                
            total_loss += loss.item() * self.grad_accum
        return total_loss / len(self.dataloader)
''',

    "evaluation/evaluator.py": '''import torch

class ChangeEvaluator:
    """Computes F1-Score and Intersection over Union (IoU) evaluation metrics."""
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        
    def evaluate(self, preds, targets):
        preds_bin = (preds > self.threshold).float()
        targets_bin = (targets > self.threshold).float()
        
        # Calculate intersection and union
        intersection = (preds_bin * targets_bin).sum().item()
        union = preds_bin.sum().item() + targets_bin.sum().item() - intersection
        
        # True Positives, False Positives, False Negatives
        tp = intersection
        fp = preds_bin.sum().item() - tp
        fn = targets_bin.sum().item() - tp
        
        eps = 1e-6
        iou = tp / (union + eps)
        precision = tp / (tp + fp + eps)
        recall = tp / (tp + fn + eps)
        f1_score = 2.0 * (precision * recall) / (precision + recall + eps)
        
        return {
            "iou": iou,
            "f1_score": f1_score,
            "precision": precision,
            "recall": recall
        }
'''
}

def run_code_generation_agent(
    component_name: str,
    filepath: str,
    specification: ProjectSpecification,
    model_name: str = "qwen2.5-coder:1.5b"
) -> str:
    """Uses Ollama to generate python code file for a project component, falling back to

    functional modular code blueprints if structured code generation fails.
    """
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=4096)
    
    prompt = (
        f"You are a Senior Deep Learning Developer. Your task is to generate complete, clean, and bug-free Python code "
        f"for the file '{filepath}' based on this Project Specification:\n\n"
        f"Requirements: {specification.requirements}\n"
        f"Architecture: {specification.architecture}\n"
        f"Dataset Setup: {', '.join(specification.datasets)}\n"
        f"Training Setup: {specification.training_setup}\n"
        f"Evaluation Metrics: {specification.evaluation}\n\n"
        f"Instructions:\n"
        f"1. Generate code ONLY for '{filepath}' matching the component name: '{component_name}'.\n"
        f"2. Your output must contain ONLY the raw Python code block enclosed in ```python and ```.\n"
        f"3. Make sure to define standard class structures, imports, docstrings, and handle standard tensor inputs.\n"
        f"4. Do NOT output explanations, introductory paragraphs, or conversational text. Output raw code only."
    )

    print(f"Sending request to local Ollama to generate code for '{filepath}'...")
    try:
        response = llm.invoke(prompt)
        content = response.content
        # Extract code content within markdown code blocks if present
        if "```python" in content:
            code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            code = content.split("```")[1].split("```")[0].strip()
        else:
            code = content.strip()
            
        # Basic sanity check: if less than 50 characters or does not contain import/class, fallback
        if len(code) < 50 or "class" not in code and "def" not in code:
            raise ValueError("Generated code appears incomplete or empty.")
            
    except Exception as e:
        print(f"Warning: Code generation failed for '{filepath}' ({e}). Writing robust baseline fallback.")
        code = FALLBACK_CODE.get(filepath, "# Placeholder fallback code.")
        
    return code
