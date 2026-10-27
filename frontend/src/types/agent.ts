export type Language = 'python' | 'typescript' | 'javascript' | 'java' | 'go' | 'rust' | 'csharp' | 'sql';

export type NodeName = 'ROUTER' | 'GENERATOR' | 'VALIDATOR';

export type NodeStatus = 'running' | 'completed' | 'failed' | 'pending';

export interface RepoFileItem {
  path: string;
  filename: string;
  sha?: string;
  size: number;
  language: Language;
  extension: string;
}

export interface RepoTreeNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: RepoTreeNode[];
  language?: Language;
  size?: number;
  sha?: string;
}

export type FileTestStatus = 'idle' | 'running' | 'PASS' | 'FAIL';

export interface EditorTab {
  path: string;
  name: string;
  content: string;
  language: Language;
  testStatus?: FileTestStatus;
  testSuite?: string;
}

export interface RepoData {
  owner: string;
  repo: string;
  branch: string;
  total_source_files: number;
  files: RepoFileItem[];
  nested_tree: RepoTreeNode[];
}

export interface ChatHistoryTurn {
  session_id: string;
  language: string;
  user_prompt: string;
  generated_suite: string;
  validation_status: 'PASS' | 'FAIL';
  repair_cycles: number;
  model_used: string;
  repo_context?: string;
  created_at: string;
}

export interface AstFingerprint {
  code_type?: string;
  function_count?: number;
  class_count?: number;
  table_count?: number;
  join_count?: number;
  aggregation_count?: number;
  functions?: number;
  classes?: number;
  branches?: number;
  loops?: number;
}

export interface TelemetryEvent {
  id: string;
  timestamp: string;
  event: 'session_start' | 'node_start' | 'node_complete' | 'repair_cycle' | 'final_result' | 'error';
  node?: NodeName;
  message?: string;
  data?: {
    complexity_score?: number;
    routing_path?: 'local' | 'cloud';
    language?: Language;
    ast_fingerprint?: AstFingerprint;
    context_chunks_count?: number;
    model_used?: string;
    test_suite_preview?: string;
    validation_status?: 'PASS' | 'FAIL';
    errors?: string[];
    repair_cycle?: number;
  };
  cycle?: number;
  errors?: string[];
  status?: 'PASS' | 'FAIL';
  test_suite?: string;
  model_used?: string;
  routing_path?: 'local' | 'cloud';
  complexity_score?: number;
  repair_cycles_used?: number;
  audit?: string[];
}

export interface SessionMeta {
  session_id: string;
  language: Language;
  raw_input: string;
  complexity_score?: number;
  routing_path?: 'local' | 'cloud';
  status: string;
}

export interface ArtifactPayload {
  artifact_id: string;
  session_id: string;
  language: Language;
  verified_suite: string;
  retry_count: number;
  validation_status: string;
  generation_model: string;
  token_usage?: {
    input_chars: number;
    output_chars: number;
  };
}

export interface AuditLogRecord {
  session_id: string;
  timestamp: string;
  language: string;
  complexity_score: number;
  routing_path: string;
  validation_status: string;
  repair_cycles_used: number;
  generation_model_used: string;
  validation_errors: string[];
  audit_notes: string[];
}
