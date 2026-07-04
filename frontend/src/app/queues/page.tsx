'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, Button, Modal, Badge } from '@/components/ui';
import { Queue, RetryPolicy } from '@/lib/types';
import { Layers, Plus, Shield, RefreshCw } from 'lucide-react';

export default function QueuesOverviewPage() {
  const [queues, setQueues] = useState<Queue[]>([]);
  const [policies, setPolicies] = useState<RetryPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newPolicyName, setNewPolicyName] = useState('');
  const [newPolicyStrategy, setNewPolicyStrategy] = useState('exponential');
  const [newPolicyRetries, setNewPolicyRetries] = useState(3);
  const [newPolicyDelay, setNewPolicyDelay] = useState(1000);
  const [modalLoading, setModalLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    try {
      const policiesRes = await api.get('/retry-policies');
      setPolicies(policiesRes.data);

      const orgsRes = await api.get('/orgs');
      if (orgsRes.data.data.length > 0) {
        const orgId = orgsRes.data.data[0].id;
        const projectsRes = await api.get(`/orgs/${orgId}/projects`);
        
        let queuesAccumulator: Queue[] = [];
        for (const project of projectsRes.data.data) {
          const queuesRes = await api.get(`/projects/${project.id}/queues`);
          queuesAccumulator = [...queuesAccumulator, ...queuesRes.data.data];
        }
        setQueues(queuesAccumulator);
      }
    } catch (e) {
      console.error('Error fetching queues or retry policies:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    setError('');
    try {
      await api.post('/retry-policies', {
        name: newPolicyName,
        strategy: newPolicyStrategy,
        max_retries: newPolicyRetries,
        initial_delay_ms: newPolicyDelay,
      });
      setNewPolicyName('');
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      setError(
        err.response?.data?.message || 
        err.response?.data?.detail?.message || 
        'Failed to create retry policy.'
      );
    } finally {
      setModalLoading(false);
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
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">Queues & Retry Policies</h1>
          <p className="text-sm text-slate-400 mt-1">Configure global retry templates and review all active scheduler pipelines</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          New Retry Policy
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Queues list */}
        <Card className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-3">Active Job Queues</h2>
          {queues.length === 0 ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-500 text-sm">
              <span>No active queues found across projects.</span>
            </div>
          ) : (
            <div className="space-y-3">
              {queues.map((queue) => (
                <div key={queue.id} className="p-4 rounded-xl bg-slate-850/60 border border-slate-800/80 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
                      <Layers className="h-4.5 w-4.5" />
                    </div>
                    <div>
                      <span className="font-semibold text-slate-200 block">{queue.name}</span>
                      <span className="text-[10px] text-slate-500 font-mono">Limit: {queue.concurrency_limit} concurrency</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Badge color="slate">Priority {queue.priority}</Badge>
                    <Badge color={queue.status === 'active' ? 'emerald' : 'amber'}>{queue.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Retry policies list */}
        <Card className="space-y-4">
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-3">Retry Policies</h2>
          <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
            {policies.map((p) => (
              <div key={p.id} className="p-4 rounded-xl bg-slate-850/80 border border-slate-800/80 text-xs space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-200">{p.name}</span>
                  <Badge color="indigo">{p.strategy}</Badge>
                </div>
                <div className="text-slate-450 space-y-1 pt-1 font-mono text-[11px]">
                  <div>Max Retries: {p.max_retries}</div>
                  <div>Base Delay: {p.initial_delay_ms} ms</div>
                  <div>Multiplier: {p.backoff_multiplier}x</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Create Policy Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create New Retry Policy">
        <form onSubmit={handleCreatePolicy} className="space-y-4">
          {error && (
            <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-xs text-rose-400">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Policy Name</label>
            <input
              type="text"
              required
              value={newPolicyName}
              onChange={(e) => setNewPolicyName(e.target.value)}
              className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              placeholder="e.g. Critical API Backoff"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Backoff Strategy</label>
              <select
                value={newPolicyStrategy}
                onChange={(e) => setNewPolicyStrategy(e.target.value)}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              >
                <option value="exponential">exponential</option>
                <option value="linear">linear</option>
                <option value="fixed">fixed</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Max Retries</label>
              <input
                type="number"
                min="0"
                max="20"
                required
                value={newPolicyRetries}
                onChange={(e) => setNewPolicyRetries(parseInt(e.target.value))}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>

            <div className="space-y-1.5 col-span-2">
              <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Base Delay (ms)</label>
              <input
                type="number"
                min="100"
                required
                value={newPolicyDelay}
                onChange={(e) => setNewPolicyDelay(parseInt(e.target.value))}
                className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              />
            </div>
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={modalLoading}>
              Create Policy
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
