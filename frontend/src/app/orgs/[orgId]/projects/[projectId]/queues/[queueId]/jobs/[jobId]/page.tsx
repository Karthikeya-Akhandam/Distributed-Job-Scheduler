'use client';

import React, { useEffect, useState, use } from 'react';
import { api } from '@/lib/api';
import { Card, Button, Badge } from '@/components/ui';
import { Job, JobExecution, JobLog } from '@/lib/types';
import Link from 'next/link';
import { Activity, ArrowLeft, Terminal, AlertTriangle, CheckCircle, Info, Clock } from 'lucide-react';

interface JobDetailPageProps {
  params: Promise<{ orgId: string; projectId: string; queueId: string; jobId: string }>;
}

export default function JobDetailPage({ params }: JobDetailPageProps) {
  const { orgId, projectId, queueId, jobId } = use(params);
  const [job, setJob] = useState<Job | null>(null);
  const [executions, setExecutions] = useState<JobExecution[]>([]);
  const [logs, setLogs] = useState<JobLog[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchJobData = async () => {
    try {
      const jobRes = await api.get(`/jobs/${jobId}`);
      setJob(jobRes.data);
      setExecutions(jobRes.data.executions || []);

      const logsRes = await api.get(`/jobs/${jobId}/logs`);
      setLogs(logsRes.data);
    } catch (e) {
      console.error('Error fetching job details:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobData();
  }, [jobId]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Link href={`/orgs/${orgId}/projects/${projectId}/queues/${queueId}`} className="text-slate-400 hover:text-slate-200 flex items-center gap-1 text-sm font-semibold transition-colors">
          <ArrowLeft className="h-4 w-4" />
          Back to Queue Details
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">Job ID: {jobId.substring(0, 8)}</h1>
            <Badge 
              color={
                job?.status === 'completed' ? 'emerald' : 
                job?.status === 'failed' ? 'rose' : 
                job?.status === 'running' ? 'indigo' : 
                job?.status === 'dead' ? 'rose' : 'slate'
              }
            >
              {job?.status}
            </Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">Name: {job?.name} · Priority: {job?.priority} · Shard Key: {job?.shard_key}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Payload / details column */}
        <div className="space-y-6">
          <Card>
            <h2 className="text-sm font-bold text-white border-b border-slate-800 pb-3 uppercase tracking-wider">Job Metadata</h2>
            <div className="mt-4 space-y-4 text-xs text-slate-350">
              <div>
                <span className="block text-slate-500 font-semibold uppercase tracking-wider mb-1">Created At</span>
                <span className="font-mono">{job ? new Date(job.created_at).toLocaleString() : 'N/A'}</span>
              </div>
              <div>
                <span className="block text-slate-500 font-semibold uppercase tracking-wider mb-1">Last Updated</span>
                <span className="font-mono">{job ? new Date(job.updated_at).toLocaleString() : 'N/A'}</span>
              </div>
              <div>
                <span className="block text-slate-500 font-semibold uppercase tracking-wider mb-1">Max Retries Target</span>
                <span>{job?.max_retries} attempts allowed</span>
              </div>
              {job?.idempotency_key && (
                <div>
                  <span className="block text-slate-500 font-semibold uppercase tracking-wider mb-1">Idempotency Key</span>
                  <span className="font-mono bg-slate-950 px-2 py-1 border border-slate-850 rounded-lg text-slate-400">{job.idempotency_key}</span>
                </div>
              )}
            </div>
          </Card>

          <Card>
            <h2 className="text-sm font-bold text-white border-b border-slate-800 pb-3 uppercase tracking-wider">Parameters Payload</h2>
            <pre className="mt-4 text-xs text-slate-300 overflow-x-auto bg-slate-950 p-4 rounded-xl border border-slate-850 leading-relaxed font-mono">
              {JSON.stringify(job?.payload, null, 2)}
            </pre>
          </Card>
        </div>

        {/* Execution attempts and logs column */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <h2 className="text-sm font-bold text-white border-b border-slate-800 pb-3 uppercase tracking-wider">Execution Attempts</h2>
            
            {executions.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center text-slate-550 text-xs">
                <Clock className="h-8 w-8 text-slate-750 mb-2 animate-pulse" />
                <span>Waiting for worker process to claim and execute...</span>
              </div>
            ) : (
              <div className="mt-4 space-y-4">
                {executions.map((exec, idx) => (
                  <div key={exec.id} className="p-4 rounded-xl bg-slate-850/80 border border-slate-800/80 text-xs space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-200">Attempt #{exec.attempt_number}</span>
                      <Badge color={exec.status === 'completed' ? 'emerald' : exec.status === 'running' ? 'indigo' : 'rose'}>
                        {exec.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-slate-400 py-1">
                      <div>
                        <span className="text-[10px] text-slate-500 font-semibold block uppercase">Duration</span>
                        <span>{exec.duration_ms ? `${exec.duration_ms} ms` : 'Executing...'}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 font-semibold block uppercase">Worker Node</span>
                        <span className="font-mono">{exec.worker_id ? exec.worker_id.substring(0, 8) : 'N/A'}</span>
                      </div>
                    </div>
                    {exec.error_message && (
                      <div className="mt-2 bg-rose-500/5 border border-rose-500/10 p-3 rounded-lg text-rose-450 leading-relaxed overflow-x-auto">
                        <span className="font-semibold block mb-0.5">Error Context:</span>
                        <code className="text-[11px] font-mono whitespace-pre-wrap">{exec.error_message}</code>
                        {exec.stack_trace && (
                          <pre className="mt-2 text-[10px] font-mono text-slate-500 border-t border-rose-500/10 pt-2 leading-relaxed overflow-x-auto max-h-40">
                            {exec.stack_trace}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card>
            <h2 className="text-sm font-bold text-white border-b border-slate-800 pb-3 uppercase tracking-wider flex items-center gap-2">
              <Terminal className="h-4.5 w-4.5 text-indigo-400" />
              Console Logs
            </h2>

            {logs.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center text-slate-550 text-xs">
                <span>No logs emitted.</span>
              </div>
            ) : (
              <div className="mt-4 font-mono text-[11px] bg-slate-950 p-4 rounded-xl border border-slate-850 divide-y divide-slate-900/60 max-h-[300px] overflow-y-auto space-y-2">
                {logs.map((log) => (
                  <div key={log.id} className="pt-2 flex gap-3 leading-relaxed items-start text-slate-350">
                    <span className="text-slate-500 shrink-0 select-none">[{new Date(log.created_at).toLocaleTimeString()}]</span>
                    <span className={`font-semibold shrink-0 uppercase tracking-wide text-[9px] px-1 rounded-sm ${
                      log.level === 'error' ? 'bg-rose-500/10 text-rose-400' :
                      log.level === 'warn' ? 'bg-amber-500/10 text-amber-400' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {log.level}
                    </span>
                    <span className="flex-1 whitespace-pre-wrap">{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
