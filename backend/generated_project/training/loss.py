import torch
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
