import torch
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
