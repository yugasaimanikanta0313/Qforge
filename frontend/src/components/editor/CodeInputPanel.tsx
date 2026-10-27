import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { useAgentStore } from '../../store/agentStore';
import { useAgentSession } from '../../hooks/useAgentSession';
import { Language } from '../../types/agent';
import {
  Play,
  Square,
  Code2,
  Github,
  History,
  X,
  FileCode,
  Layers,
  Sparkles,
} from 'lucide-react';
import { RepoTreeModal } from '../github/RepoTreeModal';
import { PromptHistoryDrawer } from '../history/PromptHistoryDrawer';

export const CodeInputPanel: React.FC = () => {
  const {
    language,
    rawInput,
    setLanguage,
    setRawInput,
    isExecuting,
    openTabs,
    activeTabPath,
    setActiveTab,
    closeTab,
    isExplorerOpen,
    toggleExplorer,
    repoData,
  } = useAgentStore();
  const { startSession, stopSession } = useAgentSession();

  const [isRepoModalOpen, setIsRepoModalOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLang = e.target.value as Language;
    setLanguage(newLang);
  };

  return (
    <>
      <div className="flex flex-col h-full bg-slate-950 border border-slate-800 rounded-lg overflow-hidden shadow-xl">
        {/* Row 1: Primary Action & Execution Header */}
        <div className="flex-shrink-0 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <button
              onClick={toggleExplorer}
              title="Toggle IDE File Explorer"
              className={`p-1.5 rounded transition ${
                isExplorerOpen
                  ? 'bg-sky-950 text-sky-400 border border-sky-800/80'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-4 h-4" />
            </button>

            <Code2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
            <h3 className="font-semibold text-xs text-slate-200 truncate">
              Source Code
            </h3>
          </div>

          {/* PROMINENT RUN TEST SYNTHESIS BUTTON - ALWAYS VISIBLE */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {isExecuting ? (
              <button
                onClick={stopSession}
                className="px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-md text-xs font-bold flex items-center gap-2 shadow-lg shadow-rose-950/40 transition active:scale-95 animate-pulse"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Stop Agent</span>
              </button>
            ) : (
              <button
                onClick={() => startSession()}
                className="px-5 py-2 bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-500 hover:from-emerald-500 hover:to-teal-400 text-white rounded-md text-xs font-extrabold flex items-center gap-2 shadow-xl shadow-emerald-950/60 transition transform hover:scale-[1.02] active:scale-[0.98] border border-emerald-400/30"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run Test Synthesis</span>
              </button>
            )}
          </div>
        </div>

        {/* Row 2: IDE Tabs and Toolbar */}
        <div className="flex-shrink-0 px-3 py-1.5 border-b border-slate-800/80 flex items-center justify-between bg-slate-950 gap-2 overflow-x-auto text-xs">
          {/* Tabs */}
          <div className="flex items-center gap-1 min-w-0 overflow-x-auto scrollbar-none">
            {openTabs.map((tab) => {
              const isActive = tab.path === activeTabPath;
              return (
                <div
                  key={tab.path}
                  onClick={() => setActiveTab(tab.path)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded cursor-pointer transition select-none flex-shrink-0 ${
                    isActive
                      ? 'bg-slate-850 text-sky-300 border border-slate-700/80 font-medium'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-slate-900'
                  }`}
                >
                  <FileCode className="w-3 h-3 text-sky-400" />
                  <span className="truncate max-w-[120px]">{tab.name}</span>
                  {tab.testStatus === 'PASS' && (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" title="Tests Passed" />
                  )}
                  {tab.testStatus === 'FAIL' && (
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400" title="Tests Failed" />
                  )}
                  {openTabs.length > 1 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        closeTab(tab.path);
                      }}
                      className="hover:text-rose-400 text-slate-500 rounded p-0.5"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Right Toolbar Controls */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <button
              onClick={() => setIsRepoModalOpen(true)}
              className="flex items-center gap-1 px-2 py-1 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 rounded text-[11px] transition"
              title="Import from GitHub"
            >
              <Github className="w-3.5 h-3.5 text-slate-400" />
              <span>GitHub</span>
            </button>

            <button
              onClick={() => setIsHistoryOpen(true)}
              className="flex items-center gap-1 px-2 py-1 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 rounded text-[11px] transition"
              title="Prompt History"
            >
              <History className="w-3.5 h-3.5 text-sky-400" />
              <span>History</span>
            </button>

            <select
              value={language}
              onChange={handleLanguageChange}
              disabled={isExecuting}
              className="bg-slate-900 border border-slate-800 text-[11px] text-slate-300 rounded px-2 py-1 focus:outline-none focus:border-sky-500 font-mono"
            >
              <option value="python">Python (pytest)</option>
              <option value="typescript">TypeScript (Jest)</option>
              <option value="javascript">JavaScript (Jest)</option>
              <option value="java">Java (JUnit 5)</option>
              <option value="go">Go (testing)</option>
              <option value="rust">Rust (cargo test)</option>
              <option value="csharp">C# (xUnit)</option>
              <option value="sql">SQL (Assertions)</option>
            </select>
          </div>
        </div>

        {/* Monaco Editor Container */}
        <div className="flex-1 min-h-0 relative w-full">
          <Editor
            height="100%"
            language={language === 'csharp' ? 'csharp' : language}
            theme="vs-dark"
            value={rawInput}
            onChange={(val) => setRawInput(val || '')}
            options={{
              minimap: { enabled: false },
              fontSize: 13,
              lineNumbers: 'on',
              scrollBeyondLastLine: true,
              automaticLayout: true,
              tabSize: 4,
              padding: { top: 8, bottom: 28 },
            }}
          />
        </div>
      </div>

      {/* GitHub Repo Modal */}
      <RepoTreeModal
        isOpen={isRepoModalOpen}
        onClose={() => setIsRepoModalOpen(false)}
      />

      {/* Prompt History Drawer */}
      <PromptHistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
      />
    </>
  );
};
