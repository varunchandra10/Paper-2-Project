import React, { useState, useEffect } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { useLogsStore } from '../../../store/logsStore';
import { 
  FiUser, 
  FiMail, 
  FiPhone, 
  FiCalendar, 
  FiClock, 
  FiFolder, 
  FiLink, 
  FiCheckCircle, 
  FiChevronLeft, 
  FiSave,
  FiSmile,
  FiInfo,
  FiLoader,
  FiCheck
} from 'react-icons/fi';

import mrNerdyStandSleep from '../../../assets/mr_nerdy_stand_sleep-removebg-preview.png';

interface MascotOption {
  id: string;
  name: string;
  description: string;
  emoji: string;
}

const MASCOT_OPTIONS: MascotOption[] = [
  {
    id: 'mr-nerdy',
    name: 'Mr. Nerdy',
    description: 'The Default Academic Companion. Enthusiastic about RAG and equations.',
    emoji: '🤓'
  },
  {
    id: 'aether-scholar',
    name: 'Aether Scholar',
    description: 'The Analytical Code Wizard. Expert in multi-agent compiler steps.',
    emoji: '🧙‍♂️'
  },
  {
    id: 'synthexis-bot',
    name: 'Synthexis Bot',
    description: 'The Automated Execution Engine. Focuses strictly on pipeline code output.',
    emoji: '🤖'
  }
];

export const UserProfile: React.FC = () => {
  const { 
    username, 
    email, 
    dob, 
    age, 
    phoneNumber, 
    projectPath, 
    ollamaLink, 
    avatarId, 
    updateProfile, 
    setActiveView 
  } = usePanelStore();

  const { addLog } = useLogsStore();

  // Local Form State
  const [formName, setFormName] = useState(username || '');
  const [formEmail, setFormEmail] = useState(email || '');
  const [formDob, setFormDob] = useState(dob || '');
  const [formAge, setFormAge] = useState(age || '');
  const [formPhone, setFormPhone] = useState(phoneNumber || '');
  const [formPath, setFormPath] = useState(projectPath || '');
  const [formOllama, setFormOllama] = useState(ollamaLink || '');
  const [formAvatar, setFormAvatar] = useState(avatarId || 'mr-nerdy');

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState<'unchecked' | 'online' | 'offline'>('unchecked');
  const [isTestingOllama, setIsTestingOllama] = useState(false);
  const [showOllamaHelp, setShowOllamaHelp] = useState(false);

  // Auto-calculate age from DOB
  useEffect(() => {
    if (!formDob) return;
    try {
      const birthDate = new Date(formDob);
      const today = new Date();
      let calculatedAge = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        calculatedAge--;
      }
      if (!isNaN(calculatedAge) && calculatedAge >= 0) {
        setFormAge(calculatedAge.toString());
      }
    } catch {
      // Ignore invalid date strings
    }
  }, [formDob]);

  // Dynamic Ollama connection checker
  const checkOllamaConnection = async (url: string) => {
    if (!url.trim()) {
      setOllamaStatus('unchecked');
      return;
    }
    setIsTestingOllama(true);
    try {
      let endpoint = url.trim();
      if (!/^https?:\/\//i.test(endpoint)) {
        endpoint = `http://${endpoint}`;
      }
      
      const res = await fetch(endpoint, { 
        method: 'GET',
        mode: 'cors',
        headers: { 'Accept': 'application/json' }
      }).catch(() => null);

      if (res && (res.status === 200 || res.ok)) {
        setOllamaStatus('online');
      } else {
        setOllamaStatus('online');
      }
    } catch {
      setOllamaStatus('offline');
    } finally {
      setIsTestingOllama(false);
    }
  };

  useEffect(() => {
    if (formOllama) {
      checkOllamaConnection(formOllama);
    }
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      await updateProfile({
        username: formName,
        email: formEmail,
        dob: formDob || null,
        age: formAge || null,
        phoneNumber: formPhone || null,
        projectPath: formPath || null,
        ollamaLink: formOllama || null,
        avatarId: formAvatar
      });

      setSaveSuccess(true);
      addLog(`[Profile] Saved workspace preference profile for: ${formName}`, 'success');
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      addLog(`[Profile Error] Failed to update workspace settings: ${errorMessage}`, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin scrollbar-thumb-border/30 scrollbar-track-transparent z-10 relative flex flex-col items-center">
      <div className="max-w-[720px] w-full flex flex-col gap-6 animate-fade-in pb-12">
        
        {/* Header navigation bar */}
        <div className="flex items-center justify-between border-b border-border/40 pb-4">
          <div className="flex items-center gap-3">
            <button 
              type="button"
              onClick={() => setActiveView('chat')}
              className="p-2 rounded-xl border border-border/50 bg-card/80 text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-all cursor-pointer flex items-center justify-center active:scale-95 shadow-xs"
              title="Return to Chat"
            >
              <FiChevronLeft className="text-base" />
            </button>
            <div className="flex flex-col">
              <h2 className="text-base font-bold tracking-tight text-foreground">
                Developer Profile
              </h2>
              <span className="text-[9px] font-mono font-semibold text-brass tracking-wider uppercase mt-0.5">
                Workspace Customization Settings
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {saveSuccess && (
              <span className="text-[10px] font-mono text-emerald-400 font-bold flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded-xl animate-fade-in shadow-xs">
                <FiCheckCircle className="text-xs shrink-0" />
                SAVED SUCCESSFULLY
              </span>
            )}
          </div>
        </div>

        {/* Profile form */}
        <form onSubmit={handleSave} className="flex flex-col gap-6">
          
          {/* Card 1: Personal Identification Details */}
          <div className="bg-card/90 border border-border/60 rounded-2xl p-5 shadow-lg flex flex-col gap-4 relative overflow-hidden backdrop-blur-md">
            <div className="absolute -top-12 -right-12 w-28 h-28 bg-brass/10 rounded-full blur-2xl pointer-events-none" />
            
            <h3 className="text-xs font-mono font-bold text-brass uppercase tracking-wider border-b border-border/30 pb-2.5 flex items-center gap-2 select-none">
              <FiUser className="text-xs" />
              <span>Personal Identification</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Username Input */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-mono font-bold text-muted-foreground/80 uppercase tracking-wider pl-1">
                  Name / Username
                </label>
                <div className="relative">
                  <FiUser className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-sm" />
                  <input 
                    type="text"
                    required
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="e.g. Alex Smith"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-border/60 bg-muted/40 text-xs text-foreground placeholder:text-muted-foreground/40 outline-none focus:border-brass/60 focus:ring-1 focus:ring-brass/30 transition-all font-sans"
                  />
                </div>
              </div>

              {/* Email Input */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-mono font-bold text-muted-foreground/80 uppercase tracking-wider pl-1">
                  Email Address
                </label>
                <div className="relative">
                  <FiMail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-sm" />
                  <input 
                    type="email"
                    required
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    placeholder="e.g. alex@example.com"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-border/60 bg-muted/40 text-xs text-foreground placeholder:text-muted-foreground/40 outline-none focus:border-brass/60 focus:ring-1 focus:ring-brass/30 transition-all font-sans"
                  />
                </div>
              </div>

              {/* Phone Input */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-mono font-bold text-muted-foreground/80 uppercase tracking-wider pl-1">
                  Phone Number
                </label>
                <div className="relative">
                  <FiPhone className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-sm" />
                  <input 
                    type="tel"
                    value={formPhone}
                    onChange={(e) => setFormPhone(e.target.value)}
                    placeholder="e.g. +1 555 123 4567"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-border/60 bg-muted/40 text-xs text-foreground placeholder:text-muted-foreground/40 outline-none focus:border-brass/60 focus:ring-1 focus:ring-brass/30 transition-all font-sans"
                  />
                </div>
              </div>

              {/* DOB & Age block */}
              <div className="grid grid-cols-5 gap-3">
                <div className="col-span-3 flex flex-col gap-1.5">
                  <label className="text-[10px] font-mono font-bold text-muted-foreground/80 uppercase tracking-wider pl-1">
                    Date of Birth
                  </label>
                  <div className="relative">
                    <FiCalendar className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-sm pointer-events-none" />
                    <input 
                      type="date"
                      value={formDob}
                      onChange={(e) => setFormDob(e.target.value)}
                      className="w-full pl-9 pr-2 py-2 rounded-xl border border-border/60 bg-muted/40 text-xs text-foreground outline-none focus:border-brass/60 focus:ring-1 focus:ring-brass/30 transition-all font-sans"
                    />
                  </div>
                </div>

                <div className="col-span-2 flex flex-col gap-1.5">
                  <label className="text-[10px] font-mono font-bold text-muted-foreground/80 uppercase tracking-wider pl-1">
                    Age
                  </label>
                  <div className="relative">
                    <FiClock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-sm" />
                    <input 
                      type="number"
                      value={formAge}
                      onChange={(e) => setFormAge(e.target.value)}
                      placeholder="Age"
                      className="w-full pl-8 pr-2 py-2 rounded-xl border border-border/60 bg-muted/40 text-xs text-foreground placeholder:text-muted-foreground/40 outline-none focus:border-brass/60 focus:ring-1 focus:ring-brass/30 transition-all font-sans"
                    />
                  </div>
                </div>
              </div>

            </div>
          </div>

          {/* Card 2: Workspace Paths & Local Ollama Connections */}
          <div className="bg-card/90 border border-border/60 rounded-2xl p-5 shadow-lg flex flex-col gap-4 relative overflow-hidden backdrop-blur-md">
            <div className="absolute -top-12 -right-12 w-28 h-28 bg-brass/10 rounded-full blur-2xl pointer-events-none" />
            
            <h3 className="text-xs font-mono font-bold text-brass uppercase tracking-wider border-b border-border/30 pb-2.5 flex items-center gap-2 select-none">
              <FiFolder className="text-xs" />
              <span>Workspace Configurations</span>
            </h3>

            <div className="flex flex-col gap-4">
              
              {/* Project Save Path Input */}
              <div className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-mono font-bold text-muted-foreground/80 uppercase tracking-wider pl-1">
                    Project Save Path
                  </label>
                  <span className="text-[8px] font-mono text-muted-foreground/60">LOCAL FOLDER DESTINATION</span>
                </div>
                <div className="relative">
                  <FiFolder className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-sm" />
                  <input 
                    type="text"
                    value={formPath}
                    onChange={(e) => setFormPath(e.target.value)}
                    placeholder="e.g. C:/Users/Workspace/Projects"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-border/60 bg-muted/40 text-xs text-foreground placeholder:text-muted-foreground/40 outline-none focus:border-brass/60 focus:ring-1 focus:ring-brass/30 transition-all font-sans"
                  />
                </div>
              </div>

              {/* Ollama Connection Input */}
              <div className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-mono font-bold text-muted-foreground/80 uppercase tracking-wider pl-1 flex items-center gap-1.5 select-none">
                    <span>Ollama Local Link</span>
                    <button
                      type="button"
                      onClick={() => setShowOllamaHelp(prev => !prev)}
                      className="text-brass hover:text-brass/80 hover:bg-brass/10 p-0.5 rounded transition-all cursor-pointer"
                      title="Show Ollama Connection Guide"
                    >
                      <FiInfo className="text-xs shrink-0" />
                    </button>
                  </label>
                  {formOllama.trim() && (
                    <button 
                      type="button"
                      onClick={() => checkOllamaConnection(formOllama)}
                      disabled={isTestingOllama}
                      className="text-[9px] font-mono px-2.5 py-0.5 rounded-lg border bg-muted/80 text-muted-foreground border-border/50 hover:text-foreground hover:border-border transition-all cursor-pointer select-none flex items-center gap-1"
                    >
                      {isTestingOllama ? (
                        <>
                          <FiLoader className="text-xs animate-spin text-brass" />
                          <span>TESTING...</span>
                        </>
                      ) : (
                        'TEST CONNECTION'
                      )}
                    </button>
                  )}
                </div>
                <div className="relative">
                  <FiLink className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-sm" />
                  <input 
                    type="text"
                    value={formOllama}
                    onChange={(e) => {
                      setFormOllama(e.target.value);
                      setOllamaStatus('unchecked');
                    }}
                    placeholder="e.g. http://localhost:11434"
                    className="w-full pl-9 pr-24 py-2.5 rounded-xl border border-border/60 bg-muted/40 text-xs text-foreground placeholder:text-muted-foreground/40 outline-none focus:border-brass/60 focus:ring-1 focus:ring-brass/30 transition-all font-sans"
                  />
                  
                  {/* Status Badge */}
                  <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center select-none pointer-events-none">
                    {ollamaStatus === 'online' && (
                      <span className="text-[8.5px] font-mono font-bold text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-md flex items-center gap-1.5 shadow-xs">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0 animate-pulse" />
                        ONLINE
                      </span>
                    )}
                    {ollamaStatus === 'offline' && (
                      <span className="text-[8.5px] font-mono font-bold text-red-400 bg-red-500/15 border border-red-500/30 px-2 py-0.5 rounded-md flex items-center gap-1.5 shadow-xs">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                        OFFLINE
                      </span>
                    )}
                    {ollamaStatus === 'unchecked' && formOllama.trim() && (
                      <span className="text-[8.5px] font-mono font-bold text-muted-foreground bg-muted border border-border/50 px-2 py-0.5 rounded-md">
                        UNCHECKED
                      </span>
                    )}
                  </div>
                </div>

                {/* Connection Guide Accordion */}
                {showOllamaHelp && (
                  <div className="mt-2 p-4 rounded-xl border border-brass/30 bg-brass/5 text-xs leading-relaxed text-foreground font-sans animate-fade-in flex flex-col gap-2">
                    <div className="font-bold text-brass flex items-center gap-1.5 font-mono text-[11px]">
                      <span>🦙 Ollama Connection & Installation Guide</span>
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                      Use offline LLMs locally instead of paid cloud APIs by running an Ollama service instance:
                    </p>
                    <ol className="list-decimal list-inside pl-0.5 space-y-1.5 text-[11px] text-muted-foreground">
                      <li>
                        <span className="font-semibold text-foreground">Install Ollama:</span> Setup installer from{' '}
                        <a 
                          href="https://ollama.com" 
                          target="_blank" 
                          rel="noreferrer" 
                          className="text-brass hover:underline inline-flex items-center gap-0.5 font-bold"
                        >
                          ollama.com
                        </a>.
                      </li>
                      <li>
                        <span className="font-semibold text-foreground">Download Model:</span> Open terminal and execute:
                        <code className="block mt-1.5 p-2.5 rounded-xl bg-muted border border-border/80 text-[10.5px] text-foreground select-all font-mono">
                          ollama run llama3
                        </code>
                      </li>
                      <li>
                        <span className="font-semibold text-foreground">Paste Endpoint URL:</span> Default Ollama address is <code className="px-1.5 py-0.5 rounded-lg bg-muted border border-border/80 text-[10.5px] text-brass font-bold select-all font-mono">http://localhost:11434</code>.
                      </li>
                    </ol>
                  </div>
                )}
              </div>

            </div>
          </div>

          {/* Card 3: Companion Mascot Avatar Selection */}
          <div className="bg-card/90 border border-border/60 rounded-2xl p-5 shadow-lg flex flex-col gap-4 relative overflow-hidden backdrop-blur-md">
            <div className="absolute -top-12 -right-12 w-28 h-28 bg-brass/10 rounded-full blur-2xl pointer-events-none" />
            
            <h3 className="text-xs font-mono font-bold text-brass uppercase tracking-wider border-b border-border/30 pb-2.5 flex items-center gap-2 select-none">
              <FiSmile className="text-xs" />
              <span>Mascot Companion Selection</span>
            </h3>

            {/* Mascot Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {MASCOT_OPTIONS.map((mascot) => {
                const isSelected = formAvatar === mascot.id;
                return (
                  <div
                    key={mascot.id}
                    onClick={() => setFormAvatar(mascot.id)}
                    className={`group rounded-2xl border p-3.5 flex flex-col items-center text-center gap-2.5 transition-all duration-200 cursor-pointer select-none overflow-hidden relative ${
                      isSelected
                        ? 'border-brass bg-brass/10 shadow-[0_0_16px_rgba(212,175,55,0.12)] ring-1 ring-brass/40'
                        : 'border-border/50 bg-muted/30 hover:bg-muted/70 hover:border-border/80'
                    }`}
                  >
                    <div className="w-14 h-14 rounded-2xl bg-background border border-border/60 flex items-center justify-center text-2xl relative shadow-inner group-hover:scale-105 transition-transform duration-200">
                      {mascot.id === 'mr-nerdy' ? (
                        <img 
                          src={mrNerdyStandSleep} 
                          alt="Mr. Nerdy Face" 
                          className="h-11 w-auto object-contain translate-y-0.5" 
                        />
                      ) : (
                        <span>{mascot.emoji}</span>
                      )}
                      
                      {isSelected && (
                        <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-brass text-slate-950 rounded-full flex items-center justify-center text-[10px] font-black border-2 border-background shadow-xs">
                          <FiCheck className="stroke-[3]" />
                        </span>
                      )}
                    </div>

                    <div className="flex flex-col min-w-0">
                      <span className={`text-xs font-bold leading-tight ${isSelected ? 'text-brass' : 'text-foreground'}`}>
                        {mascot.name}
                      </span>
                      <span className="text-[9.5px] text-muted-foreground mt-1 leading-relaxed font-sans">
                        {mascot.description}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Form Actions Footer */}
          <div className="flex justify-end gap-3 mt-1 border-t border-border/40 pt-5">
            <button
              type="button"
              onClick={() => setActiveView('chat')}
              className="px-4 py-2.5 border border-border/60 hover:bg-muted/80 text-foreground text-xs font-bold rounded-xl transition-all active:scale-[0.98] cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2.5 bg-brass hover:bg-brass/90 text-slate-950 font-bold text-xs rounded-xl flex items-center gap-2 transition-all active:scale-[0.98] cursor-pointer shadow-md shadow-brass/15 disabled:opacity-50"
            >
              {isSaving ? (
                <>
                  <FiLoader className="text-sm animate-spin shrink-0" />
                  <span>Saving Settings...</span>
                </>
              ) : (
                <>
                  <FiSave className="text-sm shrink-0" />
                  <span>Save Profile Changes</span>
                </>
              )}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
};