import torch
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
