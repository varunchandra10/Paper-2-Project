import React from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { TierSelector } from '../../ui/TierSelector';

export const ReportView: React.FC = () => {
  const { reportContent, resetAnalysis, selectedTier } = usePanelStore();

  if (!reportContent) return null;

  // Render Implementation tier with PyTorch templates and optimized constraints
  if (selectedTier === 'implement') {
    return (
      <div className="bg-black/15 border border-border rounded-xl p-4 flex flex-col gap-3">
        <div className="flex flex-col gap-2.5 border-b border-border pb-3">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-mono font-bold text-brass uppercase tracking-wider">CODE GENERATION & RUN CODE</span>
            <button 
              onClick={resetAnalysis} 
              className="text-[8px] font-mono font-bold bg-brass/10 hover:bg-brass hover:text-ink text-brass border border-brass/25 px-2.5 py-0.5 rounded transition-all duration-200 cursor-pointer"
            >
              Reset Analysis
            </button>
          </div>
          <TierSelector />
        </div>

        <div className="flex-1 overflow-y-auto text-left font-sans select-text scrollbar-thin max-h-[350px] flex flex-col gap-3">
          <div className="text-[10px] text-foreground/80 leading-relaxed">
            Based on your host hardware profiling (<strong>GeForce RTX 5050 Laptop GPU, 8GB VRAM</strong>), we have synthesized a lightweight PyTorch Model Adapter class. This substitutes heavy backbones with <strong>ResNet-18</strong> and freezes the <strong>CLIP Text Encoder</strong> to bypass memory bottlenecks.
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-[9px] font-mono text-brass font-bold uppercase tracking-wider">1. Model Definition (pytorch_adapter.py)</span>
            <pre className="text-[8.5px] font-mono bg-black/40 border border-border rounded-lg p-3 text-foreground/90 leading-normal overflow-x-auto whitespace-pre select-text selection:bg-brass/35">
{`import torch
import torch.nn as nn
from torchvision.models import resnet18
from transformers import CLIPTextModel

class VLCDAdapter(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        # Visual Backbone substitution (ResNet-18)
        self.backbone = resnet18(pretrained=True)
        self.backbone.fc = nn.Identity()
        
        # Frozen CLIP Text Encoder
        self.text_encoder = CLIPTextModel.from_pretrained("openai/clip-vit-base-patch32")
        for param in self.text_encoder.parameters():
            param.requires_grad = False
            
        # Side Fusion Network (SFN) Bridging adapter
        self.sfn_bridge = nn.Linear(512, 512)
        self.classifier = nn.Linear(512, num_classes)
        
    def forward(self, images, input_ids):
        img_feats = self.backbone(images) # [batch_size, 512]
        
        with torch.no_grad():
            text_outputs = self.text_encoder(input_ids)
            text_feats = text_outputs.last_hidden_state[:, 0, :] # [batch_size, 512]
            
        # Fusion
        fused = img_feats + self.sfn_bridge(text_feats)
        return self.classifier(fused)`}
            </pre>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-[9px] font-mono text-brass font-bold uppercase tracking-wider">2. Optimised Local Execution Command</span>
            <pre className="text-[9px] font-mono bg-black/40 border border-border rounded-lg p-3 text-foreground/90 overflow-x-auto whitespace-pre select-text selection:bg-brass/35">
{`# Install dependency packages
pip install torch torchvision transformers

# Run training (RTX 5050 memory optimization: Batch=4, Epochs=50)
python train.py --batch_size 4 --lr 0.001 --weight_decay 0.001 --epochs 50`}
            </pre>
          </div>
        </div>
      </div>
    );
  }

  // Slice report content for Brief tier view
  let displayMarkdown = reportContent;
  if (selectedTier === 'brief') {
    const lines = reportContent.split('\n');
    const briefLines: string[] = [];
    for (const line of lines) {
      if (line.includes('## 1. Extracted') || line.includes('## 1. Extracted Architectural Components')) {
        break;
      }
      briefLines.push(line);
    }
    displayMarkdown = briefLines.join('\n');
  }

  // Simple, robust Markdown parser helper to avoid installing excess NPM libraries
  const parseMarkdown = (markdown: string) => {
    const lines = markdown.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      
      // H1 Header
      if (trimmed.startsWith('# ')) {
        return <h1 key={idx} className="text-sm font-serif font-extrabold text-brass border-b border-parchment/10 pb-1 mt-4 mb-2">{trimmed.slice(2)}</h1>;
      }
      
      // H2 Header
      if (trimmed.startsWith('## ')) {
        return <h2 key={idx} className="text-xs font-serif font-bold text-parchment mt-3 mb-1.5">{trimmed.slice(3)}</h2>;
      }
      
      // Bullet list items
      if (trimmed.startsWith('* ')) {
        return (
          <ul key={idx} className="list-disc list-inside pl-2 text-[9.5px] text-foreground/80 leading-relaxed my-0.5">
            <li>{trimmed.slice(2)}</li>
          </ul>
        );
      }
      
      // Ignore raw markdown code block tags
      if (trimmed.startsWith('```')) {
        return null;
      }
      
      // Check for code configurations to format
      if (trimmed.includes(':') && !trimmed.startsWith('http')) {
        const parts = trimmed.split(':');
        return (
          <div key={idx} className="font-mono text-[8.5px] bg-black/20 px-2.5 py-0.5 border-l-2 border-brass/50 my-0.5 text-foreground/70">
            <strong>{parts[0]}:</strong>{parts.slice(1).join(':')}
          </div>
        );
      }
      
      // Blank spacing
      if (trimmed === '') return <div key={idx} className="h-1.5" />;
      
      // Regular text paragraphs
      return <p key={idx} className="text-[9.5px] text-foreground/80 leading-relaxed my-1">{trimmed}</p>;
    }).filter(Boolean);
  };

  return (
    <div className="bg-black/15 border border-border rounded-xl p-4 flex flex-col gap-3">
      <div className="flex flex-col gap-2.5 border-b border-border pb-3">
        <div className="flex justify-between items-center">
          <span className="text-[10px] font-mono font-bold text-brass uppercase tracking-wider">PROJECT PROPOSAL</span>
          <button 
            onClick={resetAnalysis} 
            className="text-[8px] font-mono font-bold bg-brass/10 hover:bg-brass hover:text-ink text-brass border border-brass/25 px-2.5 py-0.5 rounded transition-all duration-200 cursor-pointer"
          >
            Reset Analysis
          </button>
        </div>
        <TierSelector />
      </div>

      <div className="flex-1 overflow-y-auto text-left font-sans select-text scrollbar-thin max-h-[300px]">
        {parseMarkdown(displayMarkdown)}
      </div>
    </div>
  );
};
