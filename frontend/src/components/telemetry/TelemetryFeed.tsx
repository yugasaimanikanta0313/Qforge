import React, { useEffect, useRef, useState } from 'react';
import { useAgentStore } from '../../store/agentStore';
import { AgentStateCard } from './AgentStateCard';
import { Activity, Brain, BrainCircuit, RefreshCw, Terminal, Sparkles, ArrowDown } from 'lucide-react';

export const TelemetryFeed: React.FC = () => {
  const { events, isExecuting, activeNode, repairCycle, language, routingPath } = useAgentStore();
  const feedContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll on new telemetry events
  useEffect(() => {
    if (autoScroll && feedContainerRef.current) {
      feedContainerRef.current.scrollTop = feedContainerRef.current.scrollHeight;
    }
  }, [events, isExecuting, activeNode, repairCycle, autoScroll]);

  const getThinkingDetails = () => {
    if (repairCycle > 0) {
      return {
        title: `Self-Healing Loop #${repairCycle} Active`,
        desc: 'Analyzing validator errors and regenerating corrected test code...',
        color: 'text-amber-400 border-amber-500/40 bg-amber-950/20',
        glow: 'shadow-amber-500/20',
        icon: <RefreshCw className="w-5 h-5 text-amber-400 animate-spin" />,
      };
    }
    switch (activeNode) {
      case 'ROUTER':
        return {
          title: 'Agent Thinking: Routing & AST Analysis',
          desc: 'Parsing abstract syntax tree, computing complexity, and querying FAISS guidelines...',
          color: 'text-sky-400 border-sky-500/40 bg-sky-950/20',
          glow: 'shadow-sky-500/20',
          icon: <BrainCircuit className="w-5 h-5 text-sky-400 animate-pulse" />,
        };
      case 'GENERATOR':
        return {
          title: `Agent Thinking: Synthesizing ${language.toUpperCase()} Tests`,
          desc: `Generating test suite via ${routingPath === 'cloud' ? 'Gemini 2.5 Flash' : 'Ollama Local LLM'} with boundary assertions...`,
          color: 'text-purple-400 border-purple-500/40 bg-purple-950/20',
          glow: 'shadow-purple-500/20',
          icon: <Brain className="w-5 h-5 text-purple-400 animate-pulse" />,
        };
      case 'VALIDATOR':
        return {
          title: 'Agent Thinking: Deterministic Syntax Audit',
          desc: 'Executing AST compiler checks and running automated quality verification...',
          color: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/20',
          glow: 'shadow-emerald-500/20',
          icon: <Activity className="w-5 h-5 text-emerald-400 animate-pulse" />,
        };
      default:
        return {
          title: 'Agent Orchestration Active',
          desc: 'Connecting to QForge LangGraph state machine...',
          color: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/20',
          glow: 'shadow-emerald-500/20',
          icon: <Sparkles className="w-5 h-5 text-emerald-400 animate-pulse" />,
        };
    }
  };

  const thinking = getThinkingDetails();

  return (
    <div className="flex flex-col h-full bg-slate-950 border border-slate-800 rounded-lg overflow-hidden shadow-lg">
      {/* Top Header */}
      <div className="flex-shrink-0 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h3 className="font-semibold text-xs text-slate-200">Agent Telemetry Feed</h3>
        </div>

        <div className="flex items-center gap-2">
          {isExecuting && (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              Live Thinking
            </span>
          )}

          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-1 rounded text-xs transition ${
              autoScroll ? 'text-sky-400 bg-sky-950/60' : 'text-slate-500 hover:text-slate-300'
            }`}
            title={autoScroll ? 'Auto-scroll Enabled' : 'Auto-scroll Disabled'}
          >
            <ArrowDown className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Scrollable Event Feed */}
      <div
        ref={feedContainerRef}
        className="flex-1 min-h-0 p-3.5 pb-16 overflow-y-auto space-y-3 scroll-smooth scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900/50"
      >
        {/* Dynamic Brain Thinking Card when executing */}
        {isExecuting && (
          <div
            className={`border rounded-xl p-3.5 shadow-lg backdrop-blur-sm transition-all duration-300 animate-in fade-in slide-in-from-top-2 ${thinking.color} ${thinking.glow}`}
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/80 shadow-inner">
                {thinking.icon}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold tracking-wide uppercase">
                    {thinking.title}
                  </h4>
                  <span className="text-[10px] font-mono opacity-70">
                    Cycle #{repairCycle}
                  </span>
                </div>

                <p className="text-[11px] text-slate-300 mt-1 leading-relaxed">
                  {thinking.desc}
                </p>

                {/* Animated progress bar */}
                <div className="mt-2.5 w-full bg-slate-900/80 rounded-full h-1.5 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-sky-400 via-emerald-400 to-purple-400 animate-[shimmer_1.5s_infinite] w-full" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {events.length === 0 && !isExecuting && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs gap-3 p-6 text-center">
            <div className="p-3 rounded-full bg-slate-900 border border-slate-800">
              <Brain className="w-7 h-7 text-slate-600 stroke-1" />
            </div>
            <div>
              <p className="font-semibold text-slate-400">Ready for Test Synthesis</p>
              <p className="text-[11px] text-slate-500 mt-1">
                Click <strong>"Run Test Synthesis"</strong> above to observe AST routing, LLM generation, and self-heal repair loops in real time.
              </p>
            </div>
          </div>
        )}

        {/* Render each event card */}
        {events.map((ev) => (
          <AgentStateCard key={ev.id} event={ev} />
        ))}
      </div>
    </div>
  );
};
