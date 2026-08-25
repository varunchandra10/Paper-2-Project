# Paper-to-Project: Phase 1–7 Corpus-Wide Code Synthesis Report
**Generated:** 2026-08-25 01:17:08
**Model:** `qwen2.5-coder:1.5b`
**GPU:** NVIDIA GeForce RTX 5050 Laptop GPU (8.0 GB VRAM) | **RAM:** 23.6 GB
**Total Running Time:** 10129.86 seconds
**Papers Run:** 29 | **Success:** 24 | **Errors:** 5

## Per-Paper Results Summary
| # | PDF | Status | Time(s) | Comps | VRAM Est | Feasibility | Adaptations | Code Files | Title |
|---|-----|--------|---------|-------|----------|-------------|-------------|------------|-------|
| 1 | [1].pdf | OK | 446.34 | 2 | 3.4 GB | FEASIBLE | 0 | 5 | A Novel Change Detection Method Based on Visual La |
| 2 | [2].pdf | OK | 234.13 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | A New Learning Paradigm for Foundation Model-Based |
| 3 | [3].pdf | OK | 243.45 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | ChangeCLIP: Remote sensing change detection with m |
| 4 | [4].pdf | OK | 439.48 | 1 | 3.4 GB | FEASIBLE | 0 | 10 | Change Knowledge-Guided Vision-Language Remote Sen |
| 5 | [5].pdf | OK | 465.15 | 2 | 3.4 GB | FEASIBLE | 0 | 5 | MDS-Net: An Image-Text Enhanced Multimodal Network |
| 6 | [7].pdf | OK | 1115.83 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | RFHP-CD: A Prompt-Driven Fine-Tuning Framework of  |
| 7 | [9].pdf | OK | 230.02 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | SemiCD-VL: Visual-Language Model Guidance Makes Be |
| 8 | [10].pdf | OK | 178.3 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | FULLY CONVOLUTIONAL SIAMESE NETWORKS FOR CHANGE DE |
| 9 | [11].pdf | OK | 442.78 | 2 | 3.4 GB | FEASIBLE | 0 | 5 | An eﬃcient change detection method for disaster-aﬀ |
| 10 | [12].pdf | OK | 292.46 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | Bi-Temporal Feature Relational Distillation for On |
| 11 | [13].pdf | OK | 229.87 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | Burden-Free Distillation From Foundation Model |
| 12 | [14].pdf | OK | 430.02 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | CDxLSTM: Boosting Remote Sensing Change Detection  |
| 13 | [15].pdf | OK | 453.19 | 2 | 3.4 GB | FEASIBLE | 0 | 5 | LORA: LOW-RANK ADAPTATION OF LARGE LANGUAGE MODELS |
| 14 | [17].pdf | OK | 220.55 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | A Copula-Guided In-Model Interpretable Neural Netw |
| 15 | [18].pdf | OK | 282.91 | 1 | 3.4 GB | FEASIBLE_WITH_MODIFICATION | 3 | 5 | Real-Time Detection of Forest Fires Using FireNet- |
| 16 | [20].pdf | OK | 204.56 | 6 | 3.4 GB | FEASIBLE_WITH_MODIFICATION | 0 | 5 | XChange: An Explainable Dynamic Convolutional Netw |
| 17 | [21].pdf | OK | 199.57 | 4 | 3.4 GB | FEASIBLE | 0 | 5 | Adversarial Mask-Guided Generation for Multi-Tempo |
| 18 | [22].pdf | OK | 196.53 | 4 | 3.4 GB | FEASIBLE_WITH_MODIFICATION | 0 | 5 | IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING |
| 19 | [23].pdf | OK | 1753.04 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | Science of Remote Sensing |
| 20 | [24].pdf | OK | 168.02 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | Manifold Learning and Deep Generative Networks |
| 21 | [25].pdf | OK | 389.68 | 2 | 3.4 GB | FEASIBLE | 0 | 5 | Prototype-oriented Unsupervised Change Detection |
| 22 | [26].pdf | OK | 186.43 | 1 | 3.4 GB | FEASIBLE | 0 | 5 | Article A Novel Change Detection Method for Natura |
| 23 | [27].pdf | OK | 406.7 | 2 | 3.4 GB | FEASIBLE | 0 | 5 | An onboard automatic change detection system for d |
| 24 | [29].pdf | OK | 420.61 | 2 | 3.4 GB | FEASIBLE | 0 | 5 | Deep Learning for Change Detection in Remote Sensi |

## Per-Paper Code Generation Blueprints

### [1] [1].pdf — A Novel Change Detection Method Based on Visual Language from High-Resolution Re

- **Time:** 446.34s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── custom_patches_loader.py
├── LEVIR-CD_dataset.py
├── RemoteCLIP_image_encoder.py
models
├── Swin_Transformer.py
├── RemoteCLIP.py
training
├── optimizer.py
├── loss_functions.py
├── gradient_accumulation.py
evaluation
├── metrics.py
├── checkpointer.py
├── utils.py
configs
├── project_config.yaml
└── training_config.yaml
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the Swin Transformer (RFN) and RemoteCLIP Image Encoder models. |
| training | Contains the training setup, optimizer, loss functions, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [2] [2].pdf — A New Learning Paradigm for Foundation Model-Based Remote-Sensing Change Detecti

- **Time:** 234.13s | **Feasibility:** FEASIBLE
- **Architecture:** The FireNet-CNN model architecture is a sequence of convolutional layers, pooling layers, dropout layers, and batch normalization layers. The model is designed to detect forest fires. The model takes an input image and outputs fire patterns.
- **System Requirements:** The project requires the following libraries and tools: PyTorch, PyMuPDF, CUDA drivers version 11.0, and VRAM limits of 8GB. The project also requires a GPU with at least 8GB VRAM to run the training process.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── LEVIR-CD
│   ├── train
│   │   ├── val
│   │   └── test
│   └── patch_sizes
│       ├── 128x128
│       └── 256x256
├── models
│   └── FireNet-CNN
├── training
│   ├── DataLoader
│   │   ├── Dataset
│   │   │   ├── Model
│   │   │   │   ├── LossFunction
│   │   │   │   │   ├── EvaluationMetric
│   │   │   │   │   ├── Checkpoint
│   │   │   │   │   └── TrainingLoop
│   └── evaluation
│       ├── convergence_validation_frequency
│       └── F1-Score_IoU
├── configs
│   └── config.yaml
└── utils
    ├── batch_size
    ├── learning_rate
    ├── gradient_accumulation
    └── fp16_usage
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset and patch crop sizes. |
| models | Contains the FireNet-CNN model architecture. |
| training | Contains the DataLoader, Dataset, Model, LossFunction, EvaluationMetric, Checkpoint, and TrainingLoop. |
| evaluation | Contains the convergence validation frequency and F1-Score / IoU calculations. |
| configs | Contains the configuration files for the project. |

---
### [3] [3].pdf — ChangeCLIP: Remote sensing change detection with multimodal vision-language repr

- **Time:** 243.45s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── custom_patches_loader.py
│   └── __init__.py
├── models
│   ├── __init__.py
│   ├── firenet_cnn.py
│   └── __init__.py
├── training
│   ├── __init__.py
│   ├── optimizer.py
│   ├── loss.py
│   ├── gradient_accumulation.py
│   └── __init__.py
├── evaluation
│   ├── __init__.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   ├── checkpointer.py
│   └── __init__.py
├── configs
│   ├── __init__.py
│   ├── project_config.py
│   └── __init__.py
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN model. |
| training | Contains the training setup, optimizer, loss, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [4] [4].pdf — Change Knowledge-Guided Vision-Language Remote Sensing Change Detection

- **Time:** 439.48s | **Feasibility:** FEASIBLE
- **Architecture:** The FireNet-CNN model is a specialized Convolutional Neural Network (CNN) designed for detecting forest fires. The model consists of three convolutional layers, each with a different number of filters and kernel size. The model uses max pooling to reduce spatial dimensions and dropout to prevent overfitting. The model uses ReLU activation function and batch normalization to stabilize the training process. The model is trained for 100 epochs with a learning rate of 0.001 and a batch size of 32. The model is validated using a validation split of 0.2 and early stopping is used to prevent overfitting. The model is saved using checkpoints to save the best model during training.
- **System Requirements:** The project requires the following libraries and tools: PyTorch, PyMuPDF, CUDA drivers version 11.0, and VRAM limits of 8GB. The project also requires a GPU with at least 8GB VRAM to run the training process.

**ASCII Project Structure Layout (Day 29):**
```text
project/
├── data/
│   └── dataset.py
├── models/
│   ├── backbone.py
│   ├── fusion.py
│   └── decoder.py
├── training/
│   ├── loss.py
│   └── trainer.py
├── evaluation/
│   └── evaluator.py
├── configs/
│   └── config.json
├── requirements.txt
└── README.md
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data/dataset.py | Custom PyTorch Dataset class parsing bi-temporal image pairs and change masks for LEVIR-CD. |
| models/backbone.py | Utility to load visual backbone encoders (Swin/ResNet) and extract high-level feature maps. |
| models/fusion.py | Implements Side Fusion Networks or adapter modules to integrate temporal features. |
| models/decoder.py | Decodes fused features into spatial binary change predictions mask. |
| training/loss.py | Custom loss function implementations combining Binary Cross Entropy (BCE) and Dice Loss. |
| training/trainer.py | FP16 training executor with gradient accumulation steps and validation logic. |
| evaluation/evaluator.py | Batch evaluation loops computing IoU and F1-Score metrics. |
| configs/config.json | Refinement config parameters registry (e.g. batch size 4, gradient accumulation 4). |
| requirements.txt | Package dependency specification tree file. |
| README.md | Technical architecture description, usage scripts guide, and spec tree overview. |

---
### [5] [5].pdf — MDS-Net: An Image-Text Enhanced Multimodal Network for Remote Sensing Change Det

- **Time:** 465.15s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── custom_patches_loader.py
├── LEVIR-CD_dataset.py
├── RemoteCLIP_image_encoder.py
models
├── Swin_Transformer.py
├── RemoteCLIP.py
training
├── optimizer.py
├── loss_functions.py
├── gradient_accumulation.py
evaluation
├── metrics.py
├── checkpointer.py
├── utils.py
configs
├── project_config.yaml
└── training_config.yaml
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the Swin Transformer (RFN) and RemoteCLIP Image Encoder models. |
| training | Contains the training setup, optimizer, loss functions, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [6] [7].pdf — RFHP-CD: A Prompt-Driven Fine-Tuning Framework of Remote Sensing Foundation Mode

- **Time:** 1115.83s | **Feasibility:** FEASIBLE
- **Architecture:** The FireNet-CNN model is a specialized Convolutional Neural Network (CNN) designed for detecting forest fires. The model consists of three convolutional layers, each with a different number of filters, and a max pooling layer. The model uses ReLU activation function and batch normalization. The model is trained for 100 epochs with a learning rate of 0.001 and a batch size of 32. The model is validated using a validation split of 0.2 and early stopping is used to prevent overfitting. The model is saved to models/FireNet-CNN and loaded from models/FireNet-CNN. The model is exported to models/FireNet-CNN and predicted from models/FireNet-CNN. The model is trained from models/FireNet-CNN and tested from models/FireNet-CNN. The model is validated from models/FireNet-CNN.
- **System Requirements:** The project requires the following libraries and tools: PyTorch, PyMuPDF, CUDA drivers version 11.0, and VRAM limits of 8GB. The project also requires a GPU with at least RTX 5050 Laptop GPU for training.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── images
│   ├── train
│   │   ├── ...
│   │   └── val
│   └── test
├── labels
│   ├── train
│   │   ├── ...
│   │   └── val
│   └── test
├── metadata
│   ├── train
│   │   ├── ...
│   │   └── val
│   └── test
└── utils
    ├── data_loader.py
    ├── image_folder.py
    ├── tensor_dataset.py
    ├── dataloader.py
    ├── loss_function.py
    ├── evaluation_metric.py
    ├── checkpoint.py
    ├── model_checkpoint.py
    ├── sfn.py
    ├── bridging_module.py
    ├── decoder.py
    ├── training_loop.py
    └── utils.py
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the raw data for the project, including images and labels. |
| models | Contains the trained and exported models for the project. |
| training | Contains the training scripts and configurations for the project. |
| evaluation | Contains the evaluation scripts and configurations for the project. |
| configs | Contains the configuration files for the project. |

---
### [7] [9].pdf — SemiCD-VL: Visual-Language Model Guidance Makes Better Semi-Supervised Change De

- **Time:** 230.02s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── custom_patches_loader.py
│   └── __init__.py
├── models
│   ├── __init__.py
│   ├── firenet_cnn.py
│   └── __init__.py
├── training
│   ├── __init__.py
│   ├── optimizer.py
│   ├── loss.py
│   ├── gradient_accumulation.py
│   └── __init__.py
├── evaluation
│   ├── __init__.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   ├── checkpointer.py
│   └── __init__.py
├── configs
│   ├── __init__.py
│   ├── project_config.py
│   └── __init__.py
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN model. |
| training | Contains the training setup, optimizer, loss, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [8] [10].pdf — FULLY CONVOLUTIONAL SIAMESE NETWORKS FOR CHANGE DETECTION

- **Time:** 178.3s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── custom_patches_loader.py
│   └── __init__.py
├── models
│   ├── __init__.py
│   ├── firenet_cnn.py
│   └── __init__.py
├── training
│   ├── __init__.py
│   ├── optimizer.py
│   ├── loss.py
│   ├── gradient_accumulation.py
│   └── __init__.py
├── evaluation
│   ├── __init__.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   ├── checkpointer.py
│   └── __init__.py
├── configs
│   ├── __init__.py
│   ├── project_config.py
│   └── __init__.py
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN model. |
| training | Contains the training setup, optimizer, loss, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [9] [11].pdf — An eﬃcient change detection method for disaster-aﬀected buildings based on a lig

- **Time:** 442.78s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── custom_patches_loader.py
├── LEVIR-CD_dataset.py
├── RemoteCLIP_image_encoder.py
models
├── Swin_Transformer.py
├── RemoteCLIP.py
training
├── optimizer.py
├── loss_functions.py
├── gradient_accumulation.py
evaluation
├── metrics.py
├── checkpointer.py
├── utils.py
configs
├── project_config.yaml
└── training_config.yaml
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the Swin Transformer (RFN) and RemoteCLIP Image Encoder models. |
| training | Contains the training setup, optimizer, loss functions, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [10] [12].pdf — Bi-Temporal Feature Relational Distillation for On-Board Lightweight Change Dete

- **Time:** 292.46s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── custom_patches_loader.py
│   └── __init__.py
├── models
│   ├── __init__.py
│   ├── firenet_cnn.py
│   └── __init__.py
├── training
│   ├── __init__.py
│   ├── optimizer.py
│   ├── loss.py
│   ├── gradient_accumulation.py
│   └── __init__.py
├── evaluation
│   ├── __init__.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   ├── checkpointer.py
│   └── __init__.py
├── configs
│   ├── __init__.py
│   ├── project_config.py
│   └── __init__.py
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN model. |
| training | Contains the training setup, optimizer, loss, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [11] [13].pdf — Burden-Free Distillation From Foundation Model

- **Time:** 229.87s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── custom_patches_loader.py
│   └── __init__.py
├── models
│   ├── __init__.py
│   ├── firenet_cnn.py
│   └── __init__.py
├── training
│   ├── __init__.py
│   ├── optimizer.py
│   ├── loss.py
│   ├── gradient_accumulation.py
│   └── __init__.py
├── evaluation
│   ├── __init__.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   ├── checkpointer.py
│   └── __init__.py
├── configs
│   ├── __init__.py
│   ├── project_config.py
│   └── __init__.py
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN model. |
| training | Contains the training setup, optimizer, loss, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [12] [14].pdf — CDxLSTM: Boosting Remote Sensing Change Detection With Extended Long Short-Term 

- **Time:** 430.02s | **Feasibility:** FEASIBLE
- **Architecture:** The FireNet-CNN model architecture is a sequence of convolutional layers, pooling layers, dropout layers, and activation layers. The fusion and decoder layers are designed to combine the features extracted by the convolutional layers and the features extracted by the fusion and decoder layers. The fusion and decoder layers are designed to produce a single output that can be used for classification or regression.
- **System Requirements:** The project requires the following libraries and tools: PyTorch, PyMuPDF, CUDA drivers version 11.0, and VRAM limits of 8GB. The project also requires a GPU with at least 8GB VRAM to run the training process.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── LEVIR-CD
│   ├── train
│   │   ├── images
│   │   │   └── labels
│   │   └── val
│   │       ├── images
│   │       │   └── labels
│   │       └── test
│   │           ├── images
│   │           │   └── labels
│   │           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │   └── labels
│           └── val
│           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │   └── labels
│           └── val
│           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │   └── labels
│           └── val
│           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │   └── labels
│           └── val
│           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │   └── labels
│           └── val
│           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │   └── labels
│           └── val
│           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │   └── labels
│           └── val
│           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │   └── labels
│           └── val
│           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │   └── labels
│           └── val
│           └── test
│   └── train
│       ├── images
│       │   └── labels
│       └── val
│           ├── images
│           │   └── labels
│           └── test
│       └── train
│           ├── images
│           │
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset files. |
| models | Contains the FireNet-CNN model architecture files. |
| training | Contains the training script files. |
| evaluation | Contains the evaluation script files. |
| configs | Contains the configuration files for the project. |

---
### [13] [15].pdf — LORA: LOW-RANK ADAPTATION OF LARGE LANGUAGE MODELS

- **Time:** 453.19s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── custom_patches_loader.py
├── LEVIR-CD_dataset.py
├── RemoteCLIP_image_encoder.py
models
├── Swin_Transformer.py
├── RemoteCLIP.py
training
├── optimizer.py
├── loss_functions.py
├── gradient_accumulation.py
evaluation
├── metrics.py
├── checkpointer.py
├── utils.py
configs
├── project_config.yaml
└── training_config.yaml
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the Swin Transformer (RFN) and RemoteCLIP Image Encoder models. |
| training | Contains the training setup, optimizer, loss functions, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [14] [17].pdf — A Copula-Guided In-Model Interpretable Neural Network for Change Detection in He

- **Time:** 220.55s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── custom_patches_loader.py
│   └── __init__.py
├── models
│   ├── __init__.py
│   ├── firenet_cnn.py
│   └── __init__.py
├── training
│   ├── __init__.py
│   ├── optimizer.py
│   ├── loss.py
│   ├── gradient_accumulation.py
│   └── __init__.py
├── evaluation
│   ├── __init__.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   ├── checkpointer.py
│   └── __init__.py
├── configs
│   ├── __init__.py
│   ├── project_config.py
│   └── __init__.py
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN model. |
| training | Contains the training setup, optimizer, loss, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [15] [18].pdf — Real-Time Detection of Forest Fires Using FireNet-CNN and Explainable AI Techniq

- **Time:** 282.91s | **Feasibility:** FEASIBLE_WITH_MODIFICATION
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── __main__.py
│   ├── __pycache__
│   │   └── ...
│   ├── levir_cd_dataset.py
│   │   └── ...
│   └── utils.py
│       └── ...
├── models
│   ├── __init__.py
│   ├── __main__.py
│   ├── __pycache__
│   │   └── ...
│   ├── visual_backbone.py
│   │   └── ...
│   ├── adaptive_fusion_network.py
│   │   └── ...
│   ├── change_decoder.py
│   │   └── ...
│   └── binary_output_change_mask.py
│       └── ...
├── training
│   ├── __init__.py
│   ├── __main__.py
│   ├── __pycache__
│   │   └── ...
│   ├── optimizer.py
│   │   └── ...
│   ├── base_learning_rate.py
│   │   └── ...
│   ├── loss.py
│   │   └── ...
│   ├── mixed_precision.py
│   │   └── ...
│   ├── gradient_accumulation.py
│   │   └── ...
│   └── checkpointer.py
│       └── ...
├── evaluation
│   ├── __init__.py
│   ├── __main__.py
│   ├── __pycache__
│   │   └── ...
│   ├── validation_frequency.py
│   │   └── ...
│   ├── primary_metrics.py
│   │   └── ...
│   └── evaluation_utils.py
│       └── ...
├── configs
│   ├── __init__.py
│   ├── __main__.py
│   ├── __pycache__
│   │   └── ...
│   ├── project_config.py
│   │   └── ...
│   └── ...
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the visual backbones feature extraction, adaptive fusion network, change decoder, and binary output change mask models. |
| training | Contains the optimizer, base learning rate, loss, mixed precision, gradient accumulation, and checkpointer utilities. |
| evaluation | Contains the validation frequency, primary metrics, and evaluation utilities. |
| configs | Contains the project configuration files. |

---
### [16] [20].pdf — XChange: An Explainable Dynamic Convolutional Network for Unsupervised Change De

- **Time:** 204.56s | **Feasibility:** FEASIBLE_WITH_MODIFICATION
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── custom_patches_loader.py
├── ...
models
├── FireNet-CNN.py
├── ...
├── Inception-V3.py
├── ...
├── VGG16.py
├── ...
├── VGG19.py
├── CAE.py
├── ...
├── Kullback-Leibler.py
├── ...
training
├── optimizer.py
├── base_learning_rate.py
├── loss.py
├── mixed_precision.py
├── gradient_accumulation.py
├── BATCH_SIZE.py
├── FREEZE_BACKBONE.py
├── ...
└── ...
evaluation
├── validation_frequency.py
├── primary_metrics.py
├── checkpointer.py
├── ...
└── ...
configs
├── project_config.yaml
├── ...
└── ...

```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN, Inception V3, VGG16, VGG19, CAE, Kullback–Leibler (KL) divergence measure. |
| training | Contains the optimizer, base learning rate, loss, mixed precision, gradient accumulation, BATCH_SIZE, FREEZE_BACKBONE, and other training utilities. |
| evaluation | Contains the validation frequency, primary metrics, checkpointer, and other evaluation utilities. |
| configs | Contains the project configuration files. |

---
### [17] [21].pdf — Adversarial Mask-Guided Generation for Multi-Temporal Change Detection in Remote

- **Time:** 199.57s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── custom_patches_loader.py
│   └── ...
├── models
│   ├── firenet_cnn.py
│   ├── inception_v3.py
│   ├── vgg16.py
│   └── vgg19.py
├── training
│   ├── optimizer.py
│   ├── loss.py
│   ├── mixed_precision.py
│   ├── gradient_accumulation.py
│   ├── checkpointer.py
│   └── ...
├── evaluation
│   ├── metrics.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   └── checkpointer.py
├── configs
│   ├── ...
└── ...
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN, Inception V3, VGG16, VGG19 models. |
| training | Contains the training setup, optimizer, loss, mixed precision, gradient accumulation, and checkpointer utilities. |
| evaluation | Contains the evaluation metrics, validation frequency, primary metrics, and checkpointer utilities. |
| configs | Contains the configuration files for the project. |

---
### [18] [22].pdf — IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING, VOL. 63, 2025 4417812 BiSAM-

- **Time:** 196.53s | **Feasibility:** FEASIBLE_WITH_MODIFICATION
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── custom_patches_loader.py
│   └── __init__.py
├── models
│   ├── __init__.py
│   ├── firenet_cnn.py
│   ├── sam2.py
│   ├── bidirectional_frame_sequence_construction_with_adaptive_interpolation.py
│   └── cross_sequence_change_verification_totc_cscv.py
├── training
│   ├── __init__.py
│   ├── optimizer.py
│   ├── loss.py
│   ├── mixed_precision.py
│   ├── gradient_accumulation.py
│   └── checkpointer.py
├── evaluation
│   ├── __init__.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   └── checkpointer.py
├── configs
│   ├── __init__.py
│   ├── firenet_cnn_config.py
│   ├── sam2_config.py
│   ├── bidirectional_frame_sequence_construction_with_adaptive_interpolation_config.py
│   └── cross_sequence_change_verification_totc_cscv_config.py
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN, SAM2, Bidirectional Frame Sequence Construction with Adaptive Interpolation, Cross-Sequence Change Verification (TOTC-CSCV) models. |
| training | Contains the training setup, optimizer, loss, mixed precision, gradient accumulation, and checkpointer utilities. |
| evaluation | Contains the evaluation metrics, validation frequency, primary metrics, and checkpointer utilities. |
| configs | Contains the configuration files for the project. |

---
### [19] [23].pdf — Science of Remote Sensing

- **Time:** 1753.04s | **Feasibility:** FEASIBLE
- **Architecture:** The FireNet-CNN model architecture is a specialized Convolutional Neural Network designed for detecting forest fires. The model consists of 3 convolutional layers, each with 64 filters, followed by max pooling, dropout, and batch normalization. The model is trained using the Adam optimizer with a learning rate of 0.001 and 100 epochs. The model is validated using 20% of the data and trained for 1.97 hours. The model is exported to a file and imported from a file. The model is trained using the training dataset, evaluated on the validation dataset, and deployed for real-world applications.
- **System Requirements:** The project requires the following libraries and dependencies: PyTorch, PyMuPDF, CUDA drivers version 11.0, and VRAM limits of 8GB. The project also requires the following components: FireNet-CNN, DataLoader, ImageDataset, DataAugmentation, Normalization, Model, Optimizer, LossFunction, Trainer, ModelCheckpoint, TensorBoard, EarlyStopping, ModelExport, and ModelImport. The project also requires the following datasets: LEVIR-CD train/val/test divisions, patch crop sizes of 128x128, and dataloader properties such as batch size, gradient accumulation, and FP16 usage. The project also requires the following training setup: epochs, loss functions, learning rate, and optimizer. The project also requires the following evaluation: convergence validation frequency, F1-Score / IoU calculations, and checkpoint save locations. The project also requires the following assumptions: hardware limits of RTX 5050 Laptop GPU, 8GB VRAM, and dataset path availability. The project also requires the following adaptations: hyperparameter overrides and trace origins.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── train
│   ├── images
│   └── masks
├── val
│   ├── images
│   └── masks
└── test
    ├── images
    └── masks
models
├── firenet_cnn.py
├── dataloader.py
├── image_dataset.py
├── data_augmentation.py
├── normalization.py
├── model.py
├── optimizer.py
├── loss_function.py
├── trainer.py
├── model_checkpoint.py
├── tensorboard.py
├── early_stopping.py
├── model_export.py
├── model_import.py
training
├── train.py
└── validation.py
└── evaluation.py
evaluation
├── f1_score.py
├── iou.py
└── evaluation_utils.py
configs
├── firenet_cnn_config.py
├── dataloader_config.py
├── image_dataset_config.py
├── data_augmentation_config.py
├── normalization_config.py
├── model_config.py
├── optimizer_config.py
├── loss_function_config.py
├── trainer_config.py
├── model_checkpoint_config.py
├── tensorboard_config.py
├── early_stopping_config.py
├── model_export_config.py
├── model_import_config.py
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Data preprocessing and loading utilities |
| models | Model architecture and implementation |
| training | Training setup and execution |
| evaluation | Evaluation metrics and results |
| configs | Configuration files and settings |

---
### [20] [24].pdf — Manifold Learning and Deep Generative Networks

- **Time:** 168.02s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── custom_patches_loader.py
│   └── __init__.py
├── models
│   ├── __init__.py
│   ├── firenet_cnn.py
│   └── __init__.py
├── training
│   ├── __init__.py
│   ├── optimizer.py
│   ├── loss.py
│   ├── gradient_accumulation.py
│   └── __init__.py
├── evaluation
│   ├── __init__.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   ├── checkpointer.py
│   └── __init__.py
├── configs
│   ├── __init__.py
│   ├── project_config.py
│   └── __init__.py
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN model. |
| training | Contains the training setup, optimizer, loss, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [21] [25].pdf — Prototype-oriented Unsupervised Change Detection

- **Time:** 389.68s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── custom_patches_loader.py
├── LEVIR-CD_dataset.py
├── RemoteCLIP_image_encoder.py
models
├── Swin_Transformer.py
├── RemoteCLIP.py
training
├── optimizer.py
├── loss_functions.py
├── gradient_accumulation.py
evaluation
├── metrics.py
├── checkpointer.py
├── utils.py
configs
├── project_config.yaml
└── training_config.yaml
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the Swin Transformer (RFN) and RemoteCLIP Image Encoder models. |
| training | Contains the training setup, optimizer, loss functions, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [22] [26].pdf — Article A Novel Change Detection Method for Natural Disasters

- **Time:** 186.43s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
```
├── data
│   ├── __init__.py
│   ├── custom_patches_loader.py
│   └── __init__.py
├── models
│   ├── __init__.py
│   ├── firenet_cnn.py
│   └── __init__.py
├── training
│   ├── __init__.py
│   ├── optimizer.py
│   ├── loss.py
│   ├── gradient_accumulation.py
│   └── __init__.py
├── evaluation
│   ├── __init__.py
│   ├── validation_frequency.py
│   ├── primary_metrics.py
│   ├── checkpointer.py
│   └── __init__.py
├── configs
│   ├── __init__.py
│   ├── project_config.py
│   └── __init__.py
```
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the FireNet-CNN model. |
| training | Contains the training setup, optimizer, loss, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [23] [27].pdf — An onboard automatic change detection system for disaster monitoring

- **Time:** 406.7s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── custom_patches_loader.py
├── LEVIR-CD_dataset.py
├── RemoteCLIP_image_encoder.py
models
├── Swin_Transformer.py
├── RemoteCLIP.py
training
├── optimizer.py
├── loss_functions.py
├── gradient_accumulation.py
evaluation
├── metrics.py
├── checkpointer.py
├── utils.py
configs
├── project_config.yaml
└── training_config.yaml
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the Swin Transformer (RFN) and RemoteCLIP Image Encoder models. |
| training | Contains the training setup, optimizer, loss functions, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---
### [24] [29].pdf — Deep Learning for Change Detection in Remote Sensing Images: Comprehensive Revie

- **Time:** 420.61s | **Feasibility:** FEASIBLE
- **Architecture:** Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.
- **System Requirements:** Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.

**ASCII Project Structure Layout (Day 29):**
```text
data
├── custom_patches_loader.py
├── LEVIR-CD_dataset.py
├── RemoteCLIP_image_encoder.py
models
├── Swin_Transformer.py
├── RemoteCLIP.py
training
├── optimizer.py
├── loss_functions.py
├── gradient_accumulation.py
evaluation
├── metrics.py
├── checkpointer.py
├── utils.py
configs
├── project_config.yaml
└── training_config.yaml
```

**Generated Python Modules Map (Day 30):**
| Generated Relative Path | Functional Module Summary |
|-------------------------|--------------------------|
| data | Contains the LEVIR-CD dataset custom patches loader. |
| models | Contains the Swin Transformer (RFN) and RemoteCLIP Image Encoder models. |
| training | Contains the training setup, optimizer, loss functions, and gradient accumulation. |
| evaluation | Contains the evaluation metrics, checkpointer, and utilities. |
| configs | Contains the project configuration files. |

---