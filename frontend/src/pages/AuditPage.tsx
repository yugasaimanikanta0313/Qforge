import React, { useEffect, useState } from 'react';
import { qforgeApi } from '../api/qforgeApi';
import { AuditLogRecord } from '../types/agent';
import { StatusPill } from '../components/shared/StatusPill';
import { LoadingSpinner } from '../components/shared/LoadingSpinner';
import { Search, Download, ShieldCheck, RefreshCw, AlertTriangle } from 'lucide-react';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedRecord, setSelectedRecord] = useState<AuditLogRecord | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await qforgeApi.getAuditLogs(100);
      setLogs(data.logs || []);
    } catch (err) {
      console.error('Failed to load audit logs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const filteredLogs = logs.filter(
    (l) =>
      l.session_id.toLowerCase().includes(searchFilter.toLowerCase()) ||
      l.language?.toLowerCase().includes(searchFilter.toLowerCase()) ||
      l.routing_path?.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `qforge_audit_logs_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full overflow-y-auto p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <h1 className="text-xl font-bold text-slate-100">Enterprise Compliance & Audit Logs</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-evident trail of LangGraph routing choices, self-heal repairs, and cloud egress validations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <button
            onClick={downloadJson}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold shadow transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Audit JSON</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 max-w-md">
        <Search className="w-4 h-4 text-slate-500" />
        <input
          type="text"
          placeholder="Filter by session ID, language, or path..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          className="bg-transparent text-xs text-slate-200 placeholder-slate-500 focus:outline-none w-full"
        />
      </div>

      {/* Table & Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Table View */}
        <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 uppercase text-[10px] text-slate-400 tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Session ID</th>
                  <th className="px-4 py-3">Language</th>
                  <th className="px-4 py-3">Complexity</th>
                  <th className="px-4 py-3">Path</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Repairs</th>
                  <th className="px-4 py-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12">
                      <LoadingSpinner />
                      <p className="mt-2 text-slate-500 text-xs">Loading audit records...</p>
                    </td>
                  </tr>
                ) : filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-slate-500 text-xs font-sans">
                      No audit records found.
                    </td>
                  </tr>
                ) : (
                  filteredLogs.map((log, idx) => (
                    <tr
                      key={idx}
                      onClick={() => setSelectedRecord(log)}
                      className="hover:bg-slate-800/50 cursor-pointer transition"
                    >
                      <td className="px-4 py-3 text-sky-400 font-semibold">{log.session_id}</td>
                      <td className="px-4 py-3 uppercase">{log.language}</td>
                      <td className="px-4 py-3">{log.complexity_score}/10</td>
                      <td className="px-4 py-3">
                        <StatusPill status={log.routing_path || 'local'} />
                      </td>
                      <td className="px-4 py-3">
                        <StatusPill status={log.validation_status || 'PENDING'} />
                      </td>
                      <td className="px-4 py-3 text-amber-400">#{log.repair_cycles_used || 0}</td>
                      <td className="px-4 py-3 text-slate-500 font-sans">
                        {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Record Detail Panel */}
        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-4">
          <h3 className="font-semibold text-sm text-slate-200 pb-2 border-b border-slate-800">
            Session Execution Trace
          </h3>

          {selectedRecord ? (
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-500">Session ID:</span>
                <p className="font-mono text-sky-400 font-semibold">{selectedRecord.session_id}</p>
              </div>

              <div>
                <span className="text-slate-500">Model Used:</span>
                <p className="font-mono text-purple-300">{selectedRecord.generation_model_used || 'N/A'}</p>
              </div>

              <div>
                <span className="text-slate-500">Audit Notes:</span>
                <ul className="mt-1 space-y-1 list-disc pl-4 text-slate-300">
                  {(selectedRecord.audit_notes || []).map((note, i) => (
                    <li key={i}>{note}</li>
                  ))}
                </ul>
              </div>

              {selectedRecord.validation_errors && selectedRecord.validation_errors.length > 0 && (
                <div>
                  <span className="text-rose-400 font-semibold flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Validation Errors:
                  </span>
                  <ul className="mt-1 space-y-1 list-disc pl-4 text-rose-300">
                    {selectedRecord.validation_errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-16 text-slate-500 text-xs">
              Select a session record to view full audit notes and validation traces.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
