import type { StateCreator } from 'zustand';
import type { PanelState } from '../panelStore';
import { API_BASE } from '../utils/storeUtils';

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
  fetchProfile: () => Promise<void>;
  loginLocalUser: (username: string, email: string) => Promise<void>;
  updateProfile: (profile: {
    username: string;
    email: string;
    dob?: string | null;
    age?: string | null;
    phoneNumber?: string | null;
    projectPath?: string | null;
    ollamaLink?: string | null;
    avatarId?: string | null;
  }) => Promise<void>;
}

export const createProfileSlice: StateCreator<PanelState, [], [], ProfileSlice> = (set, get) => ({
  userId: localStorage.getItem('local_user_id') || 'usr_1',
  username: localStorage.getItem('local_username') || 'Varun Chandra',
  email: localStorage.getItem('local_email') || 'varunchandra10@gmail.com',
  dob: localStorage.getItem('local_dob') || null,
  age: localStorage.getItem('local_age') || null,
  phoneNumber: localStorage.getItem('local_phone_number') || null,
  projectPath: localStorage.getItem('local_project_path') || null,
  ollamaLink: localStorage.getItem('local_ollama_link') || null,
  avatarId: localStorage.getItem('local_avatar_id') || 'mr-nerdy',

  fetchProfile: async () => {
    try {
      const uid = get().userId || 'usr_1';
      const response = await fetch(`${API_BASE}/auth/user/profile?user_id=${uid}`);
      if (response.ok) {
        const data = await response.json();
        set({
          userId: data.user_id || uid,
          username: data.username || get().username,
          email: data.email || get().email,
          dob: data.dob ?? get().dob,
          age: data.age ?? get().age,
          phoneNumber: data.phoneNumber ?? get().phoneNumber,
          projectPath: data.projectPath ?? get().projectPath,
          ollamaLink: data.ollamaLink ?? get().ollamaLink,
          avatarId: data.avatarId ?? get().avatarId
        });
      }
    } catch (err) {
      console.error("Failed to fetch user profile from database:", err);
    }
  },

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
        if (profile.avatarId) localStorage.setItem('local_avatar_id', profile.avatarId);
        else localStorage.removeItem('local_avatar_id');
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
        avatarId: profile.avatarId !== undefined ? profile.avatarId : get().avatarId
      });
      get().fetchConversations();
      get().fetchUploadedPapers();
    } catch (err) {
      console.error(err);
      throw err;
    }
  },
});
