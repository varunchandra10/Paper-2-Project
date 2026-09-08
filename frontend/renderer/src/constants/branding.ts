/**
 * Centralized Application Branding & Identity Constants
 *
 * Defines the official application name, assistant titles,
 * mascot quips, and notices, eradicating legacy branding strings.
 */

export const APP_BRANDING = {
  NAME: 'REUXIS AI',
  FULL_NAME: 'REUXIS AI — Research, Understand, Extract, eXecute, Implement, Synthesize',
  TAGLINE: 'Research • Understand • Extract • eXecute • Implement • Synthesize',
  ASSISTANT_NAME: 'REUXIS AI Assistant',
  AGENT_NAME: 'REUXIS AI ReACT Agent',
  DEFAULT_TITLE: 'REUXIS AI',
  FAVICON_ALT: 'REUXIS AI Logo',
  MASCOT_DEFAULT_NAME: 'Mr. Nerdy',
  LATENCY_NOTICE: 'REUXIS AI runs on free and local models; apologies for any latency',
  WELCOME_HEADING: 'Welcome to REUXIS AI',
  WELCOME_SUBHEADING: 'Upload an academic paper PDF to automatically extract architectures, audit VRAM, and synthesize verified PyTorch code.',
  
  // Mascot companion quips
  QUIPS: [
    "100% Local Ollama or Free Cloud LPUs, zero unexpected bills 💅",
    "Parsed a 40-page arXiv paper in seconds with PyMuPDF 🚀",
    "AST Auto-healing and dummy forward pass just validated your tensors ⚡",
    "Feed me any research PDF from Vision to NLP, I won't choke 🧠",
    "PyTorch models aligned, dimension-verified, and ready to train 🔥"
  ]
} as const;
