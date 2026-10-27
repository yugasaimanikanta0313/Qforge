import { useCallback } from 'react';
import { useAgentStore } from '../store/agentStore';
import { useQForgeSocket } from './useQForgeSocket';
import { Language } from '../types/agent';

export const useAgentSession = () => {
  const { sessionId, isExecuting } = useAgentStore();
  const { connectAndRun, disconnect } = useQForgeSocket();

  const startSession = useCallback(
    async (
      codeOverride?: string,
      languageOverride?: Language
    ): Promise<{ status: 'PASS' | 'FAIL'; test_suite?: string }> => {
      const store = useAgentStore.getState();
      const codeToRun = codeOverride !== undefined ? codeOverride : store.rawInput;
      const langToRun = languageOverride !== undefined ? languageOverride : store.language;
      const newSessionId = `sess-${Date.now().toString(36)}-${Math.random().toString(36).substr(2, 4)}`;

      store.setSessionId(newSessionId);
      store.resetSession();

      return await connectAndRun(newSessionId, codeToRun, langToRun);
    },
    [connectAndRun]
  );

  const stopSession = useCallback(() => {
    disconnect();
  }, [disconnect]);

  return {
    sessionId,
    isExecuting,
    startSession,
    stopSession,
  };
};
