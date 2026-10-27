import React, { useEffect, useState } from 'react';
import { qforgeApi } from '../../api/qforgeApi';
import { ChatHistoryTurn, Language } from '../../types/agent';
import { useAgentStore } from '../../store/agentStore';
import { History, X, Clock, CheckCircle2, AlertCircle, ArrowUpRight } from 'lucide-react';
import { LoadingSpinner } from '../shared/LoadingSpinner';

interface PromptHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PromptHistoryDrawer: React.FC<PromptHistoryDrawerProps> = ({
  isOpen,
  onClose,
}) => {
  const { setRawInput, setLanguage, setFinalResult } = useAgentStore();
  const [history, setHistory] = useState<ChatHistoryTurn[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await qforgeApi.getChatHistory(30);
      setHistory(data.history || []);
    } catch (err) {
      console.error('Failed to load history', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTurn = (turn: ChatHistoryTurn) => {
    setRawInput(turn.user_prompt);
    setLanguage(turn.language as Language);
    if (turn.generated_suite) {
      setFinalResult({
        test_suite: turn.generated_suite,
        status: turn.validation_status,
        model_used: turn.model_used,
        repair_cycles_used: turn.repair_cycles,
      });
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border-l border-slate-800 w-full max-w-md h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-sky-400" />
            <h2 className="text-sm font-semibold text-slate-100">
              Prompt & Run History
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition p-1 rounded hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-48 gap-3 text-slate-400">
              <LoadingSpinner size="md" />
              <p className="text-xs">Loading past test generations...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-xs gap-2">
              <Clock className="w-8 h-8 text-slate-600" />
              <p>No previous prompt sessions recorded yet.</p>
            </div>
          ) : (
            history.map((turn, idx) => (
              <div
                key={turn.session_id + idx}
                onClick={() => handleSelectTurn(turn)}
                className="p-3 bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-lg cursor-pointer transition hover:bg-slate-850 group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-sky-400 uppercase">
                      {turn.language}
                    </span>
                    <span className="text-[11px] font-mono text-slate-500">
                      #{turn.session_id}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs">
                    {turn.validation_status === 'PASS' ? (
                      <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        PASS
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                        <AlertCircle className="w-3.5 h-3.5" />
                        FAIL
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-xs text-slate-300 font-mono line-clamp-2 bg-slate-900/60 p-1.5 rounded border border-slate-800/60">
                  {turn.user_prompt.trim().slice(0, 150)}
                </p>

                <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                  <span>
                    Model: <strong className="text-slate-400">{turn.model_used.split(':')[0]}</strong>
                    {turn.repair_cycles > 0 && ` • Repair #${turn.repair_cycles}`}
                  </span>
                  <span className="flex items-center gap-1 text-sky-400 group-hover:underline">
                    Restore <ArrowUpRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500 bg-slate-950/70">
          <span>{history.length} past runs indexed</span>
          <button
            onClick={loadHistory}
            className="text-xs text-sky-400 hover:underline"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  );
};
