'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, Button, Badge } from '@/components/ui';
import { Worker } from '@/lib/types';
import { Cpu, Terminal, Network, Shield, Power } from 'lucide-react';

export default function WorkersPage() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchWorkers = async () => {
    try {
      const response = await api.get('/workers');
      setWorkers(response.data);
    } catch (e) {
      console.error('Error fetching workers telemetry:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkers();
  }, []);

  const handleDrainWorker = async (workerId: string) => {
    try {
      await api.post(`/workers/${workerId}/drain`);
      fetchWorkers();
    } catch (e) {
      console.error('Failed to trigger worker drain:', e);
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
        <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">Worker Telemetry</h1>
        <p className="text-sm text-slate-400 mt-1">Monitor distributed execution nodes, capacity, system load, and thread configuration</p>
      </div>

      {workers.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-20 text-slate-500">
          <Cpu className="h-12 w-12 text-slate-700 mb-4 animate-pulse" />
          <h3 className="text-lg font-bold text-slate-350">No worker processes registered</h3>
          <p className="text-sm text-slate-550 mt-1 max-w-sm text-center">
            Start a custom Python worker host executing in the shell (`make dev-worker`) or via Docker containers to list node telemetry.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workers.map((worker) => (
            <Card key={worker.id} hoverEffect className="flex flex-col justify-between h-56 border-slate-800/80">
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
                      <Cpu className="h-4.5 w-4.5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white leading-none truncate max-w-[150px]">{worker.hostname}</h3>
                      <span className="text-[10px] text-slate-500 font-mono block mt-1">{worker.id.substring(0, 8)}</span>
                    </div>
                  </div>
                  <Badge 
                    color={
                      worker.status === 'online' ? 'emerald' : 
                      worker.status === 'busy' ? 'amber' : 
                      worker.status === 'draining' ? 'sky' : 'slate'
                    }
                  >
                    {worker.status}
                  </Badge>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-4 text-xs bg-slate-950 p-3.5 rounded-xl border border-slate-850">
                  <div className="flex justify-between items-center col-span-2">
                    <span className="text-slate-500 font-semibold uppercase text-[10px]">Active Tasks Load</span>
                    <span className="text-slate-200 font-bold font-mono">{worker.current_load} / {worker.max_concurrency} jobs</span>
                  </div>
                  <div className="pt-2 border-t border-slate-900/60 col-span-2 flex justify-between items-center text-slate-500 text-[10px]">
                    <span>LAST SEEN</span>
                    <span className="font-mono text-slate-400 font-semibold">{new Date(worker.last_seen_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-2">
                {worker.status !== 'draining' && worker.status !== 'offline' ? (
                  <Button 
                    variant="danger" 
                    size="sm" 
                    onClick={() => handleDrainWorker(worker.id)}
                    className="w-full flex items-center justify-center gap-1.5 py-2 text-xs"
                  >
                    <Power className="h-3.5 w-3.5" />
                    Drain Worker Process
                  </Button>
                ) : (
                  <Button variant="secondary" size="sm" disabled className="w-full py-2 text-xs">
                    {worker.status === 'draining' ? 'Worker Draining...' : 'Process Offline'}
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
