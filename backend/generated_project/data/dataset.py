import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
from sklearn.model_selection import train_test_split
from PIL import Image
import numpy as np
from skimage.metrics import dice_coefficient

class LEVIRCDataset(torch.utils.data.Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.images = []
        self.masks = []

        for img_name in os.listdir(os.path.join(root_dir, 'images')):
            img_path = os.path.join(root_dir, 'images', img_name)
            mask_path = os.path.join(root_dir, 'masks', img_name.replace('.png', '.png'))
            if os.path.isfile(img_path) and os.path.isfile(mask_path):
                self.images.append(img_path)
                self.masks.append(mask_path)

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]
        mask_path = self.masks[idx]

        img = Image.open(img_path).convert('RGB')
        mask = Image.open(mask_path).convert('L')

        if self.transform:
            img = self.transform(img)
            mask = self.transform(mask)

        return img, mask

class BiTemporalImagePatchExtractor(nn.Module):
    def __init__(self, patch_size=128):
        super(BiTemporalImagePatchExtractor, self).__init__()
        self.patch_size = patch_size

    def forward(self, images):
        patches = []
        for img in images:
            img = img.unsqueeze(0)
            for i in range(img.shape[2] - self.patch_size + 1):
                for j in range(img.shape[3] - self.patch_size + 1):
                    patch = img[:, :, i:i+self.patch_size, j:j+self.patch_size]
                    patches.append(patch)
        patches = torch.stack(patches, dim=0)
        return patches

class AdaptiveFusionNetwork(nn.Module):
    def __init__(self, num_channels=3):
        super(AdaptiveFusionNetwork, self).__init__()
        self.conv1 = nn.Conv2d(num_channels, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.fc = nn.Linear(256, 1)

    def forward(self, patches):
        x = self.conv1(patches)
        x = nn.functional.relu(x)
        x = self.conv2(x)
        x = nn.functional.relu(x)
        x = self.conv3(x)
        x = nn.functional.relu(x)
        x = x.mean(dim=(2, 3))
        x = self.fc(x)
        return x

class ChangeDecoder(nn.Module):
    def __init__(self, num_channels=3):
        super(ChangeDecoder, self).__init__()
        self.conv1 = nn.Conv2d(num_channels, 128, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(128, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 32, kernel_size=3, padding=1)
        self.conv4 = nn.Conv2d(32, 1, kernel_size=1, padding=0)

    def forward(self, x):
        x = self.conv1(x)
        x = nn.functional.relu(x)
        x = self.conv2(x)
        x = nn.functional.relu(x)
        x = self.conv3(x)
        x = nn.functional.relu(x)
        x = self.conv4(x)
        return x

class ChangeDetectionModel(nn.Module):
    def __init__(self, patch_size=128):
        super(ChangeDetectionModel, self).__init__()
        self.patch_extractor = BiTemporalImagePatchExtractor(patch_size)
        self.fusion_network = AdaptiveFusionNetwork()
        self.decoder = ChangeDecoder()

    def forward(self, images):
        patches = self.patch_extractor(images)
        features = self.fusion_network(patches)
        change_mask = self.decoder(features)
        return change_mask

def train(model, dataloader, optimizer, criterion, device):
    model.train()
    running_loss = 0.0
    for images, masks in dataloader:
        images, masks = images.to(device), masks.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, masks)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    return running_loss / len(dataloader)

def evaluate(model, dataloader, criterion, device):
    model.eval()
    with torch.no_grad():
        running_loss = 0.0
        for images, masks in dataloader:
            images, masks = images.to(device), masks.to(device)
            outputs = model(images)
            loss = criterion(outputs, masks)
            running_loss += loss.item()
        return running_loss / len(dataloader)

def main():
    root_dir = 'data/LEVIR-CD'
    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    dataset = LEVIRCDataset(root_dir, transform)
    train_dataset, val_dataset = train_test_split(dataset, test_size=0.2, random_state=42)

    train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = ChangeDetectionModel(patch_size=128).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=0.0001)
    criterion = nn.BCEWithLogitsLoss() + nn.DiceLoss()

    best_val_iou = 0.0
    best_model = None

    for epoch in range(10):
        train_loss = train(model, train_loader, optimizer, criterion, device)
        val_loss = evaluate(model, val_loader, criterion, device)

        print(f'Epoch {epoch+1}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}')

        if val_loss < best_val_iou:
            best_val_iou = val_loss
            best_model = model

    if best_model:
        torch.save(best_model.state_dict(), 'best_model.pth')

if __name__ == '__main__':
    main()