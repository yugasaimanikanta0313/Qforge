import { create } from 'zustand';
import { TelemetryEvent, Language, RepoData, EditorTab, FileTestStatus } from '../types/agent';

interface AgentStateStore {
  sessionId: string | null;
  language: Language;
  rawInput: string;
  isExecuting: boolean;
  events: TelemetryEvent[];
  activeNode: string | null;
  repairCycle: number;
  finalTestSuite: string | null;
  finalStatus: 'PASS' | 'FAIL' | null;
  complexityScore: number | null;
  routingPath: 'local' | 'cloud' | null;
  modelUsed: string | null;

  // IDE Repository & Tab Management
  repoData: RepoData | null;
  openTabs: EditorTab[];
  activeTabPath: string | null;
  fileTestStatuses: Record<string, FileTestStatus>;
  isExplorerOpen: boolean;

  // Batch Execution
  isBatchRunning: boolean;
  batchQueue: string[];
  batchIndex: number;

  setSessionId: (id: string) => void;
  setLanguage: (lang: Language) => void;
  setRawInput: (input: string) => void;
  setIsExecuting: (val: boolean) => void;
  addEvent: (event: TelemetryEvent) => void;
  setActiveNode: (node: string | null) => void;
  setRepairCycle: (cycle: number) => void;
  setFinalResult: (payload: {
    test_suite?: string;
    status?: 'PASS' | 'FAIL';
    model_used?: string;
    routing_path?: 'local' | 'cloud';
    complexity_score?: number;
    repair_cycles_used?: number;
  }) => void;
  resetSession: () => void;

  // IDE Actions
  setRepoData: (data: RepoData | null) => void;
  openTab: (tab: EditorTab) => void;
  closeTab: (path: string) => void;
  setActiveTab: (path: string) => void;
  setFileStatus: (path: string, status: FileTestStatus, suite?: string) => void;
  toggleExplorer: () => void;
  setIsExplorerOpen: (open: boolean) => void;

  // Batch Actions
  startBatch: (paths: string[]) => void;
  advanceBatch: () => void;
  setBatchIndex: (index: number) => void;
  stopBatch: () => void;
}

const DEFAULT_SAMPLE_CODE = `def calculate_order_discount(customer_type: str, order_total: float) -> float:
    """Calculates customer discount based on tier and spend."""
    if order_total <= 0:
        return 0.0
    if customer_type == "VIP":
        return round(order_total * 0.20, 2)
    elif customer_type == "STANDARD" and order_total >= 100:
        return round(order_total * 0.10, 2)
    return 0.0
`;

export const useAgentStore = create<AgentStateStore>((set, get) => ({
  sessionId: null,
  language: 'python',
  rawInput: DEFAULT_SAMPLE_CODE,
  isExecuting: false,
  events: [],
  activeNode: null,
  repairCycle: 0,
  finalTestSuite: null,
  finalStatus: null,
  complexityScore: null,
  routingPath: null,
  modelUsed: null,

  repoData: null,
  openTabs: [
    {
      path: 'sample.py',
      name: 'sample.py',
      content: DEFAULT_SAMPLE_CODE,
      language: 'python',
      testStatus: 'idle',
    },
  ],
  activeTabPath: 'sample.py',
  fileTestStatuses: {},
  isExplorerOpen: true,

  isBatchRunning: false,
  batchQueue: [],
  batchIndex: 0,

  setSessionId: (id) => set({ sessionId: id }),
  setLanguage: (lang) => {
    set({ language: lang });
    const { activeTabPath, openTabs } = get();
    if (activeTabPath) {
      set({
        openTabs: openTabs.map((t) =>
          t.path === activeTabPath ? { ...t, language: lang } : t
        ),
      });
    }
  },
  setRawInput: (input) => {
    set({ rawInput: input });
    const { activeTabPath, openTabs } = get();
    if (activeTabPath) {
      set({
        openTabs: openTabs.map((t) =>
          t.path === activeTabPath ? { ...t, content: input } : t
        ),
      });
    }
  },
  setIsExecuting: (val) => set({ isExecuting: val }),
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
  setActiveNode: (node) => set({ activeNode: node }),
  setRepairCycle: (cycle) => set({ repairCycle: cycle }),
  setFinalResult: (payload) => {
    const { activeTabPath, openTabs, fileTestStatuses } = get();
    const updatedStatus = payload.status || 'FAIL';
    const updatedStatuses = { ...fileTestStatuses };
    if (activeTabPath) {
      updatedStatuses[activeTabPath] = updatedStatus;
    }

    set({
      finalTestSuite: payload.test_suite || null,
      finalStatus: payload.status || null,
      modelUsed: payload.model_used || null,
      routingPath: payload.routing_path || null,
      complexityScore: payload.complexity_score ?? null,
      repairCycle: payload.repair_cycles_used ?? 0,
      isExecuting: false,
      activeNode: null,
      fileTestStatuses: updatedStatuses,
      openTabs: openTabs.map((t) =>
        t.path === activeTabPath
          ? { ...t, testStatus: updatedStatus, testSuite: payload.test_suite }
          : t
      ),
    });
  },
  resetSession: () =>
    set({
      events: [],
      activeNode: null,
      repairCycle: 0,
      finalTestSuite: null,
      finalStatus: null,
      complexityScore: null,
      routingPath: null,
      modelUsed: null,
      isExecuting: false,
    }),

  setRepoData: (data) => set({ repoData: data, isExplorerOpen: !!data }),
  openTab: (tab) => {
    const { openTabs } = get();
    const existingIndex = openTabs.findIndex((t) => t.path === tab.path);
    if (existingIndex === -1) {
      set({
        openTabs: [...openTabs, tab],
        activeTabPath: tab.path,
        rawInput: tab.content,
        language: tab.language,
        finalTestSuite: tab.testSuite || null,
        finalStatus: tab.testStatus === 'PASS' || tab.testStatus === 'FAIL' ? tab.testStatus : null,
      });
    } else {
      const updatedTabs = openTabs.map((t, idx) =>
        idx === existingIndex
          ? {
              ...t,
              name: tab.name || t.name,
              content: tab.content !== undefined ? tab.content : t.content,
              language: tab.language || t.language,
              testStatus: tab.testStatus !== undefined ? tab.testStatus : t.testStatus,
              testSuite: tab.testSuite !== undefined ? tab.testSuite : t.testSuite,
            }
          : t
      );
      const current = updatedTabs[existingIndex];
      set({
        openTabs: updatedTabs,
        activeTabPath: tab.path,
        rawInput: current.content,
        language: current.language,
        finalTestSuite: current.testSuite || null,
        finalStatus:
          current.testStatus === 'PASS' || current.testStatus === 'FAIL' ? current.testStatus : null,
      });
    }
  },
  closeTab: (path) => {
    const { openTabs, activeTabPath } = get();
    const filtered = openTabs.filter((t) => t.path !== path);
    if (filtered.length === 0) {
      set({
        openTabs: [],
        activeTabPath: null,
        rawInput: '',
        finalTestSuite: null,
        finalStatus: null,
      });
    } else if (activeTabPath === path) {
      const nextTab = filtered[filtered.length - 1];
      set({
        openTabs: filtered,
        activeTabPath: nextTab.path,
        rawInput: nextTab.content,
        language: nextTab.language,
        finalTestSuite: nextTab.testSuite || null,
        finalStatus:
          nextTab.testStatus === 'PASS' || nextTab.testStatus === 'FAIL' ? nextTab.testStatus : null,
      });
    } else {
      set({ openTabs: filtered });
    }
  },
  setActiveTab: (path) => {
    const { openTabs } = get();
    const tab = openTabs.find((t) => t.path === path);
    if (tab) {
      set({
        activeTabPath: path,
        rawInput: tab.content,
        language: tab.language,
        finalTestSuite: tab.testSuite || null,
        finalStatus: tab.testStatus === 'PASS' || tab.testStatus === 'FAIL' ? tab.testStatus : null,
      });
    }
  },
  setFileStatus: (path, status, suite) =>
    set((state) => ({
      fileTestStatuses: { ...state.fileTestStatuses, [path]: status },
      openTabs: state.openTabs.map((t) =>
        t.path === path
          ? {
              ...t,
              testStatus: status,
              testSuite: suite !== undefined ? suite : t.testSuite,
            }
          : t
      ),
      ...(state.activeTabPath === path
        ? {
            finalStatus: status === 'PASS' || status === 'FAIL' ? status : state.finalStatus,
            ...(suite !== undefined ? { finalTestSuite: suite } : {}),
          }
        : {}),
    })),
  toggleExplorer: () => set((state) => ({ isExplorerOpen: !state.isExplorerOpen })),
  setIsExplorerOpen: (open) => set({ isExplorerOpen: open }),

  startBatch: (paths) =>
    set({
      isBatchRunning: true,
      batchQueue: paths,
      batchIndex: 0,
    }),
  advanceBatch: () =>
    set((state) => {
      const nextIdx = state.batchIndex + 1;
      if (nextIdx >= state.batchQueue.length) {
        return { isBatchRunning: false, batchQueue: [], batchIndex: 0 };
      }
      return { batchIndex: nextIdx };
    }),
  setBatchIndex: (index) => set({ batchIndex: index }),
  stopBatch: () =>
    set({
      isBatchRunning: false,
      batchQueue: [],
      batchIndex: 0,
    }),
}));
