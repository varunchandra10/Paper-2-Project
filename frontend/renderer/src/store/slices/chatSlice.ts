import type { StateCreator } from 'zustand';
import type { PanelState, ChatMessage } from '../panelStore';
import { API_BASE } from '../utils/storeUtils';
import { resolveFailoverModelId } from '../../constants/models';
import { useLogsStore } from '../logsStore';
import {
  parseChatStreamDone,
  parseCreateConversation,
  parseConversationDetail,
  parseConversationsList
} from '../../schemas/api';

export interface ChatSlice {
  messages: ChatMessage[];
  activeConversationId: string | null;
  activeConversationTitle: string | null;
  conversations: Array<{ conversation_id: string; id?: string; title: string; project_id?: string | null; created_at?: number | string }>;
  isChatGenerating: boolean;
  isConversationsLoading: boolean;
  isMessagesLoading: boolean;
  streamingStatus: string | null;
  streamingThought: string | null;
  streamingAction: string | null;
  /** Holds the AbortController for any in-flight /chat request. Aborted on conversation switch. */
  currentAbortController: AbortController | null;

  sendMessage: (content: string, includeAttachment?: boolean) => Promise<void>;
  createConversation: (title: string, projectId?: string | null) => Promise<string>;
  fetchMessages: (conversationId: string, showSkeleton?: boolean) => Promise<void>;
  fetchConversations: () => Promise<void>;
  selectConversation: (conversationId: string) => Promise<void>;
  deleteConversation: (conversationId: string) => Promise<void>;
  updateConversationTitle: (conversationId: string, newTitle: string) => Promise<void>;
  regenerateMessage: (promptContent?: string) => Promise<void>;
}

interface SseDispatcher {
  onToken: (token: string) => void;
  onDone: (meta: any) => void;
  onError: (err: string) => void;
  onStatus?: (status: string) => void;
  onThought?: (thought: string) => void;
  onAction?: (action: string) => void;
}

function createSseParser(dispatcher: SseDispatcher) {
  let currentEvent = 'message';
  let currentData = '';

  const dispatchCurrent = () => {
    if (!currentData && currentEvent === 'message') return;

    let resolvedEvent = currentEvent;
    let resolvedData = currentData;

    // Handle case where data is wrapped JSON containing event & data
    if (resolvedData.trim().startsWith('{') && resolvedData.trim().endsWith('}')) {
      try {
        const parsed = JSON.parse(resolvedData);
        if (parsed.event && typeof parsed.event === 'string') {
          resolvedEvent = parsed.event;
        }
        if (parsed.data !== undefined) {
          resolvedData = typeof parsed.data === 'string' ? parsed.data : JSON.stringify(parsed.data);
        }
      } catch {}
    }

    if (resolvedEvent === 'token') {
      dispatcher.onToken(resolvedData);
    } else if (resolvedEvent === 'done') {
      try {
        const metaObj = typeof resolvedData === 'string' ? JSON.parse(resolvedData) : resolvedData;
        dispatcher.onDone(metaObj);
      } catch (err) {
        console.warn("Failed to parse SSE done payload:", err);
      }
    } else if (resolvedEvent === 'error') {
      dispatcher.onError(resolvedData);
    } else if (resolvedEvent === 'status' && dispatcher.onStatus) {
      dispatcher.onStatus(resolvedData);
    } else if (resolvedEvent === 'thought' && dispatcher.onThought) {
      dispatcher.onThought(resolvedData);
    } else if (resolvedEvent === 'action' && dispatcher.onAction) {
      dispatcher.onAction(resolvedData);
    }

    currentEvent = 'message';
    currentData = '';
  };

  const feedLine = (rawLine: string) => {
    const line = rawLine.replace(/\r$/, '');
    if (line.startsWith(':')) {
      // SSE comment or keep-alive ping
      return;
    }
    if (line.startsWith('event:')) {
      currentEvent = line.slice(6).trim();
      return;
    }
    if (line.startsWith('data:')) {
      let dataContent = line.slice(5);
      if (dataContent.startsWith(' ')) {
        dataContent = dataContent.slice(1);
      }
      currentData = currentData ? currentData + '\n' + dataContent : dataContent;
      return;
    }
    if (line === '') {
      dispatchCurrent();
    }
  };

  const flush = () => {
    dispatchCurrent();
  };

  return { feedLine, flush };
}

export const createChatSlice: StateCreator<PanelState, [], [], ChatSlice> = (set, get) => ({
  messages: [],
  conversations: [],
  activeConversationId: null,
  activeConversationTitle: null,
  isChatGenerating: false,
  isConversationsLoading: false,
  isMessagesLoading: false,
  streamingStatus: null,
  streamingThought: null,
  streamingAction: null,
  currentAbortController: null,

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
      const data = parseCreateConversation(await response.json());
      const newTitle = data.title || title;

      try {
        localStorage.setItem('active_conversation_id', data.conversation_id);
        if (newTitle) localStorage.setItem('active_conversation_title', newTitle);
      } catch {}

      set((state) => ({
        activeConversationId: data.conversation_id,
        activeConversationTitle: newTitle,
        conversations: [
          {
            conversation_id: data.conversation_id,
            id: data.conversation_id,
            title: newTitle,
            project_id: projectId
          },
          ...state.conversations.filter(c => (c.conversation_id || c.id) !== data.conversation_id)
        ]
      }));
      return data.conversation_id;
    } catch (err) {
      console.error(err);
      throw err;
    }
  },

  fetchMessages: async (conversationId: string, showSkeleton: boolean = true) => {
    if (showSkeleton) set({ isMessagesLoading: true });
    try {
      const response = await fetch(`${API_BASE}/conversations/${conversationId}`);
      if (!response.ok) {
        throw new Error(`Failed to load messages: ${response.statusText}`);
      }
      const raw = await response.json();
      const data = parseConversationDetail(Array.isArray(raw) ? { messages: raw } : raw);
      const rawMsgs = data.messages || [];
      const { activePaperId, uploadedFileName } = get();

      // Only the FIRST user message gets the PDF attachment card (Claude-style).
      // All subsequent user messages are plain text prompts.
      // Filter out any legacy welcome-rag-prompt messages
      const filteredMsgs = rawMsgs.filter((m: any) => 
        m.id !== 'welcome-rag-prompt' && 
        !m.id?.startsWith('welcome-rag-') && 
        !(typeof m.content === 'string' && m.content.includes('successfully ingested and indexed'))
      );

      let firstUserMsgSeen = false;
      const loadedMessages: ChatMessage[] = filteredMsgs.map((m: any, idx: number) => {
        let attachment = m.attachment;

        if (m.role === 'user') {
          if (!firstUserMsgSeen) {
            // First user message — attach PDF if available
            firstUserMsgSeen = true;
            if (!attachment) {
              const pId = m.paper_id || activePaperId;
              if (pId) {
                const fName = uploadedFileName || `${pId.replace('paper_', '')}.pdf`;
                attachment = { filename: fName, paperId: pId };
              }
            }
          } else {
            // Subsequent user messages — strip any attachment (plain prompt)
            attachment = undefined;
          }
        }

        return {
          id: m.id || m.message_id || `msg_${idx}_${crypto.randomUUID()}`,
          role: m.role || 'user',
          content: m.content || m.response || m.text || '',
          model_used: m.model_used || m.model,
          attachment
        };
      });

      const existingTitle = get().activeConversationTitle;
      const isTitleAlreadySet = Boolean(existingTitle && !existingTitle.startsWith('conv_') && existingTitle !== 'New Research Analysis' && existingTitle !== 'Research Thread' && existingTitle !== 'Untitled Thread');
      const titleToApply = isTitleAlreadySet ? existingTitle : data.title;

      if (!isTitleAlreadySet && titleToApply && !titleToApply.startsWith('conv_') && titleToApply !== 'New Research Analysis' && titleToApply !== 'Research Thread' && titleToApply !== 'Untitled Thread') {
        try {
          localStorage.setItem('active_conversation_title', titleToApply);
        } catch {}
      }

      set((state) => ({
        messages: loadedMessages,
        ...(!isTitleAlreadySet && titleToApply ? { activeConversationTitle: titleToApply } : {}),
        conversations: !isTitleAlreadySet && titleToApply
          ? state.conversations.map(c => 
              (c.conversation_id === conversationId || c.id === conversationId)
                ? { ...c, title: titleToApply }
                : c
            )
          : state.conversations
      }));
    } catch (err) {
      console.error("Failed to load messages:", err);
    } finally {
      if (showSkeleton) set({ isMessagesLoading: false });
    }
  },

  fetchConversations: async () => {
    set({ isConversationsLoading: true });
    try {
      const userId = get().userId || 'e2e_test_user';
      const response = await fetch(`${API_BASE}/conversations?user_id=${userId}`);
      if (response.ok) {
        const raw = await response.json();
        const data = parseConversationsList(Array.isArray(raw) ? { conversations: raw } : raw);
        const rawList = data.conversations || [];
        const list = rawList.map((c: any) => ({
          conversation_id: c.conversation_id || c.id,
          id: c.id || c.conversation_id,
          title: c.title || c.conversation_id || c.id,
          project_id: c.project_id,
          created_at: c.created_at
        }));
        
        // Only keep active conversation if already selected in current session
        const currentActiveId = get().activeConversationId;
        const matchingActive = currentActiveId ? list.find((c: any) => (c.conversation_id === currentActiveId || c.id === currentActiveId)) : null;

        let activeId: string | null = null;
        let activeTitle: string | null = null;

        if (currentActiveId) {
          activeId = currentActiveId;
          const currentStoreTitle = get().activeConversationTitle;
          const isStoreTitleValid = Boolean(currentStoreTitle && !currentStoreTitle.startsWith('conv_') && currentStoreTitle !== 'New Research Analysis' && currentStoreTitle !== 'Research Thread' && currentStoreTitle !== 'Untitled Thread');
          
          if (isStoreTitleValid) {
            // Conversation title is already established for this thread; keep it intact
            activeTitle = currentStoreTitle;
          } else {
            const rawTitle = matchingActive?.title;
            const isMatchValid = Boolean(rawTitle && !rawTitle.startsWith('conv_') && rawTitle !== 'New Research Analysis' && rawTitle !== 'Research Thread' && rawTitle !== 'Untitled Thread');
            activeTitle = isMatchValid ? rawTitle : null;
          }
        }

        set({
          conversations: list,
          activeConversationId: activeId,
          activeConversationTitle: activeTitle
        });
      }
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
    } finally {
      set({ isConversationsLoading: false });
    }
  },

  selectConversation: async (conversationId: string) => {
    // Abort any in-flight /chat request before switching conversations.
    // Without this, the stale response would append to the newly selected conversation.
    const inflight = get().currentAbortController;
    if (inflight) {
      inflight.abort();
      set({ currentAbortController: null, isChatGenerating: false });
    }

    const conv = get().conversations.find(c => (c.conversation_id || c.id) === conversationId);
    const paperId = conv?.project_id || null;
    let filename = null;
    if (paperId) {
      const paper = get().uploadedHistory.find(h => h.id === paperId);
      filename = paper?.name || `${paperId.replace('paper_', '')}.pdf`;
    }

    const titleToSet = conv?.title || null;
    try {
      localStorage.setItem('active_conversation_id', conversationId);
      if (titleToSet) {
        localStorage.setItem('active_conversation_title', titleToSet);
      }
    } catch {}

    // Asynchronously notify backend of newly selected active conversation
    fetch(`${API_BASE}/conversations/active`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: conversationId })
    }).catch(() => {});

    set({
      isMessagesLoading: true,
      messages: [],
      activeConversationId: conversationId,
      activeConversationTitle: titleToSet,
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
          try {
            localStorage.removeItem('active_conversation_id');
            localStorage.removeItem('active_conversation_title');
          } catch {}
          fetch(`${API_BASE}/conversations/active`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conversation_id: null })
          }).catch(() => {});
          set({ activeConversationId: null, activeConversationTitle: null, messages: [] });
        }
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  },

  updateConversationTitle: async (conversationId: string, newTitle: string) => {
    const cleanTitle = newTitle.trim();
    if (!cleanTitle) return;

    try {
      localStorage.setItem('active_conversation_title', cleanTitle);
    } catch {}

    // Optimistic local update
    set((state) => ({
      activeConversationTitle: cleanTitle,
      conversations: state.conversations.map((c) =>
        (c.conversation_id === conversationId || c.id === conversationId)
          ? { ...c, title: cleanTitle }
          : c
      )
    }));

    try {
      await fetch(`${API_BASE}/conversations/${conversationId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: cleanTitle })
      });
    } catch (err) {
      console.error("Failed to update conversation title:", err);
    }
  },
  sendMessage: async (content: string, includeAttachment: boolean = false) => {
    let currentConvId = get().activeConversationId;
    const { activePaperId } = get();

    // Derive intelligent title from the user prompt (ChatGPT/Claude style: 3-5 words)
    const firstLine = content.trim().split('\n')[0].replace(/^[#\-*\s]+/, '').trim();
    const promptWords = firstLine.split(/\s+/).slice(0, 5).join(' ');
    const derivedTitle = promptWords ? (promptWords.charAt(0).toUpperCase() + promptWords.slice(1)) : 'Research Analysis';

    if (!currentConvId) {
      try {
        currentConvId = await get().createConversation(derivedTitle, activePaperId);
        set({ activeConversationId: currentConvId });
        get().fetchConversations();
      } catch (err: any) {
        console.error("Failed to create conversation:", err);
        return;
      }
    } else {
      // If current thread has a generic placeholder name, upgrade it
      const activeConv = get().conversations.find(c => (c.conversation_id || c.id) === currentConvId);
      if (activeConv) {
        const isGeneric = !activeConv.title || 
          activeConv.title === 'New Research Analysis' || 
          activeConv.title.startsWith('Chat - ') || 
          activeConv.title.startsWith('conv_');
        if (isGeneric && derivedTitle) {
          get().updateConversationTitle(currentConvId, derivedTitle);
        }
      }
    }

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      ...(includeAttachment && activePaperId && get().uploadedFileName
        ? { attachment: { filename: get().uploadedFileName!, paperId: activePaperId } }
        : {}),
    };

    // Create AbortController for this request — stored so selectConversation can cancel it
    const controller = new AbortController();
    set((state) => ({ messages: [...state.messages, userMsg], isChatGenerating: true, currentAbortController: controller }));

    // Streaming assistant placeholder — filled in token by token
    const assistantId = crypto.randomUUID();
    const placeholderMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      model_used: get().selectedModel
    };
    set((state) => ({ messages: [...state.messages, placeholderMsg] }));

    try {
      const response = await fetch(`${API_BASE}/conversations/${currentConvId}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': get().userId || 'e2e_test_user'
        },
        body: JSON.stringify({
          content,
          paper_id: activePaperId,
          model_name: get().selectedModel
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`API returned error status ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let finalMeta: any = null;

      const sseParser = createSseParser({
        onToken: (token) => {
          set((state) => ({
            messages: state.messages.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + token } : m
            )
          }));
        },
        onDone: (meta) => {
          finalMeta = parseChatStreamDone(meta);
          const failoverTarget = finalMeta?.failover_model || resolveFailoverModelId(finalMeta?.model_used);
          if (failoverTarget && failoverTarget !== get().selectedModel) {
            get().setSelectedModel(failoverTarget);
            useLogsStore.getState().addLog(`[Model Router] Auto-failover triggered: switched active model to ${failoverTarget}`, 'warning');
          }
        },
        onError: (errMsg) => {
          throw new Error(errMsg);
        },
        onStatus: (statusText) => {
          set({ streamingStatus: statusText });
        },
        onThought: (thoughtText) => {
          set({ streamingThought: thoughtText });
        },
        onAction: (actionText) => {
          set({ streamingAction: actionText });
        }
      });

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          sseParser.feedLine(line);
        }
      }

      if (buffer) {
        sseParser.feedLine(buffer);
      }
      sseParser.flush();

      // Apply metadata from the done event (set title only once per conversation)
      const existingTitle = get().activeConversationTitle;
      const hasValidTitle = Boolean(existingTitle && !existingTitle.startsWith('conv_') && existingTitle !== 'New Research Analysis' && existingTitle !== 'Research Thread' && existingTitle !== 'Untitled Thread');
      const responseTitle = (!hasValidTitle && finalMeta?.title && !finalMeta.title.startsWith('conv_') && finalMeta.title !== 'New Research Analysis' && finalMeta.title !== 'Research Thread' && finalMeta.title !== 'Untitled Thread')
        ? finalMeta.title
        : null;
      const modelUsed = finalMeta?.model_used || get().selectedModel;
      const failoverTarget = finalMeta?.failover_model || resolveFailoverModelId(modelUsed);
      if (failoverTarget && failoverTarget !== get().selectedModel) {
        get().setSelectedModel(failoverTarget);
        useLogsStore.getState().addLog(`[Model Router] Auto-failover triggered: switched active model to ${failoverTarget}`, 'warning');
      }
      if (!hasValidTitle && responseTitle) {
        try { localStorage.setItem('active_conversation_title', responseTitle); } catch {}
      }

      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === assistantId ? { ...m, model_used: modelUsed } : m
        ),
        isChatGenerating: false,
        streamingStatus: null,
        streamingThought: null,
        streamingAction: null,
        currentAbortController: null,
        ...(responseTitle ? { activeConversationTitle: responseTitle } : {}),
        conversations: responseTitle
          ? state.conversations.map((c) =>
              (c.conversation_id === currentConvId || c.id === currentConvId)
                ? { ...c, title: responseTitle }
                : c
            )
          : state.conversations
      }));
      get().fetchConversations();
      // Silently sync conversation messages to load complete ReACT reasoning trace and canonical IDs
      get().fetchMessages(currentConvId, false);
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('refresh-model-limits'));
      }

    } catch (err: any) {
      if (err?.name === 'AbortError') {
        set((state) => ({
          messages: state.messages.filter((m) => m.id !== assistantId),
          isChatGenerating: false,
          streamingStatus: null,
          streamingThought: null,
          streamingAction: null,
          currentAbortController: null
        }));
        return;
      }
      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === assistantId
            ? { ...m, content: `Error generating response: ${err.message || 'Server error'}` }
            : m
        ),
        isChatGenerating: false,
        streamingStatus: null,
        streamingThought: null,
        streamingAction: null,
        currentAbortController: null
      }));
    }
  },

  regenerateMessage: async (promptContent?: string) => {
    const { messages, activePaperId, selectedModel, userId, activeConversationId } = get();
    let currentConvId = activeConversationId;
    let targetPrompt = promptContent?.trim();
    if (!targetPrompt) {
      for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].role === 'user' && messages[i].content) {
          targetPrompt = messages[i].content.trim();
          break;
        }
      }
    }
    if (!targetPrompt) return;

    if (!currentConvId) {
      await get().sendMessage(targetPrompt);
      return;
    }

    // Remove trailing assistant message (error or previous generation) so it replaces cleanly
    let updatedMsgs = [...messages];
    if (updatedMsgs.length > 0 && updatedMsgs[updatedMsgs.length - 1].role === 'assistant') {
      updatedMsgs = updatedMsgs.slice(0, -1);
    }

    set({ messages: updatedMsgs, isChatGenerating: true });

    // Create AbortController for this regenerate request
    const controller = new AbortController();
    set({ currentAbortController: controller });

    // Streaming placeholder for regenerated response
    const assistantId = crypto.randomUUID();
    const placeholderMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      model_used: selectedModel
    };
    set((state) => ({ messages: [...state.messages, placeholderMsg] }));

    try {
      const response = await fetch(`${API_BASE}/conversations/${currentConvId}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId || 'e2e_test_user'
        },
        body: JSON.stringify({
          content: targetPrompt,
          paper_id: activePaperId,
          model_name: selectedModel
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`API returned error status ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let finalMeta: any = null;

      const sseParser = createSseParser({
        onToken: (token) => {
          set((state) => ({
            messages: state.messages.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + token } : m
            )
          }));
        },
        onDone: (meta) => {
          finalMeta = parseChatStreamDone(meta);
          const failoverTarget = finalMeta?.failover_model || resolveFailoverModelId(finalMeta?.model_used);
          if (failoverTarget && failoverTarget !== get().selectedModel) {
            get().setSelectedModel(failoverTarget);
            useLogsStore.getState().addLog(`[Model Router] Auto-failover triggered: switched active model to ${failoverTarget}`, 'warning');
          }
        },
        onError: (errMsg) => {
          throw new Error(errMsg);
        },
        onStatus: (statusText) => {
          set({ streamingStatus: statusText });
        },
        onThought: (thoughtText) => {
          set({ streamingThought: thoughtText });
        },
        onAction: (actionText) => {
          set({ streamingAction: actionText });
        }
      });

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          sseParser.feedLine(line);
        }
      }

      if (buffer) {
        sseParser.feedLine(buffer);
      }
      sseParser.flush();

      const existingTitle = get().activeConversationTitle;
      const hasValidTitle = Boolean(existingTitle && !existingTitle.startsWith('conv_') && existingTitle !== 'New Research Analysis' && existingTitle !== 'Research Thread' && existingTitle !== 'Untitled Thread');
      const responseTitle = (!hasValidTitle && finalMeta?.title && !finalMeta.title.startsWith('conv_') && finalMeta.title !== 'New Research Analysis' && finalMeta.title !== 'Research Thread' && finalMeta.title !== 'Untitled Thread')
        ? finalMeta.title
        : null;
      const modelUsed = finalMeta?.model_used || selectedModel;
      const failoverTarget = finalMeta?.failover_model || resolveFailoverModelId(modelUsed);
      if (failoverTarget && failoverTarget !== get().selectedModel) {
        get().setSelectedModel(failoverTarget);
        useLogsStore.getState().addLog(`[Model Router] Auto-failover triggered: switched active model to ${failoverTarget}`, 'warning');
      }
      if (!hasValidTitle && responseTitle) {
        try { localStorage.setItem('active_conversation_title', responseTitle); } catch {}
      }

      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === assistantId ? { ...m, model_used: modelUsed } : m
        ),
        isChatGenerating: false,
        streamingStatus: null,
        streamingThought: null,
        streamingAction: null,
        currentAbortController: null,
        ...(responseTitle ? { activeConversationTitle: responseTitle } : {}),
        conversations: responseTitle
          ? state.conversations.map((c) =>
              (c.conversation_id === currentConvId || c.id === currentConvId)
                ? { ...c, title: responseTitle }
                : c
            )
          : state.conversations
      }));
      get().fetchConversations();
      get().fetchMessages(currentConvId, false);
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('refresh-model-limits'));
      }

    } catch (err: any) {
      if (err?.name === 'AbortError') {
        set((state) => ({
          messages: state.messages.filter((m) => m.id !== assistantId),
          isChatGenerating: false,
          streamingStatus: null,
          streamingThought: null,
          streamingAction: null,
          currentAbortController: null
        }));
        return;
      }
      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === assistantId
            ? { ...m, content: `Error generating response: ${err.message || 'Server error'}` }
            : m
        ),
        isChatGenerating: false,
        streamingStatus: null,
        streamingThought: null,
        streamingAction: null,
        currentAbortController: null
      }));
    }
  },
});
