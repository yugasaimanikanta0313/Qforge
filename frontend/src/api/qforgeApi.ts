import axios from 'axios';
import { AuditLogRecord, SessionMeta } from '../types/agent';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const qforgeApi = {
  getHealth: async () => {
    const res = await api.get('/health');
    return res.data;
  },

  getAuditLogs: async (limit: number = 50): Promise<{ logs: AuditLogRecord[]; count: number }> => {
    const res = await api.get('/audit/logs', { params: { limit } });
    return res.data;
  },

  getSessionTrace: async (sessionId: string) => {
    const res = await api.get(`/audit/${sessionId}/trace`);
    return res.data;
  },

  createSession: async (code: string, language: string) => {
    const res = await api.post('/sessions', { code, language });
    return res.data;
  },

  listSessions: async () => {
    const res = await api.get('/sessions');
    return res.data;
  },

  getGitHubTree: async (repo: string, branch?: string, token?: string) => {
    const res = await api.post('/github/tree', { repo, branch, token });
    return res.data;
  },

  getGitHubFile: async (owner: string, repo: string, sha?: string, path?: string, token?: string) => {
    const res = await api.post('/github/file', { owner, repo, sha, path, token });
    return res.data;
  },

  getChatHistory: async (limit: number = 50) => {
    const res = await api.get('/sessions/history', { params: { limit } });
    return res.data;
  },

  getSessionConversation: async (sessionId: string) => {
    const res = await api.get(`/sessions/history/${sessionId}`);
    return res.data;
  },
};
