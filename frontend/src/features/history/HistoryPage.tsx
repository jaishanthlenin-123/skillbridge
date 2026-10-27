import React, { useEffect, useState } from 'react';
import { History, ShieldCheck, Clock, Layers } from 'lucide-react';
import { api } from '../../services/api';
import type { AuditEvent } from '../../types';

export const HistoryPage: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadEvents() {
      try {
        setLoading(true);
        const data = await api.getAuditEvents();
        setEvents(data);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    loadEvents();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Activity History</h2>
        <p className="text-sm text-slate-400 mt-1">
          Review your recent account activity and operations. To protect your privacy, logs never store resume text or personal details.
        </p>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <History className="h-4 w-4 text-indigo-400" />
            <span>Audit Events ({events.length})</span>
          </h3>
          <span className="text-xs text-emerald-400 flex items-center gap-1">
            <ShieldCheck className="h-3.5 w-3.5" /> PII-Redacted Logging
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading audit history...</div>
        ) : events.length === 0 ? (
          <div className="p-12 text-center text-slate-500 italic">No events recorded yet.</div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {events.map((evt) => (
              <div key={evt.id} className="p-4 hover:bg-slate-900/40 flex items-center justify-between text-xs">
                <div>
                  <div className="flex items-center gap-2 font-mono font-semibold text-indigo-300">
                    <span className="h-2 w-2 rounded-full bg-indigo-500" />
                    <span>{evt.event_type}</span>
                  </div>
                  {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                    <div className="mt-1 text-slate-400 font-mono text-[11px]">
                      {JSON.stringify(evt.metadata)}
                    </div>
                  )}
                </div>
                <div className="text-slate-500 flex items-center gap-1 font-mono">
                  <Clock className="h-3 w-3" />
                  <span>{new Date(evt.timestamp).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
