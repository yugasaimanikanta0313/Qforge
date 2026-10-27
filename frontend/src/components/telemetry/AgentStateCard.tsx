import React from 'react';
import { TelemetryEvent } from '../../types/agent';
import { StatusPill } from '../shared/StatusPill';
import {
  CheckCircle2,
  AlertCircle,
  Cpu,
  Cloud,
  Terminal,
  RefreshCw,
  Sparkles,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

interface AgentStateCardProps {
  event: TelemetryEvent;
}

export const AgentStateCard: React.FC<AgentStateCardProps> = ({ event }) => {
  const { node, message, data, timestamp } = event;

  // Extract errors from data.errors OR event.errors (for repair_cycle)
  const errors = data?.errors || event.errors || [];
  const repairCycleNum = event.cycle !== undefined ? event.cycle : data?.repair_cycle;

  // 1. Dedicated Card for Self-Heal Repair Loop Events
  if (event.event === 'repair_cycle' || (node === 'GENERATOR' && repairCycleNum && repairCycleNum > 0)) {
    return (
      <div className="bg-amber-950/30 border border-amber-500/50 rounded-lg p-3 text-xs shadow-md shadow-amber-950/20 animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="p-1 rounded bg-amber-500/20 text-amber-400">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            </div>
            <span className="font-bold text-amber-300 uppercase tracking-wide">
              Self-Heal Loop #{repairCycleNum || 1}
            </span>
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-900/60 text-amber-300 font-mono">
              Auto-Healing Active
            </span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">{timestamp}</span>
        </div>

        <p className="text-slate-300 mb-2 leading-relaxed">
          {message || 'Validator detected syntax or semantic errors. Re-routing error trace to Generator for automated repair.'}
        </p>

        {errors.length > 0 && (
          <div className="mt-2 bg-slate-950/80 border border-amber-500/30 rounded p-2 text-amber-200">
            <div className="flex items-center gap-1.5 font-semibold text-rose-400 mb-1">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Errors Fed Back to Generator:</span>
            </div>
            <ul className="list-disc pl-4 space-y-1 font-mono text-[11px] text-slate-300">
              {errors.map((err, i) => (
                <li key={i} className="text-rose-300">{err}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-2 pt-2 border-t border-amber-500/20 flex items-center gap-2 text-[11px] text-slate-400">
          <span className="text-rose-400 font-medium">VALIDATOR (Failed)</span>
          <ArrowRight className="w-3 h-3 text-amber-400" />
          <span className="text-amber-300 font-medium">REPAIR PROMPT</span>
          <ArrowRight className="w-3 h-3 text-amber-400" />
          <span className="text-sky-300 font-medium">GENERATOR (Retry #{repairCycleNum || 1})</span>
        </div>
      </div>
    );
  }

  // 2. Final Result Card
  if (event.event === 'final_result') {
    const isPass = event.status === 'PASS';
    return (
      <div
        className={`border rounded-lg p-3 text-xs shadow-md animate-in fade-in ${
          isPass
            ? 'bg-emerald-950/30 border-emerald-500/50 text-emerald-200'
            : 'bg-rose-950/30 border-rose-500/50 text-rose-200'
        }`}
      >
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-2">
            {isPass ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400" />
            )}
            <span className="font-bold uppercase tracking-wider text-slate-100">
              {isPass ? 'Test Suite Certified (PASS)' : 'Synthesis Incomplete (FAIL)'}
            </span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">{timestamp}</span>
        </div>

        <p className="text-slate-300 mb-2">{message}</p>

        <div className="flex flex-wrap items-center gap-3 text-[11px] bg-slate-950/70 p-2 rounded border border-slate-800">
          <span>
            Status: <strong className={isPass ? 'text-emerald-400' : 'text-rose-400'}>{event.status}</strong>
          </span>
          {event.complexity_score !== undefined && (
            <span>
              Complexity: <strong className="text-sky-300">{event.complexity_score}/10</strong>
            </span>
          )}
          {event.model_used && (
            <span>
              Model: <code className="text-purple-300">{event.model_used}</code>
            </span>
          )}
          {event.repair_cycles_used !== undefined && (
            <span>
              Repair Cycles: <strong className="text-amber-400">{event.repair_cycles_used}</strong>
            </span>
          )}
        </div>
      </div>
    );
  }

  const getNodeIcon = () => {
    switch (node) {
      case 'ROUTER':
        return <Cpu className="w-4 h-4 text-sky-400" />;
      case 'GENERATOR':
        return data?.routing_path === 'cloud' ? (
          <Cloud className="w-4 h-4 text-purple-400" />
        ) : (
          <Terminal className="w-4 h-4 text-emerald-400" />
        );
      case 'VALIDATOR':
        return data?.validation_status === 'FAIL' ? (
          <AlertCircle className="w-4 h-4 text-rose-400" />
        ) : (
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        );
      default:
        return <Sparkles className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs transition-all hover:border-slate-700">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          {getNodeIcon()}
          <span className="font-semibold text-slate-200">
            {node || event.event.toUpperCase()}
          </span>
          {data?.routing_path && <StatusPill status={data.routing_path} />}
          {data?.validation_status && <StatusPill status={data.validation_status} />}
        </div>
        <span className="text-[10px] text-slate-500 font-mono">{timestamp}</span>
      </div>

      {message && <p className="text-slate-400 mb-2 leading-relaxed">{message}</p>}

      {/* Node-specific metadata displays */}
      {data?.complexity_score !== undefined && (
        <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 bg-slate-950/70 p-2 rounded border border-slate-800/80">
          <span>
            Complexity: <strong className="text-sky-300">{data.complexity_score}/10</strong>
          </span>
          <span>
            Type: <strong className="text-slate-300">{data.ast_fingerprint?.code_type || 'code'}</strong>
          </span>
          <span>
            Guidelines: <strong className="text-slate-300">{data.context_chunks_count || 0} chunks</strong>
          </span>
        </div>
      )}

      {data?.model_used && (
        <div className="text-[11px] text-slate-400 bg-slate-950/70 p-2 rounded flex justify-between border border-slate-800/80">
          <span>
            Model: <code className="text-purple-300">{data.model_used}</code>
          </span>
          {data.repair_cycle !== undefined && data.repair_cycle > 0 && (
            <span className="text-amber-400 font-medium">Repair #{data.repair_cycle}</span>
          )}
        </div>
      )}

      {errors.length > 0 && (
        <div className="mt-2 text-xs bg-rose-950/40 border border-rose-900/50 rounded p-2 text-rose-300">
          <p className="font-semibold mb-1 text-rose-300">Syntax / Logic Errors Detected:</p>
          <ul className="list-disc pl-4 space-y-0.5 font-mono text-[11px]">
            {errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
