# Phase 4 Complete End-to-End Ingestion & RAG Scorecard Report

This report summarizes the end-to-end integration checks across Routing, Merging, Validation, and pgvector local database storage for all 29 papers.

## 📊 Aggregate Pipeline Statistics
- **Total Papers Processed**: 29
- **Valid Ingestions**: 29 (100.0%)
- **Validation Blocked Ingestions**: 0
- **Total Semantic Chunks Stored**: 2604
- **Total Pipeline Duration**: 167.41 seconds

## 🔍 Grounded Evidence Reranker Verification
**Test Query**: `What optimizer and learning rate were used?`

| Rank | Score | Chunk ID | Page | Section | Content Snippet |
| :---: | :---: | :--- | :---: | :--- | :--- |
| 1 | 5/5 | `paper_13_chunk_030` | 1 | 'B. Implementation Details' | During the training process, we compute the feature distillation loss for each backbone layer and use the AdamW optimizer. The learning rate is 2 × 10... |
| 2 | 5/5 | `paper_12_chunk_045` | 1 | 'D. Loss Function' | All experiments were conducted using PyTorch 1.11.0 on an NVIDIA TITAN RTX Graphics Processing Unit. For training, the stochastic gradient descent (SG... |
| 3 | 5/5 | `paper_8_chunk_036` | 1 | 'C. Details' | We conducted our training using eight A100 (80G) GPUs, employing the Adam optimizer with a weight decay of 0.05. The image resolution was set to 448 ×... |

## 📋 Combined Ingestion Ledger
| Paper ID | Filename | Status | Chunks | Tables | Equations | Algorithms |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `paper_10` | [10].pdf | Valid | 26 | 5 | 0 | 0 |
| `paper_11` | [11].pdf | Valid | 82 | 3 | 14 | 0 |
| `paper_12` | [12].pdf | Valid | 117 | 12 | 16 | 1 |
| `paper_13` | [13].pdf | Valid | 77 | 2 | 20 | 1 |
| `paper_14` | [14].pdf | Valid | 36 | 4 | 7 | 0 |
| `paper_15` | [15].pdf | Valid | 89 | 3 | 20 | 0 |
| `paper_16` | [16].pdf | Valid | 58 | 11 | 1 | 0 |
| `paper_17` | [17].pdf | Valid | 124 | 7 | 21 | 0 |
| `paper_18` | [18].pdf | Valid | 188 | 43 | 24 | 0 |
| `paper_19` | [19].pdf | Valid | 236 | 9 | 11 | 0 |
| `paper_1` | [1].pdf | Valid | 97 | 5 | 28 | 1 |
| `paper_20` | [20].pdf | Valid | 74 | 9 | 2 | 0 |
| `paper_21` | [21].pdf | Valid | 71 | 5 | 15 | 0 |
| `paper_22` | [22].pdf | Valid | 72 | 2 | 10 | 0 |
| `paper_23` | [23].pdf | Valid | 98 | 5 | 8 | 0 |
| `paper_24` | [24].pdf | Valid | 37 | 2 | 5 | 0 |
| `paper_25` | [25].pdf | Valid | 17 | 1 | 0 | 0 |
| `paper_26` | [26].pdf | Valid | 114 | 4 | 30 | 1 |
| `paper_27` | [27].pdf | Valid | 67 | 7 | 7 | 0 |
| `paper_28` | [28].pdf | Valid | 101 | 8 | 8 | 0 |
| `paper_29` | [29].pdf | Valid | 100 | 5 | 20 | 1 |
| `paper_2` | [2].pdf | Valid | 85 | 8 | 15 | 1 |
| `paper_3` | [3].pdf | Valid | 122 | 7 | 33 | 0 |
| `paper_4` | [4].pdf | Valid | 77 | 4 | 12 | 0 |
| `paper_5` | [5].pdf | Valid | 99 | 1 | 29 | 0 |
| `paper_6` | [6].pdf | Valid | 73 | 3 | 3 | 0 |
| `paper_7` | [7].pdf | Valid | 98 | 5 | 23 | 0 |
| `paper_8` | [8].pdf | Valid | 83 | 1 | 11 | 0 |
| `paper_9` | [9].pdf | Valid | 86 | 1 | 20 | 0 |