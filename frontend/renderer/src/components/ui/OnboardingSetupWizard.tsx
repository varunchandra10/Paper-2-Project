import React, { useState, useEffect } from 'react';
import { usePanelStore } from '../../store/panelStore';
import { type AvatarId, MascotWaistUpCard } from '../mascot/MascotCompanion';
import {
  IconUser,
  IconMail,
  IconArrowRight,
  IconBack,
  IconAlertCircle,
  IconCheck,
  IconTerminal,
  IconHardware,
  IconKey,
  IconFolder,
  IconShield,
  IconLoader,
  IconRefresh,
} from './Icons';

const MASCOT_LIST: AvatarId[] = ['mr-nerdy', 'ms-nerdy', 'mr-nerd', 'ms-nerd'];

export const OnboardingSetupWizard: React.FC = () => {
  const {
    userId,
    completeOnboardingWizard,
    verifyApiKey,
    checkOllamaStatus,
  } = usePanelStore();

  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);

  // Step 1: Identity & Subscription
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(true);

  // Step 2: System & Hardware Permissions
  const [projectPath, setProjectPath] = useState('');
  const [allowCodeExecution, setAllowCodeExecution] = useState(true);
  const [detectHardware, setDetectHardware] = useState(true);

  // Step 3: Inference Strategy (BYOK vs. Local Ollama)
  const [ollamaEnabled, setOllamaEnabled] = useState(true);
  const [ollamaLink] = useState('http://localhost:11434');
  const [ollamaStatus, setOllamaStatus] = useState<{ running: boolean; message: string; count: number } | null>(null);
  const [isCheckingOllama, setIsCheckingOllama] = useState(false);

  const [groqApiKey, setGroqApiKey] = useState('');
  const [groqStatus, setGroqStatus] = useState<{ loading: boolean; valid?: boolean; message?: string } | null>(null);

  const [openrouterApiKey, setOpenrouterApiKey] = useState('');
  const [openrouterStatus, setOpenrouterStatus] = useState<{ loading: boolean; valid?: boolean; message?: string } | null>(null);

  // Step 4: Device & Companion
  const [rememberDevice, setRememberDevice] = useState(true);
  const [avatarId, setAvatarId] = useState<AvatarId>('mr-nerdy');

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Auto-detect Ollama when entering Step 3
  useEffect(() => {
    if (currentStep === 3) {
      handleCheckOllama();
    }
  }, [currentStep]);

  // If user is already authenticated/configured, do not render modal
  if (userId) return null;

  const handleCheckOllama = async () => {
    setIsCheckingOllama(true);
    try {
      const res = await checkOllamaStatus();
      setOllamaStatus({
        running: res.running,
        message: res.message,
        count: res.count,
      });
      setOllamaEnabled(res.running);
    } catch {
      setOllamaStatus({ running: false, message: 'Ollama daemon not detected', count: 0 });
      setOllamaEnabled(false);
    } finally {
      setIsCheckingOllama(false);
    }
  };

  const handleVerifyGroq = async () => {
    if (!groqApiKey.trim()) {
      setGroqStatus({ loading: false, valid: false, message: 'Please enter a Groq API key' });
      return;
    }
    setGroqStatus({ loading: true });
    const res = await verifyApiKey('groq', groqApiKey.trim());
    setGroqStatus({
      loading: false,
      valid: res.valid,
      message: res.message,
    });
  };

  const handleVerifyOpenRouter = async () => {
    if (!openrouterApiKey.trim()) {
      setOpenrouterStatus({ loading: false, valid: false, message: 'Please enter an OpenRouter API key' });
      return;
    }
    setOpenrouterStatus({ loading: true });
    const res = await verifyApiKey('openrouter', openrouterApiKey.trim());
    setOpenrouterStatus({
      loading: false,
      valid: res.valid,
      message: res.message,
    });
  };

  const handleNextStep = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);

    if (currentStep === 1) {
      if (!username.trim() || !email.trim()) {
        setError('Please enter your full name and valid email address.');
        return;
      }
      if (!email.includes('@') || !email.includes('.')) {
        setError('Please enter a valid email format (e.g. user@example.com).');
        return;
      }
      setCurrentStep(2);
    } else if (currentStep === 2) {
      setCurrentStep(3);
    } else if (currentStep === 3) {
      setCurrentStep(4);
    }
  };

  const handleFinishWizard = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await completeOnboardingWizard({
        username: username.trim(),
        email: email.trim(),
        subscribed,
        projectPath: projectPath.trim() || null,
        allowCodeExecution,
        detectHardware,
        ollamaEnabled,
        ollamaLink: ollamaLink.trim() || null,
        groqApiKey: groqApiKey.trim() || null,
        openrouterApiKey: openrouterApiKey.trim() || null,
        rememberDevice,
        avatarId,
      });
    } catch (err: any) {
      setError(err?.message || 'Failed to finalize setup. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade-in font-sans">
      <div className="w-full max-w-[560px] bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300">
        
        {/* ── 1. HEADER: Terminal Logo & Wizard Title ── */}
        <div className="px-5 py-3 border-b border-[var(--border-color)] bg-[var(--bg-base)]/60 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)] flex items-center justify-center shadow-xs">
              <IconTerminal className="text-sm" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-mono font-bold tracking-tight text-[var(--text-main)]">
                Setup & Permissions Wizard
              </span>
              <span className="text-[10px] text-[var(--text-muted)] font-mono">
                Step {currentStep} of 4
              </span>
            </div>
          </div>
          <span className="w-2.5 h-2.5 rounded-full bg-[var(--accent)] shadow-[0_0_8px_var(--accent)] animate-pulse" />
        </div>

        {/* ── 2. RUEXIS AI LOGO & WELCOME BANNER ── */}
        <div className="px-5 py-3.5 border-b border-[var(--border-color)] bg-[var(--accent-subtle)]/20 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-hover)] text-white flex items-center justify-center font-black text-sm shadow-md shrink-0">
            R
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-bold text-[var(--text-main)] flex items-center gap-1.5">
              Welcome to RUEXIS AI
              <span className="text-[9px] font-mono px-1.5 py-0.2 bg-[var(--accent-subtle)] border border-[var(--accent-border)] text-[var(--accent)] rounded font-semibold">
                v2.0
              </span>
            </span>
            <span className="text-[11px] text-[var(--text-muted)] truncate">
              Autonomous Research-to-Code Engineering Platform
            </span>
          </div>
        </div>

        {/* ── 3. COMPACT STEPPER: Step 1 | Step 2 | Step 3 | Step 4 ── */}
        <div className="grid grid-cols-4 border-b border-[var(--border-color)] bg-[var(--bg-base)]/40 text-[10px] font-mono font-medium">
          {[
            { step: 1, label: 'Identity' },
            { step: 2, label: 'Permissions' },
            { step: 3, label: 'Inference' },
            { step: 4, label: 'Avatar' },
          ].map((item) => (
            <div
              key={item.step}
              className={`py-2 px-1 text-center flex items-center justify-center gap-1 border-r last:border-r-0 border-[var(--border-color)] transition-colors ${
                currentStep === item.step
                  ? 'text-[var(--accent)] bg-[var(--accent-subtle)]/50 font-bold'
                  : currentStep > item.step
                  ? 'text-[var(--text-main)] font-semibold'
                  : 'text-[var(--text-muted)] opacity-60'
              }`}
            >
              <span
                className={`w-4 h-4 rounded-full text-[9px] flex items-center justify-center shrink-0 ${
                  currentStep === item.step
                    ? 'bg-[var(--accent)] text-white'
                    : currentStep > item.step
                    ? 'bg-emerald-500/20 text-emerald-400 font-bold'
                    : 'bg-[var(--bg-card)] border border-[var(--border-color)]'
                }`}
              >
                {currentStep > item.step ? '✓' : item.step}
              </span>
              <span className="truncate">Step {item.step}</span>
            </div>
          ))}
        </div>

        {/* ── 4. ERROR MESSAGE NOTIFICATION ── */}
        {error && (
          <div className="mx-5 mt-4 p-2.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2 animate-fade-in">
            <IconAlertCircle className="text-sm shrink-0" />
            <span className="truncate">{error}</span>
          </div>
        )}

        {/* ── 5. STEP CONTENT AREA ── */}
        <div className="p-5 flex-1 overflow-y-auto max-h-[380px]">

          {/* ══════════ STEP 1: DEVELOPER / RESEARCHER IDENTITY ══════════ */}
          {currentStep === 1 && (
            <form onSubmit={handleNextStep} className="space-y-4">
              <div>
                <span className="text-xs font-bold text-[var(--text-main)] uppercase tracking-wider block mb-1">
                  Developer / Researcher Identity
                </span>
                <p className="text-[11px] text-[var(--text-muted)]">
                  Your credentials personalize your local workspace and sync to the developer registry.
                </p>
              </div>

              {/* Full Name */}
              <div className="space-y-1">
                <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">
                  Full Name / Developer Handle *
                </label>
                <div className="relative">
                  <IconUser className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. Varun Chandra"
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-sans"
                    autoFocus
                  />
                </div>
              </div>

              {/* Email Address */}
              <div className="space-y-1">
                <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">
                  Work / Research Email Address *
                </label>
                <div className="relative">
                  <IconMail className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. researcher@domain.com"
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-sans"
                  />
                </div>
              </div>

              {/* Subscribe Checkbox */}
              <label className="flex items-center gap-2.5 p-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)]/60 cursor-pointer hover:border-[var(--accent-border)] transition-colors select-none">
                <input
                  type="checkbox"
                  checked={subscribed}
                  onChange={(e) => setSubscribed(e.target.checked)}
                  className="w-4 h-4 rounded text-[var(--accent)] border-[var(--border-color)] focus:ring-0 cursor-pointer"
                />
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-[var(--text-main)]">
                    Subscribe to latest updates & release notes
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)]">
                    Receive notifications on new model adapters and benchmarking tools.
                  </span>
                </div>
              </label>

              {/* Step 1 Actions */}
              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  className="px-5 py-2 bg-[var(--accent)] hover:opacity-90 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 transition-all shadow-md active:scale-95 cursor-pointer"
                >
                  <span>Next</span>
                  <IconArrowRight className="text-xs" />
                </button>
              </div>
            </form>
          )}

          {/* ══════════ STEP 2: SYSTEM & HARDWARE PERMISSIONS ══════════ */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div>
                <span className="text-xs font-bold text-[var(--text-main)] uppercase tracking-wider block mb-1">
                  System & Hardware Permissions
                </span>
                <p className="text-[11px] text-[var(--text-muted)]">
                  Configure local file system workspace access and hardware execution boundaries.
                </p>
              </div>

              {/* Workspace Directory */}
              <div className="space-y-1">
                <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">
                  Workspace Project Directory (for project)
                </label>
                <div className="relative">
                  <IconFolder className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                  <input
                    type="text"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                    placeholder="Default: Local repository root"
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-mono"
                  />
                </div>
              </div>

              {/* Permission Checkbox 1: Code Execution Sandbox */}
              <label className="flex items-start gap-2.5 p-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)]/60 cursor-pointer hover:border-[var(--accent-border)] transition-colors select-none">
                <input
                  type="checkbox"
                  checked={allowCodeExecution}
                  onChange={(e) => setAllowCodeExecution(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded text-[var(--accent)] border-[var(--border-color)] focus:ring-0 cursor-pointer"
                />
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-[var(--text-main)] flex items-center gap-1.5">
                    <IconShield className="text-[var(--accent)] text-xs" />
                    Hardware sandbox code execution
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)] leading-tight mt-0.5">
                    Allows the ReACT agent to run sandboxed Python code locally in isolated subprocesses.
                  </span>
                </div>
              </label>

              {/* Permission Checkbox 2: Hardware VRAM & Memory Detection */}
              <label className="flex items-start gap-2.5 p-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)]/60 cursor-pointer hover:border-[var(--accent-border)] transition-colors select-none">
                <input
                  type="checkbox"
                  checked={detectHardware}
                  onChange={(e) => setDetectHardware(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded text-[var(--accent)] border-[var(--border-color)] focus:ring-0 cursor-pointer"
                />
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-[var(--text-main)] flex items-center gap-1.5">
                    <IconHardware className="text-[var(--accent)] text-xs" />
                    Local hardware VRAM & memory detection
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)] leading-tight mt-0.5">
                    Detects available CPU threads, system RAM, and GPU VRAM for optimal batching.
                  </span>
                </div>
              </label>

              {/* Step 2 Actions */}
              <div className="pt-2 flex justify-between items-center">
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="px-4 py-2 border border-[var(--border-color)] hover:bg-[var(--accent-subtle)] text-[var(--text-main)] font-semibold text-xs rounded-xl flex items-center gap-1.5 transition-all cursor-pointer"
                >
                  <IconBack className="text-xs" />
                  <span>Back</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  className="px-5 py-2 bg-[var(--accent)] hover:opacity-90 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 transition-all shadow-md active:scale-95 cursor-pointer"
                >
                  <span>Next</span>
                  <IconArrowRight className="text-xs" />
                </button>
              </div>
            </div>
          )}

          {/* ══════════ STEP 3: INFERENCE ENGINE ══════════ */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div>
                <span className="text-xs font-bold text-[var(--text-main)] uppercase tracking-wider block mb-1">
                  Inference Engine
                </span>
                <p className="text-[11px] text-[var(--text-muted)]">
                  Connect to local Ollama hardware acceleration or configure Cloud API keys (BYOK).
                </p>
              </div>

              {/* 1. Ollama Hardware Engine Card */}
              <div className="p-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)]/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--text-main)] flex items-center gap-1.5">
                    <IconHardware className="text-[var(--accent)] text-xs" />
                    Ollama Hardware Engine
                  </span>
                  <button
                    type="button"
                    onClick={handleCheckOllama}
                    disabled={isCheckingOllama}
                    className="text-[10px] font-mono text-[var(--accent)] hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                  >
                    {isCheckingOllama ? <IconLoader className="animate-spin text-xs" /> : <IconRefresh className="text-xs" />}
                    <span>Check Status</span>
                  </button>
                </div>

                {/* Ollama Status Badge / Suggestion */}
                {ollamaStatus?.running ? (
                  <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] flex items-center gap-1.5 font-mono">
                    <IconCheck className="text-xs shrink-0" />
                    <span>Ollama Online ({ollamaStatus.count} local models available)</span>
                  </div>
                ) : (
                  <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[10px] leading-tight space-y-1">
                    <div className="flex items-center gap-1.5 font-semibold">
                      <IconAlertCircle className="text-xs shrink-0" />
                      <span>Ollama not detected on localhost:11434</span>
                    </div>
                    <p className="text-[9.5px] text-[var(--text-muted)]">
                      For zero-cost local inference, install Ollama from{' '}
                      <a
                        href="https://ollama.com"
                        target="_blank"
                        rel="noreferrer"
                        className="text-[var(--accent)] underline font-mono"
                      >
                        ollama.com
                      </a>
                      . Alternatively, provide Groq / OpenRouter cloud keys below.
                    </p>
                  </div>
                )}
              </div>

              {/* 2. Groq API Key Input */}
              <div className="space-y-1">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
                    Groq API Key (Fast LPU Inference)
                  </label>
                  {groqStatus && (
                    <span className={`text-[9px] font-mono ${groqStatus.valid ? 'text-emerald-400' : 'text-red-400'}`}>
                      {groqStatus.message}
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <IconKey className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                    <input
                      type="password"
                      value={groqApiKey}
                      onChange={(e) => {
                        setGroqApiKey(e.target.value);
                        setGroqStatus(null);
                      }}
                      placeholder="gsk_..."
                      className="w-full pl-9 pr-3 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] font-mono"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleVerifyGroq}
                    disabled={groqStatus?.loading}
                    className="px-3 py-2 bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--accent)] text-xs font-mono font-semibold rounded-xl text-[var(--text-main)] transition-colors cursor-pointer shrink-0"
                  >
                    {groqStatus?.loading ? <IconLoader className="animate-spin text-xs" /> : 'Verify'}
                  </button>
                </div>
              </div>

              {/* 3. OpenRouter API Key Input */}
              <div className="space-y-1">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
                    OpenRouter API Key (Universal Models)
                  </label>
                  {openrouterStatus && (
                    <span className={`text-[9px] font-mono ${openrouterStatus.valid ? 'text-emerald-400' : 'text-red-400'}`}>
                      {openrouterStatus.message}
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <IconKey className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                    <input
                      type="password"
                      value={openrouterApiKey}
                      onChange={(e) => {
                        setOpenrouterApiKey(e.target.value);
                        setOpenrouterStatus(null);
                      }}
                      placeholder="sk-or-v1-..."
                      className="w-full pl-9 pr-3 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] font-mono"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleVerifyOpenRouter}
                    disabled={openrouterStatus?.loading}
                    className="px-3 py-2 bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--accent)] text-xs font-mono font-semibold rounded-xl text-[var(--text-main)] transition-colors cursor-pointer shrink-0"
                  >
                    {openrouterStatus?.loading ? <IconLoader className="animate-spin text-xs" /> : 'Verify'}
                  </button>
                </div>
              </div>

              {/* Step 3 Actions */}
              <div className="pt-2 flex justify-between items-center">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="px-4 py-2 border border-[var(--border-color)] hover:bg-[var(--accent-subtle)] text-[var(--text-main)] font-semibold text-xs rounded-xl flex items-center gap-1.5 transition-all cursor-pointer"
                >
                  <IconBack className="text-xs" />
                  <span>Back</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentStep(4)}
                  className="px-5 py-2 bg-[var(--accent)] hover:opacity-90 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 transition-all shadow-md active:scale-95 cursor-pointer"
                >
                  <span>Next</span>
                  <IconArrowRight className="text-xs" />
                </button>
              </div>
            </div>
          )}

          {/* ══════════ STEP 4: DEVICE & COMPANION AVATAR ══════════ */}
          {currentStep === 4 && (
            <div className="space-y-4">
              <div>
                <span className="text-xs font-bold text-[var(--text-main)] uppercase tracking-wider block mb-1">
                  Device & Companion Avatar
                </span>
                <p className="text-[11px] text-[var(--text-muted)]">
                  Choose your AI mascot companion persona and device session preferences.
                </p>
              </div>

              {/* Avatar Selection Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {MASCOT_LIST.map((id) => {
                  const isSelected = avatarId === id;
                  return (
                    <MascotWaistUpCard
                      key={id}
                      avatarId={id}
                      isSelected={isSelected}
                      onClick={() => setAvatarId(id)}
                    />
                  );
                })}
              </div>

              {/* Remember Device Checkbox */}
              <label className="flex items-center gap-2.5 p-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-base)]/60 cursor-pointer hover:border-[var(--accent-border)] transition-colors select-none">
                <input
                  type="checkbox"
                  checked={rememberDevice}
                  onChange={(e) => setRememberDevice(e.target.checked)}
                  className="w-4 h-4 rounded text-[var(--accent)] border-[var(--border-color)] focus:ring-0 cursor-pointer"
                />
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-[var(--text-main)]">
                    Remember this device
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)]">
                    Persist local session preferences across app launches.
                  </span>
                </div>
              </label>

              {/* Step 4 Actions */}
              <div className="pt-2 flex justify-between items-center">
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  className="px-4 py-2 border border-[var(--border-color)] hover:bg-[var(--accent-subtle)] text-[var(--text-main)] font-semibold text-xs rounded-xl flex items-center gap-1.5 transition-all cursor-pointer"
                >
                  <IconBack className="text-xs" />
                  <span>Back</span>
                </button>
                <button
                  type="button"
                  onClick={handleFinishWizard}
                  disabled={isLoading}
                  className="px-6 py-2 bg-[var(--accent)] hover:opacity-90 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 transition-all shadow-md active:scale-95 cursor-pointer disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <IconLoader className="animate-spin text-xs" />
                      <span>Finalizing...</span>
                    </>
                  ) : (
                    <>
                      <span>Finish Setup</span>
                      <IconCheck className="text-xs" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
