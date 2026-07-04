'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, Button } from '@/components/ui';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Activity, Play, Pause, AlertOctagon, Cpu, CheckCircle, Clock } from 'lucide-react';
import Link from 'next/link';

export default function DashboardOverview() {
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { event } = useWebSocket();

  const fetchOverview = async () => {
    try {
      const response = await api.get('/metrics/overview');
      setOverview(response.data);
    } catch (e) {
      console.error('Error fetching metrics overview:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  // Update metrics reactively when WebSocket events arrive
  useEffect(() => {
    if (event) {
      // Re-fetch overview dynamically on job status changes or worker changes
      if (['job_completed', 'job_failed', 'worker_online', 'worker_offline', 'dlq_entry'].includes(event.type)) {
        fetchOverview();
      }
    }
  }, [event]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  const cards = [
    { name: 'Active Workers', value: overview?.active_workers ?? 0, icon: Cpu, color: 'text-indigo-400 bg-indigo-500/10' },
    { name: 'Total Jobs Created', value: overview?.total_jobs ?? 0, icon: Activity, color: 'text-sky-400 bg-sky-500/10' },
    { name: 'Completed (Last Hr)', value: overview?.jobs_completed_last_hour ?? 0, icon: CheckCircle, color: 'text-emerald-400 bg-emerald-500/10' },
    { name: 'Failed Attempts (Last Hr)', value: overview?.jobs_failed_last_hour ?? 0, icon: AlertOctagon, color: 'text-rose-400 bg-rose-500/10' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">System Dashboard</h1>
          <p className="text-sm text-slate-400">Real-time job execution telemetry and queue health overview</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <Card key={card.name} hoverEffect>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">{card.name}</p>
                <p className="mt-2 text-3xl font-extrabold text-white">{card.value}</p>
              </div>
              <div className={`p-3 rounded-2xl ${card.color}`}>
                <card.icon className="h-6 w-6" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Real-time event log */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <h2 className="text-lg font-bold text-white">Live Event Monitor</h2>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 animate-ping rounded-full bg-emerald-500"></span>
              <span className="text-xs text-emerald-400 font-semibold uppercase tracking-wide">Live Streaming</span>
            </div>
          </div>

          <div className="mt-4 space-y-3 max-h-[400px] overflow-y-auto pr-2">
            {event ? (
              <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 text-sm flex gap-3 items-start animate-slide-up">
                <Clock className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-white uppercase tracking-wider text-xs bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded-md">{event.type}</span>
                    <span className="text-xs text-slate-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <pre className="mt-2 text-xs text-slate-300 overflow-x-auto bg-slate-900/60 p-3 rounded-lg border border-slate-800/80 leading-relaxed">
                    {JSON.stringify(event.data, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-slate-500">
                <Activity className="h-10 w-10 text-slate-700 animate-pulse mb-3" />
                <p className="text-sm font-medium">Waiting for job events to trigger...</p>
                <p className="text-xs text-slate-650 mt-1">Start background workers to start execution</p>
              </div>
            )}
          </div>
        </Card>

        {/* Quick controls / system info */}
        <Card className="space-y-6">
          <div>
            <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-3">Platform Actions</h2>
            <div className="mt-4 space-y-2">
              <Link href="/queues" className="block">
                <Button variant="secondary" className="w-full justify-start text-sm py-3">
                  Configure Job Queues
                </Button>
              </Link>
              <Link href="/workers" className="block">
                <Button variant="secondary" className="w-full justify-start text-sm py-3">
                  Inspect Worker Hosts
                </Button>
              </Link>
              <Link href="/dlq" className="block">
                <Button variant="danger" className="w-full justify-start text-sm py-3">
                  Inspect Dead Letter Queue
                </Button>
              </Link>
            </div>
          </div>

          <div className="border-t border-slate-800 pt-6">
            <h3 className="text-sm font-semibold text-slate-300">System Telemetry</h3>
            <div className="mt-3 space-y-2.5 text-sm text-slate-400">
              <div className="flex justify-between">
                <span>Avg Latency (Completed)</span>
                <span className="font-semibold text-white">{overview?.avg_execution_time_ms ? `${overview.avg_execution_time_ms} ms` : 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span>DLQ Entry Total</span>
                <span className="font-semibold text-rose-400">{overview?.dlq_entries ?? 0} dead</span>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
