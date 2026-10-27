import React, { useState } from 'react';
import { RepoTreeNode, Language, FileTestStatus } from '../../types/agent';
import { useAgentStore } from '../../store/agentStore';
import { qforgeApi } from '../../api/qforgeApi';
import {
  Folder,
  FolderOpen,
  FileCode,
  ChevronRight,
  ChevronDown,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FolderSync,
  Layers,
  Sparkles,
} from 'lucide-react';

export interface BatchFileItem {
  path: string;
  name: string;
  language: Language;
  content?: string;
  sha?: string;
}

interface RepoExplorerSidebarProps {
  onOpenRepoModal: () => void;
  onRunBatch: (files: BatchFileItem[]) => void;
  onStopBatch?: () => void;
}

interface TreeNodeProps {
  node: RepoTreeNode;
  owner: string;
  repo: string;
  branch: string;
  onOpenFile: (path: string, name: string, lang: Language, sha?: string) => void;
  onTestFolder: (folderNode: RepoTreeNode) => void;
  depth?: number;
}

const TreeNode: React.FC<TreeNodeProps> = ({
  node,
  owner,
  repo,
  branch,
  onOpenFile,
  onTestFolder,
  depth = 0,
}) => {
  const [isOpen, setIsOpen] = useState(depth < 2);
  const { fileTestStatuses, activeTabPath } = useAgentStore();
  const fileStatus: FileTestStatus = fileTestStatuses[node.path] || 'idle';
  const isActive = activeTabPath === node.path;

  const handleClick = () => {
    if (node.type === 'directory') {
      setIsOpen(!isOpen);
    } else {
      const ext = node.name.split('.').pop()?.toLowerCase();
      let detectedLang: Language = node.language || 'python';
      if (ext === 'js' || ext === 'jsx') detectedLang = 'javascript';
      else if (ext === 'ts' || ext === 'tsx') detectedLang = 'typescript';
      else if (ext === 'py') detectedLang = 'python';
      else if (ext === 'java') detectedLang = 'java';
      else if (ext === 'go') detectedLang = 'go';
      else if (ext === 'rs') detectedLang = 'rust';
      else if (ext === 'cs') detectedLang = 'csharp';
      else if (ext === 'sql') detectedLang = 'sql';

      onOpenFile(node.path, node.name, detectedLang, node.sha);
    }
  };

  const renderStatusBadge = () => {
    if (fileStatus === 'running') {
      return (
        <span title="Generating & Validating Tests...">
          <Loader2 className="w-3.5 h-3.5 text-sky-400 animate-spin" />
        </span>
      );
    }
    if (fileStatus === 'PASS') {
      return (
        <span title="Tests Passed and Certified">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        </span>
      );
    }
    if (fileStatus === 'FAIL') {
      return (
        <span title="Validation Failed">
          <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
        </span>
      );
    }
    return null;
  };

  return (
    <div>
      <div
        onClick={handleClick}
        style={{ paddingLeft: `${depth * 14 + 6}px` }}
        className={`group flex items-center justify-between py-1 px-1.5 rounded cursor-pointer transition text-xs select-none ${
          isActive
            ? 'bg-sky-950/80 text-sky-200 border-l-2 border-sky-400 font-medium'
            : 'hover:bg-slate-850/80 text-slate-400 hover:text-slate-200'
        }`}
      >
        <div className="flex items-center gap-1.5 truncate flex-1 min-w-0">
          {node.type === 'directory' ? (
            <>
              {isOpen ? (
                <ChevronDown className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
              )}
              {isOpen ? (
                <FolderOpen className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
              ) : (
                <Folder className="w-3.5 h-3.5 text-amber-500/80 flex-shrink-0" />
              )}
            </>
          ) : (
            <>
              <span className="w-3.5 flex-shrink-0" />
              <FileCode className="w-3.5 h-3.5 text-sky-400 flex-shrink-0" />
            </>
          )}

          <span className="truncate">{node.name}</span>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          {renderStatusBadge()}

          {node.type === 'directory' && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onTestFolder(node);
              }}
              title={`Test all files in ${node.name}`}
              className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-slate-700 text-sky-400 rounded transition"
            >
              <Play className="w-3 h-3 fill-current" />
            </button>
          )}
        </div>
      </div>

      {node.type === 'directory' && isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              owner={owner}
              repo={repo}
              branch={branch}
              onOpenFile={onOpenFile}
              onTestFolder={onTestFolder}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const RepoExplorerSidebar: React.FC<RepoExplorerSidebarProps> = ({
  onOpenRepoModal,
  onRunBatch,
  onStopBatch,
}) => {
  const { repoData, openTab, isBatchRunning, batchIndex, batchQueue } = useAgentStore();
  const [loadingFile, setLoadingFile] = useState<string | null>(null);

  if (!repoData) {
    return (
      <div className="flex flex-col h-full bg-slate-950 border border-slate-800 rounded-lg p-4 text-center justify-center items-center">
        <Layers className="w-8 h-8 text-slate-600 mb-2 stroke-1" />
        <h4 className="text-xs font-semibold text-slate-300 mb-1">IDE File Explorer</h4>
        <p className="text-[11px] text-slate-500 mb-3">
          Load a GitHub repository to browse files and run batch folder testing.
        </p>
        <button
          onClick={onOpenRepoModal}
          className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition"
        >
          <FolderSync className="w-3.5 h-3.5" />
          <span>Import Repository</span>
        </button>
      </div>
    );
  }

  const handleOpenFile = async (path: string, name: string, lang: Language, sha?: string) => {
    setLoadingFile(path);
    try {
      const fileData = await qforgeApi.getGitHubFile(
        repoData.owner,
        repoData.repo,
        sha,
        path
      );
      openTab({
        path,
        name,
        content: fileData.content,
        language: lang,
        testStatus: 'idle',
      });
    } catch (err) {
      console.error('Failed to open file', err);
    } finally {
      setLoadingFile(null);
    }
  };

  const collectFolderFiles = (
    node: RepoTreeNode,
    acc: BatchFileItem[]
  ) => {
    if (node.type === 'file' && node.language) {
      acc.push({ path: node.path, name: node.name, language: node.language, sha: node.sha });
    } else if (node.type === 'directory' && node.children) {
      for (const child of node.children) {
        collectFolderFiles(child, acc);
      }
    }
  };

  const handleTestFolder = (folderNode: RepoTreeNode) => {
    const filesToTest: BatchFileItem[] = [];
    collectFolderFiles(folderNode, filesToTest);
    if (filesToTest.length === 0) return;
    onRunBatch(filesToTest);
  };

  const handleTestEntireRepo = () => {
    if (!repoData.files || repoData.files.length === 0) return;
    const filesToTest: BatchFileItem[] = repoData.files.map((f) => ({
      path: f.path,
      name: f.filename,
      language: f.language,
      sha: f.sha,
    }));
    onRunBatch(filesToTest);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 border border-slate-800 rounded-lg overflow-hidden shadow-lg select-none">
      {/* Sidebar Header */}
      <div className="flex-shrink-0 p-3 border-b border-slate-800 bg-slate-900/70">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 truncate">
            <Layers className="w-4 h-4 text-sky-400 flex-shrink-0" />
            <h3 className="font-semibold text-xs text-slate-200 truncate">
              {repoData.owner}/{repoData.repo}
            </h3>
          </div>
          <button
            onClick={onOpenRepoModal}
            title="Switch Repository"
            className="text-[11px] text-sky-400 hover:text-sky-300"
          >
            Switch
          </button>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2 font-mono">
          <span>Branch: {repoData.branch}</span>
          <span className="text-slate-500">{repoData.total_source_files} files</span>
        </div>

        {/* Batch Test Entire Repo Button & Active Batch State */}
        {isBatchRunning ? (
          <div className="flex items-center gap-1.5 w-full">
            <div className="flex-1 py-1.5 px-2 bg-amber-600/20 border border-amber-500/40 text-amber-300 rounded text-xs font-semibold flex items-center justify-center gap-1.5 truncate">
              <Loader2 className="w-3.5 h-3.5 animate-spin flex-shrink-0 text-amber-400" />
              <span className="truncate">
                Testing ({batchIndex + 1}/{batchQueue.length})
              </span>
            </div>
            {onStopBatch && (
              <button
                onClick={onStopBatch}
                title="Stop Batch Execution"
                className="px-2.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-bold transition flex-shrink-0"
              >
                Stop
              </button>
            )}
          </div>
        ) : (
          <button
            onClick={handleTestEntireRepo}
            className="w-full py-1.5 px-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white rounded text-xs font-semibold flex items-center justify-center gap-1.5 shadow transition active:scale-[0.98]"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Batch Test Entire Repo</span>
          </button>
        )}
      </div>

      {/* Nested Tree Body */}
      <div className="flex-1 min-h-0 overflow-y-auto p-2 pb-8 space-y-0.5 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900/50">
        {repoData.nested_tree.map((node) => (
          <TreeNode
            key={node.path}
            node={node}
            owner={repoData.owner}
            repo={repoData.repo}
            branch={repoData.branch}
            onOpenFile={handleOpenFile}
            onTestFolder={handleTestFolder}
          />
        ))}
      </div>
    </div>
  );
};
