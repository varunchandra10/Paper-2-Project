import type { StateCreator } from 'zustand';
import type { PanelState, ChatMessage } from '../panelStore';
import { API_BASE } from '../utils/storeUtils';

export interface ChatSlice {
  messages: ChatMessage[];
  activeConversationId: string | null;
  conversations: Array<{ conversation_id: string; id?: string; title: string; project_id?: string | null; created_at?: number | string }>;
  isChatGenerating: boolean;
  isConversationsLoading: boolean;
  
  sendMessage: (content: string, includeAttachment?: boolean) => Promise<void>;
  createConversation: (title: string, projectId?: string | null) => Promise<string>;
  fetchMessages: (conversationId: string) => Promise<void>;
  fetchConversations: () => Promise<void>;
  selectConversation: (conversationId: string) => Promise<void>;
  deleteConversation: (conversationId: string) => Promise<void>;
}

export const createChatSlice: StateCreator<PanelState, [], [], ChatSlice> = (set, get) => ({
  messages: [],
  conversations: [],
  activeConversationId: null,
  isChatGenerating: false,
  isConversationsLoading: false,

  createConversation: async (title: string, projectId: string | null = null) => {
    try {
      const response = await fetch(`${API_BASE}/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: get().userId || 'e2e_test_user',
          title: title,
          project_id: projectId
        })
      });
      if (!response.ok) {
        throw new Error(`Failed to create conversation: ${response.statusText}`);
      }
      const data = await response.json();
      return data.conversation_id;
    } catch (err) {
      console.error(err);
      throw err;
    }
  },

  fetchMessages: async (conversationId: string) => {
    try {
      const response = await fetch(`${API_BASE}/conversations/${conversationId}`);
      if (!response.ok) {
        throw new Error(`Failed to load messages: ${response.statusText}`);
      }
      const data = await response.json();
      const rawMsgs = Array.isArray(data) ? data : (data.messages || []);
      const { activePaperId, uploadedFileName } = get();
      
      const loadedMessages: ChatMessage[] = rawMsgs.map((m: any, idx: number) => {
        let attachment = m.attachment;
        if (!attachment && m.role === 'user') {
          const pId = m.paper_id || activePaperId;
          if (pId) {
            const fName = uploadedFileName || `${pId.replace('paper_', '')}.pdf`;
            attachment = { filename: fName, paperId: pId };
          }
        }
        return {
          id: m.id || m.message_id || `msg_${idx}_${Math.random().toString(36).substring(7)}`,
          role: m.role || 'user',
          content: m.content || m.response || m.text || '',
          model_used: m.model_used || m.model,
          attachment
        };
      });
      set({ messages: loadedMessages });
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  },

  fetchConversations: async () => {
    set({ isConversationsLoading: true });
    try {
      const userId = get().userId || 'e2e_test_user';
      const response = await fetch(`${API_BASE}/conversations?user_id=${userId}`);
      if (response.ok) {
        const data = await response.json();
        const rawList = Array.isArray(data) ? data : (data.conversations || []);
        const list = rawList.map((c: any) => ({
          conversation_id: c.conversation_id || c.id,
          id: c.id || c.conversation_id,
          title: c.title || c.conversation_id || c.id,
          project_id: c.project_id,
          created_at: c.created_at
        }));
        set({ conversations: list });
      }
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
    } finally {
      set({ isConversationsLoading: false });
    }
  },

  selectConversation: async (conversationId: string) => {
    const conv = get().conversations.find(c => (c.conversation_id || c.id) === conversationId);
    const paperId = conv?.project_id || null;
    let filename = null;
    if (paperId) {
      const paper = get().uploadedHistory.find(h => h.id === paperId);
      filename = paper?.name || `${paperId.replace('paper_', '')}.pdf`;
    }

    set({
      activeConversationId: conversationId,
      uploadedFileName: filename,
      uploadedFileType: filename ? 'pdf' : null,
      activePaperId: paperId,
      activePaperPath: null,
    });
    await get().fetchMessages(conversationId);
  },

  deleteConversation: async (conversationId: string) => {
    try {
      const response = await fetch(`${API_BASE}/conversations/${conversationId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        const updated = get().conversations.filter(c => (c.conversation_id || c.id) !== conversationId);
        set({ conversations: updated });
        if (get().activeConversationId === conversationId) {
          set({ activeConversationId: null, messages: [] });
        }
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  },

  sendMessage: async (content: string, includeAttachment: boolean = false) => {
    let currentConvId = get().activeConversationId;
    const { activePaperId } = get();

    if (!currentConvId) {
      const newTitle = activePaperId ? `Discussion: ${activePaperId}` : `Chat - ${new Date().toLocaleTimeString()}`;
      try {
        currentConvId = await get().createConversation(newTitle, activePaperId);
        set({ activeConversationId: currentConvId });
        get().fetchConversations();
      } catch (err: any) {
        console.error("Failed to create conversation:", err);
        return;
      }
    }

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(7),
      role: 'user',
      content,
      ...(includeAttachment && activePaperId && get().uploadedFileName
        ? { attachment: { filename: get().uploadedFileName!, paperId: activePaperId } }
        : {}),
    };

    set((state) => ({ messages: [...state.messages, userMsg], isChatGenerating: true }));

    try {
      const response = await fetch(`${API_BASE}/conversations/${currentConvId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': get().userId || 'e2e_test_user'
        },
        body: JSON.stringify({
          content,
          paper_id: activePaperId,
          model_name: get().selectedModel
        })
      });

      if (!response.ok) {
        throw new Error(`API returned error status ${response.status}`);
      }

      const data = await response.json();
      const assistantMsg: ChatMessage = {
        id: Math.random().toString(36).substring(7),
        role: 'assistant',
        content: data.content || data.response || data.raw_response || "I am ready to assist you.",
        model_used: data.model_used || get().selectedModel
      };

      set((state) => ({ messages: [...state.messages, assistantMsg], isChatGenerating: false }));
      get().fetchConversations();
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: Math.random().toString(36).substring(7),
        role: 'assistant',
        content: `Error generating response: ${err.message || 'Server error'}`,
        model_used: get().selectedModel
      };
      set((state) => ({ messages: [...state.messages, errorMsg], isChatGenerating: false }));
    }
  },
});
