/**
 * Centralized API Configuration & Dynamic URL Resolution
 * 
 * Dynamically resolves the backend API Base URL based on runtime environment:
 * - In Electron or file:// protocol: points directly to http://localhost:8000
 * - In standard Vite browser development: uses '/api' proxy or VITE_BACKEND_URL if specified
 */

export const isElectronEnvironment = (): boolean => {
  return typeof window !== 'undefined' && (!!window.mascotAPI || window.location.protocol === 'file:');
};

export const getApiBase = (): string => {
  // Check for environment variable override (e.g. from .env or Vite config)
  const envUrl = typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL;
  if (envUrl) {
    const cleanUrl = envUrl.replace(/\/+$/, '');
    return cleanUrl.endsWith('/api/v1') ? cleanUrl : `${cleanUrl}/api/v1`;
  }

  // Both Electron desktop window and browser dev hit the v1 API root
  return 'http://localhost:8000/api/v1';
};

/**
 * Singleton API Base URL string (always points to /api/v1)
 */
export const API_BASE = getApiBase();

/**
 * Standard API Endpoint Paths
 */
export const API_ENDPOINTS = {
  MODELS: `${API_BASE}/models`,
  LIMITS: `${API_BASE}/models/limits`,
  DUAL_ENGINE: `${API_BASE}/models/dual-engine`,
  PAPERS: `${API_BASE}/papers`,
  PIPELINE_INGEST: `${API_BASE}/pipeline/ingest`,
  CONVERSATIONS: `${API_BASE}/conversations`,
  HARDWARE: `${API_BASE}/hardware/metrics`,
  USER_PROFILE: `${API_BASE}/user/profile`,
  TELEMETRY: `${API_BASE}/telemetry/traces`,
} as const;
