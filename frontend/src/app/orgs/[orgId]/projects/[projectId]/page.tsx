'use client';

import React, { useEffect, useState, use } from 'react';
import { api } from '@/lib/api';
import { Card, Button, Modal, Badge } from '@/components/ui';
import { Project, Queue, RetryPolicy } from '@/lib/types';
import Link from 'next/link';
import { Layers, Plus, Calendar, ArrowLeft, Play, Pause, ChevronRight } from 'lucide-react';

interface ProjectDetailPageProps {
  params: Promise<{ orgId: string; projectId: string }>;
}

export default function ProjectDetailPage({ params }: ProjectDetailPageProps) {
  const { orgId, projectId } = use(params);
  const [project, setProject] = useState<Project | null>(null);
  const [queues, setQueues] = useState<Queue[]>([]);
  const [policies, setPolicies] = useState<RetryPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newQueueName, setNewQueueName] = useState('');
  const [newQueuePriority, setNewQueuePriority] = useState(5);
  const [newQueueLimit, setNewQueueLimit] = useState(10);
  const [newQueuePolicy, setNewQueuePolicy] = useState('');
  const [modalLoading, setModalLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    try {
      const projRes = await api.get(`/projects/${projectId}`);
      setProject(projRes.data);

      const queuesRes = await api.get(`/projects/${projectId}/queues`);
      setQueues(queuesRes.data.data);

      const policiesRes = await api.get('/retry-policies');
      setPolicies(policiesRes.data);
    } catch (e) {
      console.error('Error fetching project details data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const handleCreateQueue = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    setError('');
    try {
      await api.post(`/projects/${projectId}/queues`, {
        name: newQueueName,
        priority: newQueuePriority,
        concurrency_limit: newQueueLimit,
        retry_policy_id: newQueuePolicy || null,
      });
      setNewQueueName('');
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      setError(
        err.response?.data?.message || 
        err.response?.data?.detail?.message || 
        'Failed to create queue.'
      );
    } finally {
      setModalLoading(false);
    }
  };

  const toggleQueuePause = async (queue: Queue) => {
    try {
      const action = queue.status === 'paused' ? 'resume' : 'pause';
      await api.post(`/queues/${queue.id}/${action}`);
      fetchData();
    } catch (e) {
      console.error('Failed to change queue status:', e);
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
        <Link href={`/orgs/${orgId}`} className="text-slate-400 hover:text-slate-200 flex items-center gap-1 text-sm font-semibold transition-colors">
          <ArrowLeft className="h-4 w-4" />
          Back to Organization
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">{project?.name}</h1>
            <Badge color="slate">slug: {project?.slug}</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">{project?.description || 'No description provided'}</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Create Queue
        </Button>
      </div>

      <div>
        <h2 className="text-lg font-bold text-white mb-4">Job Queues</h2>
        {queues.length === 0 ? (
          <Card className="flex flex-col items-center justify-center py-16 text-slate-500">
            <Layers className="h-10 w-10 text-slate-700 mb-3" />
            <p className="text-sm font-semibold text-slate-350">No queues configured</p>
            <p className="text-xs text-slate-550 mt-1 max-w-sm text-center">
              Define background processing queues to dispatch asynchronous immediate, delayed, and cron recurring jobs.
            </p>
            <Button onClick={() => setIsModalOpen(true)} className="mt-4 text-xs py-2">
              Create First Queue
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {queues.map((queue) => (
              <Card key={queue.id} hoverEffect className="flex flex-col justify-between h-48">
                <div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
                        <Layers className="h-4.5 w-4.5" />
                      </div>
                      <h3 className="font-bold text-white leading-none hover:text-indigo-400 transition-colors">
                        <Link href={`/orgs/${orgId}/projects/${projectId}/queues/${queue.id}`}>{queue.name}</Link>
                      </h3>
                    </div>
                    <Badge color={queue.status === 'active' ? 'emerald' : 'amber'}>
                      {queue.status}
                    </Badge>
                  </div>

                  <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs border-t border-b border-slate-800/40 py-2 mt-4">
                    <div>
                      <span className="block text-slate-500 text-[10px] font-semibold uppercase tracking-wider">Priority</span>
                      <span className="text-slate-200 font-bold">{queue.priority}</span>
                    </div>
                    <div>
                      <span className="block text-slate-500 text-[10px] font-semibold uppercase tracking-wider">Max Load</span>
                      <span className="text-slate-200 font-bold">{queue.concurrency_limit} c</span>
                    </div>
                    <div>
                      <span className="block text-slate-500 text-[10px] font-semibold uppercase tracking-wider">Shards</span>
                      <span className="text-slate-200 font-bold">{queue.shard_count}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex gap-2 pt-2">
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    onClick={() => toggleQueuePause(queue)}
                    className="flex-1 flex items-center gap-1.5"
                  >
                    {queue.status === 'paused' ? (
                      <>
                        <Play className="h-3.5 w-3.5 text-emerald-400" />
                        Resume Queue
                      </>
                    ) : (
                      <>
                        <Pause className="h-3.5 w-3.5 text-amber-400" />
                        Pause Queue
                      </>
                    )}
                  </Button>
                  
                  <Link href={`/orgs/${orgId}/projects/${projectId}/queues/${queue.id}`}>
                    <Button variant="ghost" size="sm" className="flex items-center gap-1" title="View Queue Detail">
                      Inspect
                      <ChevronRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Queue Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create New Queue">
        <form onSubmit={handleCreateQueue} className="space-y-4">
          {error && (
            <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-xs text-rose-400">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5 col-span-2">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Queue Name</label>
              <input
                type="text"
                required
                value={newQueueName}
                onChange={(e) => setNewQueueName(e.target.value)}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
                placeholder="e.g. process-webhooks"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Queue Priority (1-10)</label>
              <input
                type="number"
                min="1"
                max="10"
                required
                value={newQueuePriority}
                onChange={(e) => setNewQueuePriority(parseInt(e.target.value))}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Concurrency Limit</label>
              <input
                type="number"
                min="1"
                max="1000"
                required
                value={newQueueLimit}
                onChange={(e) => setNewQueueLimit(parseInt(e.target.value))}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>

            <div className="space-y-1.5 col-span-2">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Retry Policy</label>
              <select
                value={newQueuePolicy}
                onChange={(e) => setNewQueuePolicy(e.target.value)}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              >
                <option value="">No Retry Policy (Immediately fails on exception)</option>
                {policies.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.strategy} - max {p.max_retries} retries)</option>
                ))}
              </select>
            </div>
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={modalLoading}>
              Create Queue
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
