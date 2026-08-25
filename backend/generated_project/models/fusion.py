import torch
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
