import React, { useEffect, useState } from 'react';
import { ShieldCheck, ShieldAlert, History, User, Check, X, Clock } from 'lucide-react';
import { api, AuditLogItem } from '../api';

export const AuditLogView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const data = await api.getAuditLogs();
      setLogs(data.logs);
      setLoading(false);
    } catch {}
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="glass-panel p-6 animate-pulse">
        <div className="h-6 w-48 bg-white/10 rounded mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-white/5 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="glass-panel overflow-hidden">
      <div className="p-5 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History size={18} className="text-indigo-400" />
          <h2 className="font-semibold text-base text-white">Immutable AI Audit Trail</h2>
          <span className="text-xs bg-white/10 text-slate-300 px-2 py-0.5 rounded-full font-mono">
            {logs.length} logged events
          </span>
        </div>
        <span className="text-xs text-slate-400">Complete AI &rarr; Risk &rarr; Approval &rarr; Execution Ledger</span>
      </div>

      <div className="divide-y divide-white/5 max-h-[500px] overflow-y-auto">
        {logs.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            No audit records recorded yet. Actions taken with the AI Copilot will be logged here in real time.
          </div>
        ) : (
          logs.map((log) => {
            const isPassed = log.risk_result === 'PASSED';
            const isRejected = log.risk_result === 'REJECTED';
            const isExecuted = log.execution_result === 'FILLED';

            return (
              <div key={log.id} className="p-4 hover:bg-white/[0.02] transition-colors text-xs font-mono">
                <div className="flex items-start justify-between gap-4 mb-1.5">
                  <div className="flex items-center gap-2 font-sans font-medium text-slate-200">
                    <User size={13} className="text-slate-400" />
                    <span>&ldquo;{log.user_request}&rdquo;</span>
                  </div>
                  <div className="text-slate-500 text-[11px] shrink-0 flex items-center gap-1">
                    <Clock size={11} />
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-[11px] mt-2">
                  {log.tool_used && (
                    <span className="bg-indigo-950/60 text-indigo-300 border border-indigo-500/25 px-2 py-0.5 rounded">
                      Tool: {log.tool_used}()
                    </span>
                  )}

                  {log.risk_result && log.risk_result !== 'N/A' && (
                    <span
                      className={`px-2 py-0.5 rounded flex items-center gap-1 ${
                        isPassed
                          ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
                          : 'bg-rose-950/60 text-rose-300 border border-rose-500/30'
                      }`}
                    >
                      {isPassed ? <ShieldCheck size={11} /> : <ShieldAlert size={11} />}
                      Risk: {log.risk_result}
                    </span>
                  )}

                  {log.user_approved !== null && log.user_approved !== undefined && (
                    <span
                      className={`px-2 py-0.5 rounded flex items-center gap-1 ${
                        log.user_approved
                          ? 'bg-emerald-950/50 text-emerald-400 border border-emerald-500/20'
                          : 'bg-slate-800 text-slate-400 border border-white/10'
                      }`}
                    >
                      {log.user_approved ? <Check size={11} /> : <X size={11} />}
                      User Approval: {log.user_approved ? 'Granted' : 'Declined'}
                    </span>
                  )}

                  {log.execution_result && log.execution_result !== 'N/A' && (
                    <span className="bg-cyan-950/60 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded">
                      Execution: {log.execution_result}
                    </span>
                  )}
                </div>

                {log.risk_details?.reason && (
                  <div className="mt-2 text-rose-400 text-[11px] font-sans">
                    Risk Notice: {log.risk_details.reason}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
