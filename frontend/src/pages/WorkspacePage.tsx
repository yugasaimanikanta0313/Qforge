import React, { useState, useRef } from 'react';
import { CodeInputPanel } from '../components/editor/CodeInputPanel';
import { TelemetryFeed } from '../components/telemetry/TelemetryFeed';
import { ArtifactPanel } from '../components/artifact/ArtifactPanel';
import { RepoExplorerSidebar, BatchFileItem } from '../components/github/RepoExplorerSidebar';
import { RepoTreeModal } from '../components/github/RepoTreeModal';
import { useAgentStore } from '../store/agentStore';
import { useAgentSession } from '../hooks/useAgentSession';
import { qforgeApi } from '../api/qforgeApi';

export const WorkspacePage: React.FC = () => {
  const {
    repoData,
    isExplorerOpen,
    openTab,
    startBatch,
    setBatchIndex,
    stopBatch,
    setFileStatus,
  } = useAgentStore();
  const { startSession, stopSession } = useAgentSession();
  const [isRepoModalOpen, setIsRepoModalOpen] = useState(false);
  const isBatchCancelledRef = useRef(false);

  const handleStopBatch = () => {
    isBatchCancelledRef.current = true;
    stopBatch();
    stopSession();
  };

  const handleRunBatch = async (files: BatchFileItem[]) => {
    if (files.length === 0 || !repoData) return;

    isBatchCancelledRef.current = false;
    startBatch(files.map((f) => f.path));

    try {
      for (let i = 0; i < files.length; i++) {
        if (isBatchCancelledRef.current) break;
        setBatchIndex(i);
        const file = files[i];

        // Fetch file content if not already provided
        let content = file.content;
        if (!content) {
          try {
            const fetched = await qforgeApi.getGitHubFile(
              repoData.owner,
              repoData.repo,
              file.sha,
              file.path
            );
            content = fetched.content;
          } catch (err) {
            console.error(`Failed to load content for ${file.path}:`, err);
            setFileStatus(file.path, 'FAIL');
            continue;
          }
        }

        if (isBatchCancelledRef.current) break;

        // Open tab and mark as running
        openTab({
          path: file.path,
          name: file.name,
          content: content,
          language: file.language,
          testStatus: 'running',
        });
        setFileStatus(file.path, 'running');

        // Synthesize tests via WebSocket
        try {
          const result = await startSession(content, file.language);
          if (isBatchCancelledRef.current) break;
          setFileStatus(file.path, result.status, result.test_suite);
        } catch (err) {
          console.error(`Error during batch test of ${file.path}:`, err);
          setFileStatus(file.path, 'FAIL');
        }

        // Brief delay between batch files for UI rendering
        await new Promise((r) => setTimeout(r, 600));
      }
    } finally {
      isBatchCancelledRef.current = false;
      stopBatch();
    }
  };

  const hasExplorer = isExplorerOpen && !!repoData;

  return (
    <div className="h-full w-full flex flex-col p-2.5 overflow-hidden">
      <div className="grid grid-cols-12 gap-2.5 h-full min-h-0 flex-1">
        {/* Column 0: IDE File Explorer Sidebar (2 cols) */}
        {hasExplorer && (
          <div className="col-span-12 lg:col-span-2 xl:col-span-2 h-full min-h-0 flex flex-col overflow-hidden">
            <RepoExplorerSidebar
              onOpenRepoModal={() => setIsRepoModalOpen(true)}
              onRunBatch={handleRunBatch}
              onStopBatch={handleStopBatch}
            />
          </div>
        )}

        {/* Column 1: Source Editor (4 cols) */}
        <div
          className={`col-span-12 ${
            hasExplorer
              ? 'lg:col-span-4 xl:col-span-4'
              : 'lg:col-span-4'
          } h-full min-h-0 flex flex-col overflow-hidden`}
        >
          <CodeInputPanel />
        </div>

        {/* Column 2: Agent Telemetry Feed (3 cols if explorer open, 4 cols otherwise) */}
        <div
          className={`col-span-12 ${
            hasExplorer
              ? 'lg:col-span-3 xl:col-span-3'
              : 'lg:col-span-4'
          } h-full min-h-0 flex flex-col overflow-hidden`}
        >
          <TelemetryFeed />
        </div>

        {/* Column 3: Verified Artifact Panel (3 cols if explorer open, 4 cols otherwise) */}
        <div
          className={`col-span-12 ${
            hasExplorer
              ? 'lg:col-span-3 xl:col-span-3'
              : 'lg:col-span-4'
          } h-full min-h-0 flex flex-col overflow-hidden`}
        >
          <ArtifactPanel />
        </div>
      </div>

      <RepoTreeModal
        isOpen={isRepoModalOpen}
        onClose={() => setIsRepoModalOpen(false)}
      />
    </div>
  );
};
