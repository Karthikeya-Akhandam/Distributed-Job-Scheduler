'use client';

import React, { useEffect, useState, use } from 'react';
import { api } from '@/lib/api';
import { Card, Button, Modal, Badge } from '@/components/ui';
import { Project, Organization } from '@/lib/types';
import Link from 'next/link';
import { Folder, Plus, Calendar, ArrowLeft, Layers } from 'lucide-react';

interface OrgDetailPageProps {
  params: Promise<{ orgId: string }>;
}

export default function OrgDetailPage({ params }: OrgDetailPageProps) {
  const { orgId } = use(params);
  const [org, setOrg] = useState<Organization | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectSlug, setNewProjectSlug] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [modalLoading, setModalLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchOrgDetails = async () => {
    try {
      const orgRes = await api.get(`/orgs/${orgId}`);
      setOrg(orgRes.data);
      
      const projectsRes = await api.get(`/orgs/${orgId}/projects`);
      setProjects(projectsRes.data.data);
    } catch (e) {
      console.error('Error fetching org detail data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgDetails();
  }, [orgId]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    setError('');
    try {
      await api.post(`/orgs/${orgId}/projects`, { 
        name: newProjectName, 
        slug: newProjectSlug,
        description: newProjectDesc 
      });
      setNewProjectName('');
      setNewProjectSlug('');
      setNewProjectDesc('');
      setIsModalOpen(false);
      fetchOrgDetails();
    } catch (err: any) {
      setError(
        err.response?.data?.message || 
        err.response?.data?.detail?.message || 
        'Failed to create project.'
      );
    } finally {
      setModalLoading(false);
    }
  };

  const autoGenerateSlug = (name: string) => {
    setNewProjectName(name);
    setNewProjectSlug(
      name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)+/g, '')
    );
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
        <Link href="/orgs" className="text-slate-400 hover:text-slate-200 flex items-center gap-1 text-sm font-semibold transition-colors">
          <ArrowLeft className="h-4 w-4" />
          Back to Organizations
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">{org?.name}</h1>
            <Badge color="indigo">slug: {org?.slug}</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">Manage project groups and application queues within this organization</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>

      <div>
        <h2 className="text-lg font-bold text-white mb-4">Projects</h2>
        {projects.length === 0 ? (
          <Card className="flex flex-col items-center justify-center py-16 text-slate-500">
            <Folder className="h-10 w-10 text-slate-700 mb-3" />
            <p className="text-sm font-semibold text-slate-350">No projects found</p>
            <p className="text-xs text-slate-550 mt-1 max-w-sm text-center">
              Projects compartmentalize your job schedules. Create a project to start configuring queues.
            </p>
            <Button onClick={() => setIsModalOpen(true)} className="mt-4 text-xs py-2">
              Create Project
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Card key={project.id} hoverEffect className="flex flex-col justify-between h-48">
                <div>
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
                      <Folder className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white leading-none hover:text-indigo-400 transition-colors">
                        <Link href={`/orgs/${orgId}/projects/${project.id}`}>{project.name}</Link>
                      </h3>
                      <span className="text-[11px] text-slate-500 font-mono">slug: {project.slug}</span>
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-slate-400 line-clamp-2 leading-relaxed">{project.description || 'No description provided'}</p>
                </div>
                
                <div className="mt-5 flex justify-between items-center border-t border-slate-800/60 pt-3">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500">
                    <Layers className="h-3.5 w-3.5" />
                    <span>{project.queue_count ?? 0} Queues</span>
                  </div>
                  <Link href={`/orgs/${orgId}/projects/${project.id}`}>
                    <Button variant="secondary" className="text-xs py-1.5 px-3">
                      Open Project
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create New Project">
        <form onSubmit={handleCreateProject} className="space-y-4">
          {error && (
            <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-xs text-rose-400">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Project Name</label>
            <input
              type="text"
              required
              value={newProjectName}
              onChange={(e) => autoGenerateSlug(e.target.value)}
              className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              placeholder="e.g. Core Background Engine"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Project Slug</label>
            <input
              type="text"
              required
              value={newProjectSlug}
              onChange={(e) => setNewProjectSlug(e.target.value)}
              className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm font-mono"
              placeholder="e.g. core-engine"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Description (Optional)</label>
            <textarea
              value={newProjectDesc}
              onChange={(e) => setNewProjectDesc(e.target.value)}
              className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm h-24 resize-none"
              placeholder="What does this project do?"
            />
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={modalLoading}>
              Create Project
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
