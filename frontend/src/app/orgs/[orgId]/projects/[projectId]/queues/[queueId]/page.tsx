'use client';

import React, { useEffect, useState, use } from 'react';
import { api } from '@/lib/api';
import { Card, Button, Modal, Badge } from '@/components/ui';
import { Queue, Job } from '@/lib/types';
import Link from 'next/link';
import { Layers, ArrowLeft, Plus, Play, Pause, ChevronRight, Activity, Calendar, PlayCircle } from 'lucide-react';

interface QueueDetailPageProps {
  params: Promise<{ orgId: string; projectId: string; queueId: string }>;
}

export default function QueueDetailPage({ params }: QueueDetailPageProps) {
  const { orgId, projectId, queueId } = use(params);
  const [queue, setQueue] = useState<Queue | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newJobName, setNewJobName] = useState('');
  const [newJobType, setNewJobType] = useState('immediate');
  const [newJobPriority, setNewJobPriority] = useState(5);
  const [newJobPayload, setNewJobPayload] = useState('{}');
  const [newJobCron, setNewJobCron] = useState('');
  const [newJobScheduled, setNewJobScheduled] = useState('');
  const [modalLoading, setModalLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchQueueData = async () => {
    try {
      const qRes = await api.get(`/queues/${queueId}`);
      setQueue(qRes.data);

      const jobsRes = await api.get(`/queues/${queueId}/jobs`);
      setJobs(jobsRes.data.data);
    } catch (e) {
      console.error('Error fetching queue details:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueueData();
  }, [queueId]);

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    setError('');

    let parsedPayload = {};
    try {
      parsedPayload = JSON.parse(newJobPayload);
    } catch (err) {
      setError('Payload must be valid JSON');
      setModalLoading(false);
      return;
    }

    try {
      await api.post(`/queues/${queueId}/jobs`, {
        name: newJobName,
        type: newJobType,
        priority: newJobPriority,
        payload: parsedPayload,
        cron_expression: newJobType === 'recurring' ? newJobCron : null,
        scheduled_at: newJobType === 'scheduled' || newJobType === 'delayed' ? newJobScheduled || null : null,
      });

      setNewJobName('');
      setNewJobPayload('{}');
      setNewJobCron('');
      setNewJobScheduled('');
      setIsModalOpen(false);
      fetchQueueData();
    } catch (err: any) {
      setError(
        err.response?.data?.message || 
        err.response?.data?.detail?.message || 
        'Failed to enqueue job.'
      );
    } finally {
      setModalLoading(false);
    }
  };

  const triggerJobRetry = async (jobId: string) => {
    try {
      await api.post(`/jobs/${jobId}/retry`);
      fetchQueueData();
    } catch (e) {
      console.error('Error triggering job retry:', e);
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
      <div className="flex items-center gap-2">
        <Link href={`/orgs/${orgId}/projects/${projectId}`} className="text-slate-400 hover:text-slate-200 flex items-center gap-1 text-sm font-semibold transition-colors">
          <ArrowLeft className="h-4 w-4" />
          Back to Project Queues
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">{queue?.name}</h1>
            <Badge color={queue?.status === 'active' ? 'emerald' : 'amber'}>
              {queue?.status}
            </Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">Priority {queue?.priority} · Max concurrency {queue?.concurrency_limit} · Shards {queue?.shard_count}</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Enqueue Job
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-3">
          <div className="flex justify-between items-center pb-4 border-b border-slate-800">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Activity className="h-5 w-5 text-indigo-400" />
              Job Stream
            </h2>
          </div>

          {jobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-500">
              <PlayCircle className="h-12 w-12 text-slate-700 mb-3 animate-pulse" />
              <p className="text-sm font-semibold text-slate-350">No jobs enqueued</p>
              <p className="text-xs text-slate-550 mt-1 max-w-sm text-center">
                Submit an immediate, delayed, scheduled, or recurring cron job to test execution lifecycle pipeline.
              </p>
              <Button onClick={() => setIsModalOpen(true)} className="mt-4 text-xs py-2">
                Enqueue First Job
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-850 text-xs font-semibold text-slate-400 uppercase tracking-wider bg-slate-900/10">
                    <th className="py-3 px-4">Job ID</th>
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Attempts</th>
                    <th className="py-3 px-4">Created At</th>
                    <th className="py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850 text-xs text-slate-350">
                  {jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-slate-900/15 transition-colors">
                      <td className="py-3 px-4 font-mono text-indigo-400">{job.id.substring(0, 8)}</td>
                      <td className="py-3 px-4 font-semibold text-slate-200">{job.name}</td>
                      <td className="py-3 px-4 uppercase text-[10px] font-semibold text-slate-400">{job.type}</td>
                      <td className="py-3 px-4">
                        <Badge 
                          color={
                            job.status === 'completed' ? 'emerald' : 
                            job.status === 'failed' ? 'rose' : 
                            job.status === 'running' ? 'indigo' : 
                            job.status === 'dead' ? 'rose' : 'slate'
                          }
                        >
                          {job.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-300">{job.priority}</td>
                      <td className="py-3 px-4">{job.attempt_number} / {job.max_retries}</td>
                      <td className="py-3 px-4 text-slate-500">{new Date(job.created_at).toLocaleTimeString()}</td>
                      <td className="py-3 px-4 flex gap-1">
                        {['failed', 'dead'].includes(job.status) && (
                          <Button variant="secondary" size="sm" onClick={() => triggerJobRetry(job.id)} className="text-[10px] py-1 px-2.5">
                            Retry
                          </Button>
                        )}
                        <Link href={`/orgs/${orgId}/projects/${projectId}/queues/${queueId}/jobs/${job.id}`}>
                          <Button variant="ghost" size="sm" className="text-[10px] py-1 px-2">
                            Inspect
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      {/* Enqueue Job Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Enqueue Background Job">
        <form onSubmit={handleCreateJob} className="space-y-4">
          {error && (
            <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-xs text-rose-400">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5 col-span-2">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Job Name</label>
              <input
                type="text"
                required
                value={newJobName}
                onChange={(e) => setNewJobName(e.target.value)}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
                placeholder="e.g. Sync Customer Data"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Job Type</label>
              <select
                value={newJobType}
                onChange={(e) => setNewJobType(e.target.value)}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              >
                <option value="immediate">immediate (Runs instantly)</option>
                <option value="delayed">delayed (Runs after duration)</option>
                <option value="scheduled">scheduled (Runs at timestamp)</option>
                <option value="recurring">recurring (Cron expression)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Priority (1-10)</label>
              <input
                type="number"
                min="1"
                max="10"
                required
                value={newJobPriority}
                onChange={(e) => setNewJobPriority(parseInt(e.target.value))}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>

            {newJobType === 'recurring' && (
              <div className="space-y-1.5 col-span-2">
                <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Cron Expression</label>
                <input
                  type="text"
                  required
                  value={newJobCron}
                  onChange={(e) => setNewJobCron(e.target.value)}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm font-mono"
                  placeholder="*/5 * * * * (Every 5 minutes)"
                />
              </div>
            )}

            {(newJobType === 'scheduled' || newJobType === 'delayed') && (
              <div className="space-y-1.5 col-span-2">
                <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Scheduled Run Timestamp</label>
                <input
                  type="datetime-local"
                  required
                  value={newJobScheduled}
                  onChange={(e) => setNewJobScheduled(e.target.value)}
                  className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
                />
              </div>
            )}

            <div className="space-y-1.5 col-span-2">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Payload Parameters (JSON)</label>
              <textarea
                value={newJobPayload}
                onChange={(e) => setNewJobPayload(e.target.value)}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm h-28 resize-none font-mono"
                placeholder='{ "userId": 42 }'
              />
            </div>
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={modalLoading}>
              Enqueue Job
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
