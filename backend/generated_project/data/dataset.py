import os
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
