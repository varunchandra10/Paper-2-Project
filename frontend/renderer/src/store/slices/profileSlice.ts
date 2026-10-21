import type { StateCreator } from 'zustand';
import type { PanelState } from '../panelStore';
import { API_BASE } from '../utils/storeUtils';

export interface OnboardingPayload {
  username: string;
  email: string;
  subscribed?: boolean;
  projectPath?: string | null;
  allowCodeExecution?: boolean;
  detectHardware?: boolean;
  ollamaEnabled?: boolean;
  ollamaLink?: string | null;
  groqApiKey?: string | null;
  openrouterApiKey?: string | null;
  rememberDevice?: boolean;
  avatarId?: string | null;
}

export interface ProfileSlice {
  userId: string | null;
  username: string | null;
  email: string | null;
  dob: string | null;
  age: string | null;
  phoneNumber: string | null;
  projectPath: string | null;
  ollamaLink: string | null;
  avatarId: string | null;
  groqApiKey: string | null;
  openrouterApiKey: string | null;
  allowCodeExecution: boolean;
  rememberDevice: boolean;
  setAvatarId: (avatarId: string) => void;
  fetchProfile: () => Promise<void>;
  loginLocalUser: (username: string, email: string) => Promise<void>;
  completeOnboardingWizard: (payload: OnboardingPayload) => Promise<void>;
  verifyApiKey: (provider: 'groq' | 'openrouter', apiKey: string) => Promise<{ valid: boolean; message: string; data?: any }>;
  checkOllamaStatus: () => Promise<{ running: boolean; count: number; models: string[]; message: string }>;
  updateProfile: (profile: {
    username: string;
    email: string;
    dob?: string | null;
    age?: string | null;
    phoneNumber?: string | null;
    projectPath?: string | null;
    ollamaLink?: string | null;
    avatarId?: string | null;
    groqApiKey?: string | null;
    openrouterApiKey?: string | null;
    allowCodeExecution?: boolean;
    rememberDevice?: boolean;
  }) => Promise<void>;
}

export const createProfileSlice: StateCreator<PanelState, [], [], ProfileSlice> = (set, get) => ({
  userId: localStorage.getItem('local_user_id') || 'usr_1',
  username: localStorage.getItem('local_username') || 'Varun Chandra',
  email: localStorage.getItem('local_email') || 'varunchandra@research.edu',
  dob: localStorage.getItem('local_dob') || null,
  age: localStorage.getItem('local_age') || null,
  phoneNumber: localStorage.getItem('local_phone_number') || null,
  projectPath: localStorage.getItem('local_project_path') || null,
  ollamaLink: localStorage.getItem('local_ollama_link') || null,
  avatarId: localStorage.getItem('local_avatar_id') || 'mr-nerdy',
  groqApiKey: localStorage.getItem('local_groq_api_key') || null,
  openrouterApiKey: localStorage.getItem('local_openrouter_api_key') || null,

  setAvatarId: (avatarId: string) => {
    localStorage.setItem('local_avatar_id', avatarId);
    set({ avatarId });
    if (typeof window !== 'undefined' && window.mascotAPI?.setMascotSkin) {
      window.mascotAPI.setMascotSkin(avatarId);
    }
  },

  fetchProfile: async () => {
    try {
      const uid = get().userId;
      const url = uid ? `${API_BASE}/auth/user/profile?user_id=${uid}` : `${API_BASE}/auth/user/profile`;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        if (data && data.user_id) {
          const effectiveAvatarId = data.avatarId ?? get().avatarId ?? 'mr-nerdy';
          set({
            userId: data.user_id,
            username: data.username || get().username,
            email: data.email || get().email,
            dob: data.dob ?? get().dob,
            age: data.age ?? get().age,
            phoneNumber: data.phoneNumber ?? get().phoneNumber,
            projectPath: data.projectPath ?? get().projectPath,
            ollamaLink: data.ollamaLink ?? get().ollamaLink,
            avatarId: effectiveAvatarId,
            groqApiKey: data.groqApiKey ?? get().groqApiKey,
            openrouterApiKey: data.openrouterApiKey ?? get().openrouterApiKey
          });
          localStorage.setItem('local_user_id', data.user_id);
          if (data.username) localStorage.setItem('local_username', data.username);
          if (data.email) localStorage.setItem('local_email', data.email);
          if (effectiveAvatarId) {
            localStorage.setItem('local_avatar_id', effectiveAvatarId);
            if (typeof window !== 'undefined' && window.mascotAPI?.setMascotSkin) {
              window.mascotAPI.setMascotSkin(effectiveAvatarId);
            }
          }
        } else {
          // Backend has clean/wiped storage — clear all local session keys to trigger setup wizard
          localStorage.removeItem('local_user_id');
          localStorage.removeItem('local_username');
          localStorage.removeItem('local_email');
          set({
            userId: 'usr_1',
            username: 'Varun Chandra',
            email: 'varunchandra@research.edu'
          });
        }
      }
    } catch (err) {
      console.error("Failed to fetch user profile from database:", err);
    }
  },

  allowCodeExecution: localStorage.getItem('local_allow_code_exec') !== 'false',
  rememberDevice: localStorage.getItem('local_remember_device') !== 'false',

  loginLocalUser: async (username: string, email: string) => {
    try {
      const response = await fetch(`${API_BASE}/auth/local-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email })
      });
      if (!response.ok) {
        throw new Error(`Failed to login: ${response.statusText}`);
      }
      const data = await response.json();
      localStorage.setItem('local_user_id', data.user_id);
      localStorage.setItem('local_username', data.username);
      localStorage.setItem('local_email', data.email);
      set({
        userId: data.user_id,
        username: data.username,
        email: data.email
      });
      await get().fetchProfile();
      get().fetchConversations();
      get().fetchUploadedPapers();
    } catch (err) {
      console.error(err);
      throw err;
    }
  },

  completeOnboardingWizard: async (payload: OnboardingPayload) => {
    try {
      const response = await fetch(`${API_BASE}/auth/setup-wizard`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        throw new Error(`Onboarding setup failed: ${response.statusText}`);
      }
      const data = await response.json();
      const user = data.user || {};
      const uid = data.user_id || user.user_id || 'usr_1';

      localStorage.setItem('local_user_id', uid);
      localStorage.setItem('local_username', payload.username);
      localStorage.setItem('local_email', payload.email);
      if (payload.projectPath) localStorage.setItem('local_project_path', payload.projectPath);
      if (payload.groqApiKey) localStorage.setItem('local_groq_api_key', payload.groqApiKey);
      if (payload.openrouterApiKey) localStorage.setItem('local_openrouter_api_key', payload.openrouterApiKey);
      if (payload.avatarId) localStorage.setItem('local_avatar_id', payload.avatarId);
      localStorage.setItem('local_allow_code_exec', String(payload.allowCodeExecution ?? true));
      localStorage.setItem('local_remember_device', String(payload.rememberDevice ?? true));

      set({
        userId: uid,
        username: payload.username,
        email: payload.email,
        projectPath: payload.projectPath || null,
        groqApiKey: payload.groqApiKey || null,
        openrouterApiKey: payload.openrouterApiKey || null,
        avatarId: payload.avatarId || 'mr-nerdy',
        allowCodeExecution: payload.allowCodeExecution ?? true,
        rememberDevice: payload.rememberDevice ?? true,
      });

      if (payload.avatarId && typeof window !== 'undefined' && window.mascotAPI?.setMascotSkin) {
        window.mascotAPI.setMascotSkin(payload.avatarId);
      }

      await get().fetchProfile();
      get().fetchConversations();
      get().fetchUploadedPapers();
    } catch (err) {
      console.error('[ProfileSlice] completeOnboardingWizard error:', err);
      throw err;
    }
  },

  verifyApiKey: async (provider: 'groq' | 'openrouter', apiKey: string) => {
    try {
      const response = await fetch(`${API_BASE}/auth/verify-key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: apiKey })
      });
      if (response.ok) {
        return await response.json();
      }
      return { valid: false, message: `Verification failed with HTTP ${response.status}` };
    } catch (err: any) {
      return { valid: false, message: err?.message || 'Connection error' };
    }
  },

  checkOllamaStatus: async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/check-ollama`);
      if (response.ok) {
        return await response.json();
      }
      return { running: false, count: 0, models: [], message: 'Ollama service offline' };
    } catch {
      return { running: false, count: 0, models: [], message: 'Could not connect to backend' };
    }
  },

  updateProfile: async (profile) => {
    try {
      const uid = get().userId || 'usr_1';
      const response = await fetch(`${API_BASE}/auth/user/profile?user_id=${uid}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profile)
      });
      if (!response.ok) {
        throw new Error(`Failed to update profile: ${response.statusText}`);
      }
      const data = await response.json();
      const updatedUser = data.user || {};
      
      localStorage.setItem('local_user_id', updatedUser.id || uid);
      localStorage.setItem('local_username', updatedUser.username || profile.username);
      localStorage.setItem('local_email', updatedUser.email || profile.email);

      if (profile.dob !== undefined) {
        if (profile.dob) localStorage.setItem('local_dob', profile.dob);
        else localStorage.removeItem('local_dob');
      }
      if (profile.age !== undefined) {
        if (profile.age) localStorage.setItem('local_age', profile.age);
        else localStorage.removeItem('local_age');
      }
      if (profile.phoneNumber !== undefined) {
        if (profile.phoneNumber) localStorage.setItem('local_phone_number', profile.phoneNumber);
        else localStorage.removeItem('local_phone_number');
      }
      if (profile.projectPath !== undefined) {
        if (profile.projectPath) localStorage.setItem('local_project_path', profile.projectPath);
        else localStorage.removeItem('local_project_path');
      }
      if (profile.ollamaLink !== undefined) {
        if (profile.ollamaLink) localStorage.setItem('local_ollama_link', profile.ollamaLink);
        else localStorage.removeItem('local_ollama_link');
      }
      if (profile.avatarId !== undefined) {
        if (profile.avatarId) {
          localStorage.setItem('local_avatar_id', profile.avatarId);
          if (typeof window !== 'undefined' && window.mascotAPI?.setMascotSkin) {
            window.mascotAPI.setMascotSkin(profile.avatarId);
          }
        } else {
          localStorage.removeItem('local_avatar_id');
        }
      }
      if (profile.groqApiKey !== undefined) {
        if (profile.groqApiKey) localStorage.setItem('local_groq_api_key', profile.groqApiKey);
        else localStorage.removeItem('local_groq_api_key');
      }
      if (profile.openrouterApiKey !== undefined) {
        if (profile.openrouterApiKey) localStorage.setItem('local_openrouter_api_key', profile.openrouterApiKey);
        else localStorage.removeItem('local_openrouter_api_key');
      }

      set({
        userId: updatedUser.id || uid,
        username: updatedUser.username || profile.username,
        email: updatedUser.email || profile.email,
        dob: profile.dob !== undefined ? profile.dob : get().dob,
        age: profile.age !== undefined ? profile.age : get().age,
        phoneNumber: profile.phoneNumber !== undefined ? profile.phoneNumber : get().phoneNumber,
        projectPath: profile.projectPath !== undefined ? profile.projectPath : get().projectPath,
        ollamaLink: profile.ollamaLink !== undefined ? profile.ollamaLink : get().ollamaLink,
        avatarId: profile.avatarId !== undefined ? profile.avatarId : get().avatarId,
        groqApiKey: profile.groqApiKey !== undefined ? profile.groqApiKey : get().groqApiKey,
        openrouterApiKey: profile.openrouterApiKey !== undefined ? profile.openrouterApiKey : get().openrouterApiKey
      });
      get().fetchConversations();
      get().fetchUploadedPapers();
    } catch (err) {
      console.error(err);
      throw err;
    }
  },
});
