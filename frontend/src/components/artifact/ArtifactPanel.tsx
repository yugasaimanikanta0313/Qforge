import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { useAgentStore } from '../../store/agentStore';
import { Copy, Download, Check, Sparkles, AlertOctagon } from 'lucide-react';
import { StatusPill } from '../shared/StatusPill';
import { RepairBadge } from '../telemetry/RepairBadge';

export const ArtifactPanel: React.FC = () => {
  const {
    finalTestSuite,
    finalStatus,
    modelUsed,
    routingPath,
    complexityScore,
    repairCycle,
    language,
    isExecuting,
  } = useAgentStore();

  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!finalTestSuite) return;
    navigator.clipboard.writeText(finalTestSuite);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!finalTestSuite) return;
    const ext = language === 'python' ? 'py' : 'sql';
    const blob = new Blob([finalTestSuite], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `test_suite_${Date.now()}.${ext}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 border border-slate-800 rounded-lg overflow-hidden">
      {/* Header Bar */}
      <div className="flex-shrink-0 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <h3 className="font-semibold text-xs text-slate-200">Verified Test Artifact</h3>
          {finalStatus && <StatusPill status={finalStatus} />}
          {routingPath && <StatusPill status={routingPath} />}
          <RepairBadge cycle={repairCycle} />
        </div>

        <div className="flex items-center gap-2">
          {finalTestSuite && (
            <>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs transition"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>

              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs transition"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Artifact Metadata Info Bar */}
      {finalTestSuite && (
        <div className="flex-shrink-0 px-4 py-2 bg-slate-900/30 border-b border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <div>
            Synthesized by: <span className="text-purple-300 font-mono">{modelUsed}</span>
          </div>
          {complexityScore !== null && (
            <div>
              Complexity: <span className="text-sky-300 font-semibold">{complexityScore}/10</span>
            </div>
          )}
        </div>
      )}

      {/* Editor Body */}
      <div className="flex-1 min-h-0 relative w-full">
        {finalTestSuite ? (
          <Editor
            height="100%"
            language={language}
            theme="vs-dark"
            value={finalTestSuite}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              fontSize: 13,
              lineNumbers: 'on',
              scrollBeyondLastLine: true,
              automaticLayout: true,
              padding: { top: 8, bottom: 28 },
            }}
          />
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs p-6 text-center">
            {isExecuting ? (
              <>
                <Sparkles className="w-8 h-8 stroke-1 mb-2 text-purple-400 animate-pulse" />
                <p>Generating compilation-verified test suite...</p>
                <p className="text-slate-600 mt-1">Applying enterprise guidelines and AST validation</p>
              </>
            ) : (
              <>
                <AlertOctagon className="w-8 h-8 stroke-1 mb-2 text-slate-600" />
                <p>No test artifact generated yet.</p>
                <p className="text-slate-600 mt-1">Submit your code to generate a verified test suite.</p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
