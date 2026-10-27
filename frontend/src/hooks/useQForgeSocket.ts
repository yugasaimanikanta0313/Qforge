import { useRef, useCallback } from 'react';
import { useAgentStore } from '../store/agentStore';
import { TelemetryEvent } from '../types/agent';

export const useQForgeSocket = () => {
  const socketRef = useRef<WebSocket | null>(null);
  const resolveRef = useRef<((result: { status: 'PASS' | 'FAIL'; test_suite?: string }) => void) | null>(null);

  const {
    addEvent,
    setActiveNode,
    setRepairCycle,
    setFinalResult,
    setIsExecuting,
  } = useAgentStore();

  const connectAndRun = useCallback(
    (sessionId: string, code: string, language: string): Promise<{ status: 'PASS' | 'FAIL'; test_suite?: string }> => {
      return new Promise((resolve) => {
        // Close and resolve any pending previous socket
        if (resolveRef.current) {
          resolveRef.current({ status: 'FAIL' });
          resolveRef.current = null;
        }

        if (socketRef.current) {
          socketRef.current.close();
          socketRef.current = null;
        }

        resolveRef.current = resolve;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/qforge/${sessionId}`;

        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;
        setIsExecuting(true);

        ws.onopen = () => {
          // Send code execution payload
          ws.send(JSON.stringify({ code, language, session_id: sessionId }));
        };

        ws.onmessage = (event) => {
          try {
            const payload: TelemetryEvent = JSON.parse(event.data);
            payload.id = `${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;
            payload.timestamp = new Date().toLocaleTimeString();

            addEvent(payload);

            if (payload.event === 'node_start' && payload.node) {
              setActiveNode(payload.node);
            } else if (payload.event === 'repair_cycle' && payload.cycle !== undefined) {
              setRepairCycle(payload.cycle);
            } else if (payload.event === 'final_result') {
              setFinalResult({
                test_suite: payload.test_suite,
                status: payload.status,
                model_used: payload.model_used,
                routing_path: payload.routing_path,
                complexity_score: payload.complexity_score,
                repair_cycles_used: payload.repair_cycles_used,
              });

              if (resolveRef.current) {
                resolveRef.current({
                  status: payload.status || 'FAIL',
                  test_suite: payload.test_suite,
                });
                resolveRef.current = null;
              }
            } else if (payload.event === 'error') {
              setIsExecuting(false);
              setActiveNode(null);
              if (resolveRef.current) {
                resolveRef.current({ status: 'FAIL' });
                resolveRef.current = null;
              }
            }
          } catch (err) {
            console.error('Failed to parse WebSocket frame', err);
          }
        };

        ws.onerror = (err) => {
          console.error('WebSocket error', err);
          setIsExecuting(false);
          setActiveNode(null);
          if (resolveRef.current) {
            resolveRef.current({ status: 'FAIL' });
            resolveRef.current = null;
          }
        };

        ws.onclose = () => {
          setIsExecuting(false);
          setActiveNode(null);
          if (resolveRef.current) {
            resolveRef.current({ status: 'FAIL' });
            resolveRef.current = null;
          }
        };
      });
    },
    [addEvent, setActiveNode, setRepairCycle, setFinalResult, setIsExecuting]
  );

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    if (resolveRef.current) {
      resolveRef.current({ status: 'FAIL' });
      resolveRef.current = null;
    }
  }, []);

  return { connectAndRun, disconnect };
};
