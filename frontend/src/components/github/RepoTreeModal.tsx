import React, { useState } from 'react';
import { RepoTreeNode, Language } from '../../types/agent';
import { qforgeApi } from '../../api/qforgeApi';
import { useAgentStore } from '../../store/agentStore';
import {
  Folder,
  FolderOpen,
  FileCode,
  ChevronRight,
  ChevronDown,
  Github,
  X,
  Search,
  ExternalLink,
} from 'lucide-react';
import { LoadingSpinner } from '../shared/LoadingSpinner';

interface RepoTreeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface TreeNodeItemProps {
  node: RepoTreeNode;
  owner: string;
  repo: string;
  branch: string;
  token?: string;
  onSelectFile: (content: string, language: Language, filePath: string) => void;
  depth?: number;
}

const TreeNodeItem: React.FC<TreeNodeItemProps> = ({
  node,
  owner,
  repo,
  branch,
  token,
  onSelectFile,
  depth = 0,
}) => {
  const [isOpen, setIsOpen] = useState(depth === 0);
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    if (node.type === 'directory') {
      setIsOpen(!isOpen);
    } else {
      setIsLoading(true);
      try {
        const fileData = await qforgeApi.getGitHubFile(
          owner,
          repo,
          node.sha,
          node.path,
          token
        );
        onSelectFile(
          fileData.content,
          fileData.language as Language,
          node.path
        );
      } catch (err) {
        console.error('Failed to load file', err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div>
      <div
        onClick={handleClick}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer transition text-xs select-none ${
          node.type === 'directory'
            ? 'hover:bg-slate-800 text-slate-300 font-medium'
            : 'hover:bg-sky-950/50 hover:text-sky-300 text-slate-400'
        }`}
      >
        {node.type === 'directory' ? (
          <>
            {isOpen ? (
              <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
            )}
            {isOpen ? (
              <FolderOpen className="w-4 h-4 text-amber-400" />
            ) : (
              <Folder className="w-4 h-4 text-amber-500/80" />
            )}
          </>
        ) : (
          <>
            <span className="w-3.5" />
            <FileCode className="w-4 h-4 text-sky-400" />
          </>
        )}

        <span className="truncate flex-1">{node.name}</span>

        {isLoading && <LoadingSpinner size="sm" />}

        {node.language && (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 uppercase">
            {node.language}
          </span>
        )}
      </div>

      {node.type === 'directory' && isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeNodeItem
              key={child.path}
              node={child}
              owner={owner}
              repo={repo}
              branch={branch}
              token={token}
              onSelectFile={onSelectFile}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const RepoTreeModal: React.FC<RepoTreeModalProps> = ({ isOpen, onClose }) => {
  const { setRawInput, setLanguage, setRepoData, openTab } = useAgentStore();
  const [repoInput, setRepoInput] = useState('https://github.com/yugasaimanikanta0313/Rz');
  const [tokenInput, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [treeData, setTreeData] = useState<any | null>(null);

  if (!isOpen) return null;

  const handleFetchTree = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!repoInput.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const data = await qforgeApi.getGitHubTree(
        repoInput.trim(),
        undefined,
        tokenInput.trim() || undefined
      );
      setTreeData(data);
      setRepoData(data);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Failed to load GitHub repository tree'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSelectFile = (content: string, lang: Language, path: string) => {
    const filename = path.split('/').pop() || path;
    openTab({
      path,
      name: filename,
      content,
      language: lang,
      testStatus: 'idle',
    });
    setRawInput(content);
    setLanguage(lang);
    onClose();
  };

  const handleImportEntireRepo = () => {
    if (treeData) {
      setRepoData(treeData);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-slate-800 rounded-lg text-slate-100">
              <Github className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100">
                Import Repository from GitHub
              </h2>
              <p className="text-xs text-slate-400">
                Explore source files and generate enterprise tests for any repository
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition p-1 rounded hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Input Bar */}
        <form onSubmit={handleFetchTree} className="p-6 border-b border-slate-800/80 bg-slate-950/30">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={repoInput}
                onChange={(e) => setRepoInput(e.target.value)}
                placeholder="e.g. owner/repo or https://github.com/..."
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50"
            >
              {loading ? <LoadingSpinner size="sm" /> : <ExternalLink className="w-3.5 h-3.5" />}
              <span>Load Tree</span>
            </button>
          </div>

          <div className="mt-2 flex items-center gap-2">
            <input
              type="password"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder="Optional: GitHub Personal Access Token (for private repos)"
              className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded text-[11px] text-slate-300 placeholder-slate-600 focus:outline-none focus:border-slate-700"
            />
          </div>

          {error && (
            <div className="mt-3 p-2.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
              {error}
            </div>
          )}
        </form>

        {/* File Tree Explorer View */}
        <div className="flex-1 overflow-y-auto p-4 min-h-[300px]">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-48 gap-3 text-slate-400">
              <LoadingSpinner size="md" />
              <p className="text-xs">Fetching recursive git tree & analyzing files...</p>
            </div>
          ) : treeData ? (
            <div>
              <div className="flex items-center justify-between mb-3 px-2 text-xs text-slate-400">
                <span>
                  Repository: <strong className="text-slate-200">{treeData.owner}/{treeData.repo}</strong> ({treeData.branch})
                </span>
                <span className="px-2 py-0.5 rounded-full bg-slate-800 text-sky-400 text-[11px] font-mono">
                  {treeData.total_source_files} source files indexed
                </span>
              </div>

              <div className="border border-slate-800/80 rounded-lg p-2 bg-slate-950/40">
                {treeData.nested_tree.map((node) => (
                  <TreeNodeItem
                    key={node.path}
                    node={node}
                    owner={treeData.owner}
                    repo={treeData.repo}
                    branch={treeData.branch}
                    token={tokenInput}
                    onSelectFile={handleSelectFile}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-xs gap-2">
              <Folder className="w-8 h-8 text-slate-600" />
              <p>Enter a GitHub repository above to inspect source files and generate tests.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 flex items-center justify-between bg-slate-950/60 text-xs text-slate-500">
          <span>Click on any source file to open, or import full tree into IDE.</span>
          <div className="flex items-center gap-2">
            {treeData && (
              <button
                onClick={handleImportEntireRepo}
                className="px-3.5 py-1.5 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 shadow transition"
              >
                <span>Import Entire Repo into Workspace</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
