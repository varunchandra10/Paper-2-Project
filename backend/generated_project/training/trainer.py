import torch
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
