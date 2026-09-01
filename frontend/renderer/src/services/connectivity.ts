import { useLogsStore } from '../store/logsStore';

// Expose checks for Electron environment
const isElectron = typeof window !== 'undefined' && (!!window.mascotAPI || window.location.protocol === 'file:');

/**
 * Dynamically resolves the API Base URL.
 * In standard browser development (Vite), relative path '/api' is proxied to http://localhost:8000.
 * In Electron or production build where React runs under the file:// protocol, it points directly to http://localhost:8000.
 */
export const getApiBase = (): string => {
  if (isElectron) {
    return 'http://localhost:8000';
  }
  return '/api';
};

// Response Interfaces
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model_used?: string;
}

export interface AuthResponse {
  user_id: string;
  username: string;
  email: string;
}

export interface UploadResponse {
  job_id: string;
  paper_id: string;
  status: string;
}

export interface ExtractionStatus {
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  logs: string[];
  report?: string;
  error?: string;
}

/**
 * Service class consolidating all backend communication layer endpoints.
 */
export const connectivityService = {
  /**
   * Post local auth details to register or authenticate a developer profile.
   */
  async loginLocalUser(username: string, email: string): Promise<AuthResponse> {
    const response = await fetch(`${getApiBase()}/auth/local-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, email })
    });
    if (!response.ok) {
      throw new Error(`Auth failed: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Creates a new conversation thread session for history tracking.
   */
  async createConversation(userId: string, title: string, projectId: string | null = null): Promise<string> {
    const response = await fetch(`${getApiBase()}/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        title,
        project_id: projectId
      })
    });
    if (!response.ok) {
      throw new Error(`Failed to create conversation: ${response.statusText}`);
    }
    const data = await response.json();
    return data.conversation_id;
  },

  /**
   * Retrieves historical messages from a conversation thread session.
   */
  async fetchMessages(conversationId: string): Promise<ChatMessage[]> {
    const response = await fetch(`${getApiBase()}/conversations/${conversationId}`);
    if (!response.ok) {
      throw new Error(`Failed to load messages: ${response.statusText}`);
    }
    const data = await response.json();
    return data.messages.map((m: any) => ({
      id: m.message_id || Math.random().toString(36).substring(7),
      role: m.role,
      content: m.content,
      model_used: m.model_used
    }));
  },

  /**
   * Sends user prompt message and streams/fetches LLM response.
   */
  async sendMessage(
    conversationId: string,
    userId: string,
    content: string,
    paperId: string | null,
    modelName: string
  ): Promise<ChatMessage> {
    const response = await fetch(`${getApiBase()}/conversations/${conversationId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId
      },
      body: JSON.stringify({
        content,
        paper_id: paperId,
        model_name: modelName
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.statusText} (${response.status})`);
    }

    const data = await response.json();
    return {
      id: Math.random().toString(36).substring(7),
      role: 'assistant',
      content: data.response,
      model_used: data.model_used
    };
  },

  /**
   * Uploads a paper PDF via multipart form upload.
   */
  async uploadPaper(file: File, modelName: string): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${getApiBase()}/history/upload?model_name=${modelName}`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || `Upload failed with status ${response.status}`);
    }

    return response.json();
  },

  /**
   * Fetches the current run/job status for a pipeline run.
   */
  async getExtractionStatus(jobId: string): Promise<ExtractionStatus> {
    const response = await fetch(`${getApiBase()}/extraction/status/${jobId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch job status: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Setup EventSource stream connection to receive pipeline milestone events.
   * Exposes standard listeners that link directly into local Zustand stores.
   */
  streamExtraction(
    jobId: string,
    onLogEvent: (eventTag: string, progress: number, status: string) => void,
    onComplete: (report: string) => void,
    onFailure: (error: string) => void
  ): EventSource {
    const eventSource = new EventSource(`${getApiBase()}/extraction/stream/${jobId}`);
    const { addLog } = useLogsStore.getState();

    const handleEvent = (e: MessageEvent, logTag: string) => {
      try {
        const data = JSON.parse(e.data || '{}');
        onLogEvent(logTag, data.progress, data.status);
      } catch (err) {
        console.error("Failed to parse SSE payload", err);
      }
    };

    // Bind all registered LangGraph section extraction milestones
    eventSource.addEventListener('SECTION_DETECTED', (e) => handleEvent(e, 'SECTION_DETECTED'));
    eventSource.addEventListener('RAG_READY', (e) => handleEvent(e, 'RAG_READY'));
    eventSource.addEventListener('ANALYSIS_STARTED', (e) => handleEvent(e, 'ANALYSIS_STARTED'));
    eventSource.addEventListener('CODE_GENERATION_STARTED', (e) => handleEvent(e, 'CODE_GENERATION_STARTED'));
    eventSource.addEventListener('VERIFICATION_STARTED', (e) => handleEvent(e, 'VERIFICATION_STARTED'));
    
    // Bind terminal completion event
    eventSource.addEventListener('COMPLETED', async () => {
      eventSource.close();
      try {
        // Fetch status directly to retrieve the markdown report content
        const statusResp = await fetch(`${getApiBase()}/extraction/status/${jobId}`);
        const statusData = await statusResp.json();
        onComplete(statusData.report || '# Analysis Completed successfully.');
      } catch {
        onComplete('# Analysis Complete.\nCheck generated workspace outputs.');
      }
    });

    eventSource.addEventListener('ERROR', (e: MessageEvent) => {
      eventSource.close();
      try {
        const data = JSON.parse(e.data || '{}');
        onFailure(data.error || 'Extraction process failed');
      } catch {
        onFailure('Extraction process failed');
      }
    });

    eventSource.onerror = () => {
      eventSource.close();
      // Avoid triggering failure on standard channel closure
      addLog('[System] SSE connection closed.', 'info');
    };

    return eventSource;
  }
};
