/**
 * Universal Multi-Domain Hyperparameter & Pipeline Defaults
 *
 * Eliminates domain-specific hardcoded assumptions (e.g. Swin-T, LEVIR-CD, BCEDiceLoss)
 * providing scientific, domain-agnostic fallback configurations for any research paper.
 */

export interface HyperparameterConfig {
  learning_rate: string;
  batch_size: string;
  optimizer: string;
  loss: string;
  epochs: string;
  model: string;
  dataset: string;
  scheduler: string;
  input_size: string;
  augmentation: string;
  hardware: string;
}

export const UNIVERSAL_DEFAULT_HYPERPARAMETERS: HyperparameterConfig = {
  learning_rate: '0.0001',
  batch_size: '32',
  optimizer: 'AdamW',
  loss: 'CrossEntropyLoss',
  epochs: '50',
  model: 'NeuralNetworkModel',
  dataset: 'BenchmarkDataset',
  scheduler: 'CosineAnnealingLR',
  input_size: 'Dynamic',
  augmentation: 'Standard Normalization',
  hardware: 'NVIDIA CUDA GPU'
};

export interface MilestoneMeta {
  index: number;
  name: string;
  description: string;
  successMessage: string;
}

export const PIPELINE_MILESTONES: MilestoneMeta[] = [
  {
    index: 0,
    name: 'Paper Ingestion',
    description: 'PyMuPDF block layout extraction & high-fidelity text stream compilation',
    successMessage: 'Ingested page structure, metadata, and extracted bounding boxes.'
  },
  {
    index: 1,
    name: 'Method Decomposition',
    description: 'Decomposes model architecture into component graph topology',
    successMessage: 'Decomposed model layers, tensor dataflows, and sub-module connections.'
  },
  {
    index: 2,
    name: 'Parameters Refinement',
    description: 'Extracts explicit training hyperparameters and resolves parameter gaps',
    successMessage: 'Extracted training parameters and verified hyperparameter completeness.'
  },
  {
    index: 3,
    name: 'Hardware Feasibility',
    description: 'Audits parameter footprint and calculates CUDA GPU VRAM requirements',
    successMessage: 'Feasibility passed: memory footprint verified against GPU profile.'
  },
  {
    index: 4,
    name: 'Blueprint Synthesis',
    description: 'Generates milestone sequence and prepares implementation blueprint',
    successMessage: 'Synthesis complete: modular architecture blueprint and proposal ready.'
  }
];

export const getUniversalDefaultParams = (): HyperparameterConfig => ({
  ...UNIVERSAL_DEFAULT_HYPERPARAMETERS
});
