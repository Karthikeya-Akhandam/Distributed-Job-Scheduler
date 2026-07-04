'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, Button, Badge } from '@/components/ui';
import { DLQEntry } from '@/lib/types';
import { AlertTriangle, Trash, RefreshCw, Sparkles, Clock } from 'lucide-react';

export default function DLQPage() {
  const [entries, setEntries] = useState<DLQEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiSummaries, setAiSummaries] = useState<Record<string, string>>({});
  const [aiLoading, setAiLoading] = useState<Record<string, boolean>>({});

  const fetchDLQ = async () => {
    try {
      // Find all queues first to get DLQ items for each
      const orgsRes = await api.get('/orgs');
      if (orgsRes.data.data.length > 0) {
        const orgId = orgsRes.data.data[0].id;
        const projectsRes = await api.get(`/orgs/${orgId}/projects`);
        if (projectsRes.data.data.length > 0) {
          const projectId = projectsRes.data.data[0].id;
          const queuesRes = await api.get(`/projects/${projectId}/queues`);
          
          let dlqAccumulator: DLQEntry[] = [];
          for (const queue of queuesRes.data.data) {
            const dlqRes = await api.get(`/queues/${queue.id}/dlq`);
            dlqAccumulator = [...dlqAccumulator, ...dlqRes.data.data];
          }
          setEntries(dlqAccumulator);
        }
      }
    } catch (e) {
      console.error('Error fetching DLQ entries:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDLQ();
  }, []);

  const handleRetry = async (entry: DLQEntry) => {
    try {
      await api.post(`/dlq/${entry.id}/retry`);
      fetchDLQ();
    } catch (e) {
      console.error('Failed to retry DLQ entry:', e);
    }
  };

  const handleDiscard = async (entry: DLQEntry) => {
    try {
      await api.post(`/dlq/${entry.id}/discard`);
      fetchDLQ();
    } catch (e) {
      console.error('Failed to discard DLQ entry:', e);
    }
  };

  const fetchAISummary = async (entryId: string) => {
    setAiLoading((prev) => ({ ...prev, [entryId]: true }));
    try {
      const response = await api.get(`/dlq/${entryId}/ai-summary`);
      setAiSummaries((prev) => ({ ...prev, [entryId]: response.data.ai_summary }));
    } catch (e) {
      console.error('Failed to fetch AI failure summary:', e);
      setAiSummaries((prev) => ({ ...prev, [entryId]: 'Failed to generate AI failure analysis.' }));
    } finally {
      setAiLoading((prev) => ({ ...prev, [entryId]: false }));
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">Dead Letter Queue (DLQ)</h1>
        <p className="text-sm text-slate-400 mt-1">Review jobs that exhausted all retry policies with AI-generated root cause summaries</p>
      </div>

      {entries.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-20 text-slate-500">
          <AlertTriangle className="h-12 w-12 text-slate-700 mb-4" />
          <h3 className="text-lg font-bold text-slate-350">Dead Letter Queue is empty</h3>
          <p className="text-sm text-slate-550 mt-1 max-w-sm text-center">
            Jobs that fail persistently after exhausting their maximum retry parameters land here for inspection.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {entries.map((entry) => (
            <Card key={entry.id} className="border-rose-500/10 hover:border-rose-500/25">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800/60 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-rose-500/10 text-rose-400 rounded-xl">
                    <AlertTriangle className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-200">DLQ Item: {entry.id.substring(0, 8)}</h3>
                    <span className="text-[10px] text-slate-500 font-mono block mt-1">Original Job ID: {entry.job_id}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge color={entry.status === 'dead' ? 'rose' : entry.status === 'retried' ? 'emerald' : 'slate'}>
                    {entry.status}
                  </Badge>
                  <span className="text-xs text-slate-500 flex items-center gap-1 font-semibold ml-2">
                    <Clock className="h-3.5 w-3.5" />
                    Dead at {new Date(entry.dead_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-4">
                  <div>
                    <span className="block text-slate-500 text-[10px] font-semibold uppercase tracking-wider mb-1">Failure Exception</span>
                    <pre className="text-xs font-mono bg-slate-950 p-3.5 rounded-xl border border-slate-850 text-rose-400 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                      {entry.failure_reason}
                    </pre>
                  </div>

                  {/* AI summary trigger */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-slate-500 text-[10px] font-semibold uppercase tracking-wider">AI Root Cause Analysis</span>
                      {!aiSummaries[entry.id] && entry.status === 'dead' && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => fetchAISummary(entry.id)} 
                          isLoading={aiLoading[entry.id]}
                          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 py-1 px-2.5 flex items-center gap-1"
                        >
                          <Sparkles className="h-3.5 w-3.5" />
                          Generate Analysis
                        </Button>
                      )}
                    </div>

                    {aiSummaries[entry.id] ? (
                      <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 text-xs text-indigo-300 leading-relaxed font-sans">
                        {aiSummaries[entry.id]}
                      </div>
                    ) : (
                      entry.ai_summary && (
                        <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 text-xs text-indigo-300 leading-relaxed font-sans">
                          {entry.ai_summary}
                        </div>
                      )
                    )}
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-850 text-xs text-slate-400 flex flex-col justify-between h-44">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Total Attempts:</span>
                      <span className="font-bold text-white">{entry.total_attempts}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>DLQ Status:</span>
                      <span className="font-bold text-slate-350">{entry.status}</span>
                    </div>
                  </div>

                  {entry.status === 'dead' && (
                    <div className="mt-4 flex gap-2">
                      <Button variant="secondary" size="sm" onClick={() => handleRetry(entry)} className="flex-1 flex items-center justify-center gap-1.5 py-2">
                        <RefreshCw className="h-3.5 w-3.5" />
                        Re-enqueue
                      </Button>
                      <Button variant="danger" size="sm" onClick={() => handleDiscard(entry)} className="flex-1 flex items-center justify-center gap-1.5 py-2">
                        <Trash className="h-3.5 w-3.5" />
                        Discard
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
