import torch

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
