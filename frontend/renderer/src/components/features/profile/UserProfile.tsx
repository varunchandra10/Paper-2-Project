import React, { useState, useEffect } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { useLogsStore } from '../../../store/logsStore';
import { 
  IconUser, 
  IconMail, 
  IconPhone, 
  IconCalendar, 
  IconClock, 
  IconFolder, 
  IconCheckCircle, 
  IconBack, 
  IconSave,
  IconSmile,
  IconLoader
} from '../../ui/Icons';
import { MascotSelector } from './MascotSelector';
import { OllamaConfigSection } from './OllamaConfigSection';
import { ModelLimitsSection } from './ModelLimitsSection';
import { ApiKeysConfigSection } from './ApiKeysConfigSection';

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
    groqApiKey,
    openrouterApiKey,
    setAvatarId,
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
  const [formGroqKey, setFormGroqKey] = useState(groqApiKey || '');
  const [formOpenRouterKey, setFormOpenRouterKey] = useState(openrouterApiKey || '');

  // Keep formAvatar in sync if profile updates from backend or local storage
  useEffect(() => {
    if (avatarId) {
      setFormAvatar(avatarId);
    }
  }, [avatarId]);

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

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
        avatarId: formAvatar,
        groqApiKey: formGroqKey.trim() || null,
        openrouterApiKey: formOpenRouterKey.trim() || null
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
    <div className="flex-1 overflow-y-auto overflow-x-hidden px-6 py-6 scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent z-10 relative flex flex-col items-center w-full max-w-full">
      <div className="max-w-[1100px] w-full flex flex-col gap-6 animate-fade-in pb-12 min-w-0">
        
        {/* Header navigation bar */}
        <div className="flex items-center justify-between border-b app-border pb-4">
          <div className="flex items-center gap-3">
            <button 
              type="button"
              onClick={() => setActiveView('chat')}
              className="p-2 rounded-xl border app-border bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] transition-all cursor-pointer flex items-center justify-center active:scale-95 shadow-xs"
              title="Return to Chat"
            >
              <IconBack className="text-base" />
            </button>
            <div className="flex flex-col">
              <h2 className="text-base font-bold tracking-tight text-[var(--text-main)]">
                Developer Profile
              </h2>
              <span className="text-[9px] font-mono font-semibold text-[var(--accent)] tracking-wider uppercase mt-0.5">
                Workspace Customization Settings
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {saveSuccess && (
              <span className="text-[10px] font-mono text-emerald-400 font-bold flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 rounded-xl animate-fade-in shadow-xs">
                <IconCheckCircle className="text-xs shrink-0" />
                SAVED SUCCESSFULLY
              </span>
            )}
          </div>
        </div>

        {/* Profile form */}
        <form onSubmit={handleSave} className="flex flex-col gap-6">
          
          {/* 2-Column, 2-Row Balanced Grid (Row 1: Info & Mascot, Row 2: Workspace & API Keys) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
            
            {/* ROW 1 - LEFT: Personal Information */}
            <div className="bg-[var(--bg-card)] border app-border rounded-2xl p-5 shadow-lg flex flex-col justify-between h-full relative overflow-hidden backdrop-blur-md">
              <div className="absolute -top-12 -right-12 w-28 h-28 bg-[var(--accent-subtle)] rounded-full blur-2xl pointer-events-none" />
              
              <div>
                <h3 className="text-xs font-mono font-bold text-[var(--accent)] uppercase tracking-wider border-b app-border pb-2.5 flex items-center gap-2 select-none">
                  <IconUser className="text-xs" />
                  <span>Personal Information</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-3.5">
                  {/* Username Input */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider pl-1">
                      Name / Username
                    </label>
                    <div className="relative">
                      <IconUser className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                      <input 
                        type="text"
                        required
                        value={formName}
                        onChange={(e) => setFormName(e.target.value)}
                        placeholder="e.g. Alex Smith"
                        className="w-full pl-9 pr-3 py-2 rounded-xl border app-border bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-sans"
                      />
                    </div>
                  </div>

                  {/* Email Input */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider pl-1">
                      Email Address
                    </label>
                    <div className="relative">
                      <IconMail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                      <input 
                        type="email"
                        required
                        value={formEmail}
                        onChange={(e) => setFormEmail(e.target.value)}
                        placeholder="e.g. alex@example.com"
                        className="w-full pl-9 pr-3 py-2 rounded-xl border app-border bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-sans"
                      />
                    </div>
                  </div>

                  {/* Phone Input */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider pl-1">
                      Phone Number
                    </label>
                    <div className="relative">
                      <IconPhone className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                      <input 
                        type="tel"
                        value={formPhone}
                        onChange={(e) => setFormPhone(e.target.value)}
                        placeholder="e.g. +1 555 123 4567"
                        className="w-full pl-9 pr-3 py-2 rounded-xl border app-border bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-sans"
                      />
                    </div>
                  </div>

                  {/* DOB & Age block */}
                  <div className="grid grid-cols-5 gap-2.5">
                    <div className="col-span-3 flex flex-col gap-1.5">
                      <label className="text-[10px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider pl-1">
                        Date of Birth
                      </label>
                      <div className="relative">
                        <IconCalendar className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm pointer-events-none" />
                        <input 
                          type="date"
                          value={formDob}
                          onChange={(e) => setFormDob(e.target.value)}
                          className="w-full pl-9 pr-2 py-2 rounded-xl border app-border bg-[var(--bg-base)] text-xs text-[var(--text-main)] outline-none focus:border-[var(--accent)] transition-all font-sans"
                        />
                      </div>
                    </div>

                    <div className="col-span-2 flex flex-col gap-1.5">
                      <label className="text-[10px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider pl-1">
                        Age
                      </label>
                      <div className="relative">
                        <IconClock className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                        <input 
                          type="number"
                          value={formAge}
                          onChange={(e) => setFormAge(e.target.value)}
                          placeholder="Age"
                          className="w-full pl-8 pr-2 py-2 rounded-xl border app-border bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-sans"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ROW 1 - RIGHT: Mascot Selection */}
            <div className="bg-[var(--bg-card)] border app-border rounded-2xl p-5 shadow-lg flex flex-col justify-between h-full relative overflow-hidden backdrop-blur-md">
              <div className="absolute -top-12 -right-12 w-28 h-28 bg-[var(--accent-subtle)] rounded-full blur-2xl pointer-events-none" />
              
              <h3 className="text-xs font-mono font-bold text-[var(--accent)] uppercase tracking-wider border-b app-border pb-2.5 flex items-center gap-2 select-none">
                <IconSmile className="text-xs" />
                <span>Mascot Selection</span>
              </h3>

                <MascotSelector 
                  formAvatar={formAvatar} 
                  setFormAvatar={(newAvatarId) => {
                    setFormAvatar(newAvatarId);
                    setAvatarId(newAvatarId);
                  }} 
                />
            </div>

            {/* ROW 2 - LEFT: Workspace Config */}
            <div className="bg-[var(--bg-card)] border app-border rounded-2xl p-5 shadow-lg flex flex-col justify-between h-full relative overflow-hidden backdrop-blur-md">
              <div className="absolute -top-12 -right-12 w-28 h-28 bg-[var(--accent-subtle)] rounded-full blur-2xl pointer-events-none" />
              
              <div className="flex flex-col justify-between h-full">
                <h3 className="text-xs font-mono font-bold text-[var(--accent)] uppercase tracking-wider border-b app-border pb-2.5 flex items-center gap-2 select-none">
                  <IconFolder className="text-xs" />
                  <span>Workspace Config</span>
                </h3>

                <div className="flex flex-col gap-3.5 pt-3.5 flex-1 justify-center">
                  {/* Project Save Path Input */}
                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <label className="text-[10px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider pl-1">
                        Project Save Path
                      </label>
                      <span className="text-[8px] font-mono text-[var(--text-muted)]">LOCAL FOLDER</span>
                    </div>
                    <div className="relative">
                      <IconFolder className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm" />
                      <input 
                        type="text"
                        value={formPath}
                        onChange={(e) => setFormPath(e.target.value)}
                        placeholder="e.g. C:/Users/Workspace/Projects"
                        className="w-full pl-9 pr-3 py-2.5 rounded-xl border app-border bg-[var(--bg-base)] text-xs text-[var(--text-main)] placeholder-[var(--text-muted)] outline-none focus:border-[var(--accent)] transition-all font-sans"
                      />
                    </div>
                  </div>

                  {/* Ollama Connection Input */}
                  <OllamaConfigSection value={formOllama} onChange={setFormOllama} />
                </div>
              </div>
            </div>

            {/* ROW 2 - RIGHT: API Keys Configuration (BYOK) */}
            <div className="h-full">
              <ApiKeysConfigSection
                groqKey={formGroqKey}
                setGroqKey={setFormGroqKey}
                openrouterKey={formOpenRouterKey}
                setOpenrouterKey={setFormOpenRouterKey}
              />
            </div>

          </div>

          {/* Action Buttons below the 2 rows */}
          <div className="flex justify-end items-center gap-3 pt-1">
            <button
              type="button"
              onClick={() => setActiveView('chat')}
              className="px-5 py-2 border app-border hover:bg-[var(--accent-subtle)] text-[var(--text-main)] text-xs font-bold rounded-xl transition-all active:scale-[0.98] cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-6 py-2 bg-[var(--accent)] hover:opacity-90 text-white font-bold text-xs rounded-xl flex items-center gap-2 transition-all active:scale-[0.98] cursor-pointer shadow-md disabled:opacity-50"
            >
              {isSaving ? (
                <>
                  <IconLoader className="text-sm animate-spin shrink-0" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <IconSave className="text-sm shrink-0" />
                  <span>Save</span>
                </>
              )}
            </button>
          </div>

          {/* BOTTOM ROW: Model Rate Limits & Quotas (Full width, 3-column horizontal grid) */}
          <ModelLimitsSection />

        </form>

      </div>
    </div>
  );
};