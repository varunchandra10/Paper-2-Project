import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import autocast, GradScaler
from torch.utils.data import DataLoader
from torchvision import transforms
from sklearn.metrics import f1_score, IoU
import psutil
import numpy as np

class FusionModel(nn.Module):
    def __init__(self):
        super(FusionModel, self).__init__()
        # Define your model architecture here
        # Example: self.backbone = ResNet18(pretrained=True)
        # self.fusion_layer = nn.Linear(512, 128)
        # self.change_decoder = nn.Linear(128, 1)

    def forward(self, x):
        # Implement your forward pass here
        # Example: x = self.backbone(x)
        # x = self.fusion_layer(x)
        # x = self.change_decoder(x)
        return x

class CustomPatchLoader:
    def __init__(self, dataset, patch_size=128):
        self.dataset = dataset
        self.patch_size = patch_size

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        image, label = self.dataset[idx]
        patches = self.extract_patches(image, self.patch_size)
        return patches, label

    def extract_patches(self, image, patch_size):
        patches = []
        for i in range(0, image.shape[0] - patch_size + 1, patch_size):
            for j in range(0, image.shape[1] - patch_size + 1, patch_size):
                patch = image[i:i+patch_size, j:j+patch_size]
                patches.append(patch)
        return patches

def train(model, dataloader, optimizer, scaler, device, val_loader, num_epochs=10):
    for epoch in range(num_epochs):
        model.train()
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)
            with autocast():
                outputs = model(images)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()

        if epoch % 1 == 0:
            model.eval()
            with torch.no_grad():
                val_loss = 0.0
                val_f1 = 0.0
                val_iou = 0.0
                for images, labels in val_loader:
                    images, labels = images.to(device), labels.to(device)
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item()
                    pred = torch.sigmoid(outputs).round().long()
                    f1 = f1_score(labels.cpu(), pred.cpu(), average='macro')
                    iou = IoU(labels.cpu(), pred.cpu(), average='macro')
                    val_f1 += f1
                    val_iou += iou
                val_loss /= len(val_loader)
                val_f1 /= len(val_loader)
                val_iou /= len(val_loader)
                print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {val_loss:.4f}, F1-Score: {val_f1:.4f}, IoU: {val_iou:.4f}')

def evaluate(model, dataloader, device):
    model.eval()
    with torch.no_grad():
        val_loss = 0.0
        val_f1 = 0.0
        val_iou = 0.0
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item()
            pred = torch.sigmoid(outputs).round().long()
            f1 = f1_score(labels.cpu(), pred.cpu(), average='macro')
            iou = IoU(labels.cpu(), pred.cpu(), average='macro')
            val_f1 += f1
            val_iou += iou
        val_loss /= len(val_loader)
        val_f1 /= len(val_loader)
        val_iou /= len(val_loader)
        print(f'Validation Loss: {val_loss:.4f}, F1-Score: {val_f1:.4f}, IoU: {val_iou:.4f}')

def main():
    # Load your dataset
    dataset = LEVIRCDataset()
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(dataset, batch_size=32, shuffle=False)

    # Initialize model, optimizer, and scaler
    model = FusionModel()
    optimizer = optim.AdamW(model.parameters(), lr=0.0001)
    scaler = GradScaler()

    # Define loss function
    criterion = nn.BCEWithLogitsLoss()

    # Train the model
    train(model, dataloader, optimizer, scaler, device, val_loader, num_epochs=10)

    # Evaluate the model
    evaluate(model, val_loader, device)

if __name__ == "__main__":
    main()