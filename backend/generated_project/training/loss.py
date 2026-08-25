import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.cuda.amp import autocast, GradScaler
from sklearn.metrics import f1_score, IoU

class Loss(nn.Module):
    def __init__(self, ignore_index=255):
        super(Loss, self).__init__()
        self.ignore_index = ignore_index

    def forward(self, outputs, targets):
        # Convert targets to long for BCE loss
        targets = targets.long()
        
        # Apply ignore index to targets
        targets[targets == self.ignore_index] = 0
        
        # Calculate BCE loss
        bce_loss = F.binary_cross_entropy(outputs, targets, reduction='mean')
        
        # Calculate Dice loss
        dice_loss = 1 - F.binary_cross_entropy_with_logits(outputs, targets, reduction='mean')
        
        # Combine BCE and Dice loss
        loss = bce_loss + dice_loss
        
        return loss