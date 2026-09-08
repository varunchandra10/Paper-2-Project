import React from 'react';
import { useThemeStore } from '../../store/themeStore';
import type { ThemeMode } from '../../store/themeStore';

interface RuexisLogoProps {
  size?: number;
  className?: string;
  showBackground?: boolean;
  scaleFactor?: number;
  forcedTheme?: ThemeMode;
}

export const RuexisLogo: React.FC<RuexisLogoProps> = ({
  size = 28,
  className = '',
  showBackground = false,
  scaleFactor = 1.25,
  forcedTheme,
}) => {
  const { themeMode: currentTheme } = useThemeStore();
  const activeMode = forcedTheme || currentTheme || 'l1';
  const isDark = activeMode === 'd';

  // Dynamic theme colors for tile background (when showBackground is enabled)
  let tileFill = 'url(#ruexisBgGlowDark)';
  let tileBorder = 'url(#ruexisBorderDark)';
  
  if (activeMode === 'l1') {
    // Claude Warm Light (warm ivory tile)
    tileFill = 'url(#ruexisBgGlowWarm)';
    tileBorder = 'rgba(218, 119, 86, 0.25)';
  } else if (activeMode === 'l2') {
    // Arctic Slate Light (cool sky slate tile)
    tileFill = 'url(#ruexisBgGlowArctic)';
    tileBorder = 'rgba(56, 189, 248, 0.25)';
  } else if (activeMode === 'l3') {
    // Iris Pearl Light (lavender pearl tile)
    tileFill = 'url(#ruexisBgGlowIris)';
    tileBorder = 'rgba(129, 140, 248, 0.25)';
  }

  // Theme-tailored contrast tokens
  const ambientOpacity = isDark ? 0.16 : 0.05;
  const paperStroke = isDark ? '#475569' : '#94a3b8';
  const paperFill = isDark ? 'url(#ruexisPaperGradDark)' : 'url(#ruexisPaperGradLight)';
  const shadowOpacity = isDark ? 0.55 : 0.16;
  const shadowSpread = isDark ? 10 : 6;
  const ideBorder = isDark ? '#38bdf8' : '#0ea5e9';
  const dataStreamGlow = isDark ? 0.45 : 0.65;

  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 512 512" 
      width={size} 
      height={size}
      className={`select-none transition-transform duration-200 ${className}`}
      style={{ overflow: 'visible' }}
    >
      <defs>
        {/* Dark Obsidian Tile Gradient */}
        <radialGradient id="ruexisBgGlowDark" cx="50%" cy="50%" r="65%">
          <stop offset="0%" stopColor="#141c2e"/>
          <stop offset="60%" stopColor="#090d16"/>
          <stop offset="100%" stopColor="#04060a"/>
        </radialGradient>

        {/* L1: Claude Warm Ivory Tile Gradient */}
        <radialGradient id="ruexisBgGlowWarm" cx="50%" cy="50%" r="65%">
          <stop offset="0%" stopColor="#ffffff"/>
          <stop offset="65%" stopColor="#faf9f5"/>
          <stop offset="100%" stopColor="#f4f2ec"/>
        </radialGradient>

        {/* L2: Arctic Slate Ice Tile Gradient */}
        <radialGradient id="ruexisBgGlowArctic" cx="50%" cy="50%" r="65%">
          <stop offset="0%" stopColor="#ffffff"/>
          <stop offset="65%" stopColor="#f8fafc"/>
          <stop offset="100%" stopColor="#eef2f6"/>
        </radialGradient>

        {/* L3: Iris Pearl Lavender Tile Gradient */}
        <radialGradient id="ruexisBgGlowIris" cx="50%" cy="50%" r="65%">
          <stop offset="0%" stopColor="#ffffff"/>
          <stop offset="65%" stopColor="#faf9fd"/>
          <stop offset="100%" stopColor="#f1eff9"/>
        </radialGradient>

        {/* Dark Border Sheen */}
        <linearGradient id="ruexisBorderDark" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.45}/>
          <stop offset="50%" stopColor="#6366f1" stopOpacity={0.2}/>
          <stop offset="100%" stopColor="#f97316" stopOpacity={0.35}/>
        </linearGradient>

        {/* 6 Stage Ribbon Segment Gradients (High Chroma, Universal Contrast) */}
        <linearGradient id="ruexisS1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1"/>
          <stop offset="100%" stopColor="#3b82f6"/>
        </linearGradient>
        <linearGradient id="ruexisS2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3b82f6"/>
          <stop offset="100%" stopColor="#06b6d4"/>
        </linearGradient>
        <linearGradient id="ruexisS3" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#06b6d4"/>
          <stop offset="100%" stopColor="#10b981"/>
        </linearGradient>
        <linearGradient id="ruexisS4" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#10b981"/>
          <stop offset="100%" stopColor="#f59e0b"/>
        </linearGradient>
        <linearGradient id="ruexisS5" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#f59e0b"/>
          <stop offset="100%" stopColor="#ef4444"/>
        </linearGradient>
        <linearGradient id="ruexisS6" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#ef4444"/>
          <stop offset="100%" stopColor="#a855f7"/>
        </linearGradient>

        {/* Paper Gradients */}
        <linearGradient id="ruexisPaperGradDark" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#ffffff"/>
          <stop offset="100%" stopColor="#e2e8f0"/>
        </linearGradient>
        <linearGradient id="ruexisPaperGradLight" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#ffffff"/>
          <stop offset="100%" stopColor="#f1f5f9"/>
        </linearGradient>

        <linearGradient id="ruexisStreamGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.8}/>
          <stop offset="50%" stopColor="#38bdf8" stopOpacity={0.95}/>
          <stop offset="100%" stopColor="#60a5fa" stopOpacity={0.8}/>
        </linearGradient>

        <linearGradient id="ruexisAiGlassGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" stopOpacity={isDark ? 0.35 : 0.30}/>
          <stop offset="50%" stopColor="#0284c7" stopOpacity={isDark ? 0.18 : 0.22}/>
          <stop offset="100%" stopColor="#1e3a8a" stopOpacity={isDark ? 0.45 : 0.40}/>
        </linearGradient>

        <linearGradient id="ruexisIdeBg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0f172a"/>
          <stop offset="100%" stopColor="#090d16"/>
        </linearGradient>

        {/* Glow & Shadow Filters */}
        <filter id="ruexisCoreGlow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="16" result="blur"/>
          <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>

        <filter id="ruexisLaserGlow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="6" result="blur"/>
          <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>

        <filter id="ruexisDropShadow" x="-15%" y="-15%" width="135%" height="135%">
          <feDropShadow dx="0" dy="6" stdDeviation={shadowSpread} floodColor="#000000" floodOpacity={shadowOpacity}/>
        </filter>

        <style>
          {`
            .ruexis-txt-shadow {
              font-family: 'Plus Jakarta Sans', 'JetBrains Mono', 'Segoe UI', system-ui, -apple-system, sans-serif;
              font-size: 8.5px;
              font-weight: 800;
              letter-spacing: 1.8px;
              text-anchor: middle;
              dominant-baseline: central;
              fill: #000000;
              fill-opacity: 0.42;
            }
            .ruexis-txt-word {
              font-family: 'Plus Jakarta Sans', 'JetBrains Mono', 'Segoe UI', system-ui, -apple-system, sans-serif;
              font-size: 8.5px;
              font-weight: 800;
              letter-spacing: 1.8px;
              text-anchor: middle;
              dominant-baseline: central;
              fill: #ffffff;
              fill-opacity: 0.90;
            }
            .ruexis-txt-long {
              font-size: 7.5px;
              letter-spacing: 1.4px;
            }
          `}
        </style>
      </defs>

      {/* Optional Theme-Adaptive Background Squircle */}
      {showBackground && (
        <g>
          <rect x="14" y="14" width="484" height="484" rx="108" ry="108" fill={tileFill}/>
          <rect x="14" y="14" width="484" height="484" rx="108" ry="108" fill="none" stroke={tileBorder} strokeWidth="2.5"/>
        </g>
      )}

      {/* Scalable Emblem Core (Maximized Canvas Fill, Theme Responsive) */}
      <g transform={`translate(256, 256) scale(${scaleFactor}) translate(-256, -256)`}>

        {/* Ambient Backdrop Glow */}
        <circle cx="256" cy="256" r="160" fill="#6366f1" opacity={ambientOpacity} filter="url(#ruexisCoreGlow)"/>
        <circle cx="256" cy="256" r="105" fill="#38bdf8" opacity={ambientOpacity} filter="url(#ruexisCoreGlow)"/>

        {/* ==================== 6-STAGE DYNAMIC RIBBON ==================== */}
        <g filter="url(#ruexisDropShadow)">
          {/* Segment 1: RESEARCH */}
          <path d="M 256 72 L 403 150 L 375 187 L 256 122 Z" fill="url(#ruexisS1)"/>
          <text x="324" y="134" transform="rotate(28, 324, 134)" className="ruexis-txt-shadow">RESEARCH</text>
          <text x="323" y="133" transform="rotate(28, 323, 133)" className="ruexis-txt-word">RESEARCH</text>

          {/* Segment 2: UNDERSTAND */}
          <path d="M 403 150 L 429 286 L 381 275 L 375 187 Z" fill="url(#ruexisS2)"/>
          <text x="398" y="226" transform="rotate(79, 398, 226)" className="ruexis-txt-shadow ruexis-txt-long">UNDERSTAND</text>
          <text x="397" y="225" transform="rotate(79, 397, 225)" className="ruexis-txt-word ruexis-txt-long">UNDERSTAND</text>

          {/* Segment 3: EXTRACT */}
          <path d="M 429 286 L 291 424 L 272 378 L 381 275 Z" fill="url(#ruexisS3)"/>
          <text x="344" y="342" transform="rotate(-45, 344, 342)" className="ruexis-txt-shadow">EXTRACT</text>
          <text x="343" y="341" transform="rotate(-45, 343, 341)" className="ruexis-txt-word">EXTRACT</text>

          {/* Segment 4: EXAMINE */}
          <path d="M 291 424 L 120 372 L 149 332 L 272 378 Z" fill="url(#ruexisS4)"/>
          <text x="209" y="378" transform="rotate(17, 209, 378)" className="ruexis-txt-shadow">EXAMINE</text>
          <text x="208" y="377" transform="rotate(17, 208, 377)" className="ruexis-txt-word">EXAMINE</text>

          {/* Segment 5: IMPLEMENT */}
          <path d="M 120 372 L 90 206 L 137 218 L 149 332 Z" fill="url(#ruexisS5)"/>
          <text x="125" y="283" transform="rotate(-80, 125, 283)" className="ruexis-txt-shadow ruexis-txt-long">IMPLEMENT</text>
          <text x="124" y="282" transform="rotate(-80, 124, 282)" className="ruexis-txt-word ruexis-txt-long">IMPLEMENT</text>

          {/* Segment 6: SYNTHESIZE */}
          <path d="M 90 206 L 256 72 L 256 122 L 137 218 Z" fill="url(#ruexisS6)"/>
          <text x="186" y="156" transform="rotate(-39, 186, 156)" className="ruexis-txt-shadow ruexis-txt-long">SYNTHESIZE</text>
          <text x="185" y="155" transform="rotate(-39, 185, 155)" className="ruexis-txt-word ruexis-txt-long">SYNTHESIZE</text>

          {/* Precision 3D Overlap Shadows */}
          <polygon points="256,72 278,84 274,132 256,122" fill="#000000" opacity="0.25"/>
          <polygon points="403,150 407,170 376,200 375,187" fill="#000000" opacity="0.25"/>
          <polygon points="429,286 408,307 365,290 381,275" fill="#000000" opacity="0.25"/>
          <polygon points="291,424 265,416 254,371 272,378" fill="#000000" opacity="0.25"/>
          <polygon points="120,372 116,347 147,315 149,332" fill="#000000" opacity="0.25"/>
          <polygon points="90,206 115,186 155,204 137,218" fill="#000000" opacity="0.25"/>
        </g>

        {/* ==================== CENTRAL TRANSFORMATION SCENE ==================== */}
        <g id="ruexisCenterTransformation">
          {/* Ambient Platform Glow */}
          <ellipse cx="256" cy="276" rx="98" ry="20" fill="#38bdf8" opacity={isDark ? 0.14 : 0.08} filter="url(#ruexisCoreGlow)"/>

          {/* 1. CYBERNETIC DATA STREAM */}
          <g filter="url(#ruexisLaserGlow)">
            {/* Left Stream: Paper to AI Gateway */}
            <path d="M 218 243 C 230 243, 236 249, 244 251 L 244 261 C 236 263, 230 269, 218 269 Z" fill="url(#ruexisStreamGrad)" opacity={dataStreamGlow}/>
            <path d="M 218 256 C 228 256, 236 256, 244 256" stroke="#ffffff" strokeWidth="1.5" strokeDasharray="3.5,2" opacity="0.9"/>
            <circle cx="228" cy="248" r="2.4" fill="#38bdf8"/>
            <circle cx="236" cy="256" r="2.8" fill="#ffffff"/>
            <circle cx="229" cy="264" r="2.4" fill="#06b6d4"/>

            {/* Right Stream: AI Gateway to Code Terminal */}
            <path d="M 268 251 C 276 249, 284 243, 296 243 L 296 269 C 284 269, 276 263, 268 261 Z" fill="url(#ruexisStreamGrad)" opacity={dataStreamGlow}/>
            <path d="M 268 256 C 276 256, 284 256, 296 256" stroke="#ffffff" strokeWidth="1.5" strokeDasharray="3.5,2" opacity="0.9"/>
            <circle cx="277" cy="248" r="2.4" fill="#38bdf8"/>
            <circle cx="286" cy="256" r="2.8" fill="#ffffff"/>
            <circle cx="279" cy="264" r="2.4" fill="#60a5fa"/>
          </g>

          {/* 2. LEFT: RESEARCH PAPER DOCUMENT */}
          <g filter="url(#ruexisDropShadow)">
            <rect x="175" y="225" width="40" height="58" rx="3.5" fill="#94a3b8" opacity="0.35"/>
            <rect x="179" y="221" width="40" height="58" rx="3.5" fill={paperFill} stroke={paperStroke} strokeWidth="1.2"/>
            <path d="M 209 221 L 219 231 L 209 231 Z" fill="#94a3b8"/>
            <path d="M 209 221 L 219 231 L 209 231 Z" fill="#e2e8f0" opacity="0.8"/>
            <rect x="184" y="227" width="18" height="3.5" rx="1" fill="#3b82f6"/>
            <line x1="184" y1="234" x2="212" y2="234" stroke="#94a3b8" strokeWidth="1.3" strokeLinecap="round"/>
            <line x1="184" y1="239" x2="208" y2="239" stroke="#94a3b8" strokeWidth="1.3" strokeLinecap="round"/>
            <line x1="184" y1="244" x2="213" y2="244" stroke="#94a3b8" strokeWidth="1.3" strokeLinecap="round"/>
            <rect x="185" y="262" width="3" height="9" rx="0.6" fill="#3b82f6"/>
            <rect x="190" y="257" width="3" height="14" rx="0.6" fill="#06b6d4"/>
            <rect x="195" y="253" width="3" height="18" rx="0.6" fill="#10b981"/>
            <line x1="211" y1="257" x2="206" y2="268" stroke="#6366f1" strokeWidth="0.8"/>
            <line x1="211" y1="257" x2="215" y2="268" stroke="#6366f1" strokeWidth="0.8"/>
            <line x1="206" y1="268" x2="215" y2="268" stroke="#6366f1" strokeWidth="0.8"/>
            <circle cx="211" cy="257" r="1.9" fill="#6366f1"/>
            <circle cx="206" cy="268" r="1.9" fill="#6366f1"/>
            <circle cx="215" cy="268" r="1.9" fill="#6366f1"/>
          </g>

          {/* 3. CENTER: VERTICAL 'AI' HOLOGRAPHIC GLASS GATEWAY */}
          <g filter="url(#ruexisDropShadow)">
            <polygon points="244,216 268,207 268,295 244,304" fill="#38bdf8" opacity="0.32" filter="url(#ruexisLaserGlow)"/>
            <polygon points="244,216 268,207 268,295 244,304" fill="url(#ruexisAiGlassGrad)" stroke="#38bdf8" strokeWidth="2"/>
            <polygon points="244,216 250,213 274,204 268,207" fill="#e0f2fe" opacity="0.95"/>
            <line x1="244" y1="216" x2="244" y2="304" stroke="#ffffff" strokeWidth="1.3"/>
            <line x1="268" y1="207" x2="268" y2="295" stroke="#38bdf8" strokeWidth="1.3"/>
            <g filter="url(#ruexisLaserGlow)">
              <path d="M 256 234 L 263.5 251.5 L 260 251.5 L 258.2 247 L 253.8 247 L 252 251.5 L 248.5 251.5 Z M 256 240.2 L 257.3 244.2 L 254.7 244.2 Z" fill="#ffffff"/>
              <rect x="254.2" y="259.5" width="3.6" height="15" rx="0.8" fill="#ffffff"/>
            </g>
          </g>

          {/* 4. RIGHT: THE CODE IDE TERMINAL WINDOW */}
          <g filter="url(#ruexisDropShadow)">
            <rect x="298" y="219" width="46" height="66" rx="6" fill="url(#ruexisIdeBg)" stroke={ideBorder} strokeWidth="1.7"/>
            <line x1="298" y1="231" x2="344" y2="231" stroke="rgba(255, 255, 255, 0.16)" strokeWidth="0.9"/>
            <circle cx="305" cy="225" r="1.6" fill="#ef4444"/>
            <circle cx="310" cy="225" r="1.6" fill="#f59e0b"/>
            <circle cx="315" cy="225" r="1.6" fill="#10b981"/>
            <g filter="url(#ruexisLaserGlow)">
              <path d="M 314 240 L 309 244 L 314 248" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
              <line x1="319" y1="249" x2="323" y2="239" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round"/>
              <path d="M 328 240 L 333 244 L 328 248" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            </g>
            <line x1="305" y1="256" x2="316" y2="256" stroke="#a855f7" strokeWidth="2" strokeLinecap="round"/>
            <line x1="319" y1="256" x2="336" y2="256" stroke="#f97316" strokeWidth="2" strokeLinecap="round"/>
            <line x1="309" y1="263" x2="333" y2="263" stroke="#38bdf8" strokeWidth="1.8" strokeLinecap="round"/>
            <line x1="309" y1="270" x2="328" y2="270" stroke="#10b981" strokeWidth="1.8" strokeLinecap="round"/>
            <rect x="339" y="241" width="10" height="10" rx="2" fill="#0f172a" stroke="#38bdf8" strokeWidth="0.9"/>
            <circle cx="344" cy="246" r="2" fill="#38bdf8"/>
          </g>
        </g>

        {/* Constellation Accent Dots */}
        <circle cx="256" cy="72" r="4.5" fill="#e0e7ff" opacity="0.85"/>
        <circle cx="403" cy="150" r="4.5" fill="#bae6fd" opacity="0.85"/>
        <circle cx="429" cy="286" r="4.5" fill="#a7f3d0" opacity="0.85"/>
        <circle cx="291" cy="424" r="4.5" fill="#fde68a" opacity="0.85"/>
        <circle cx="120" cy="372" r="4.5" fill="#fed7aa" opacity="0.85"/>
        <circle cx="90" cy="206" r="4.5" fill="#f5d0fe" opacity="0.85"/>
      </g>
    </svg>
  );
};
