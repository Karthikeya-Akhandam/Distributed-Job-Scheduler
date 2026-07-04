'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, Button, Modal } from '@/components/ui';
import { Organization } from '@/lib/types';
import Link from 'next/link';
import { Briefcase, Plus, UserPlus, Shield, Calendar } from 'lucide-react';

export default function OrgsPage() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgSlug, setNewOrgSlug] = useState('');
  const [modalLoading, setModalLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchOrgs = async () => {
    try {
      const response = await api.get('/orgs');
      // API returns paginated response
      setOrgs(response.data.data);
    } catch (e) {
      console.error('Error fetching organizations:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgs();
  }, []);

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    setError('');
    try {
      await api.post('/orgs', { name: newOrgName, slug: newOrgSlug });
      setNewOrgName('');
      setNewOrgSlug('');
      setIsModalOpen(false);
      fetchOrgs();
    } catch (err: any) {
      setError(
        err.response?.data?.message || 
        err.response?.data?.detail?.message || 
        'Failed to create organization.'
      );
    } finally {
      setModalLoading(false);
    }
  };

  const autoGenerateSlug = (name: string) => {
    setNewOrgName(name);
    setNewOrgSlug(
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
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">Organizations</h1>
          <p className="text-sm text-slate-400">Manage your business boundaries and user workspace access settings</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Create Organization
        </Button>
      </div>

      {orgs.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-20 text-slate-500">
          <Briefcase className="h-12 w-12 text-slate-700 mb-4" />
          <h3 className="text-lg font-bold text-slate-350">No organizations found</h3>
          <p className="text-sm text-slate-550 mt-1 max-w-sm text-center">
            Organizations group your projects, queues, and users together. Get started by creating your first organization.
          </p>
          <Button onClick={() => setIsModalOpen(true)} className="mt-6">
            Create First Organization
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {orgs.map((org) => (
            <Card key={org.id} hoverEffect className="flex flex-col justify-between h-48">
              <div>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
                    <Briefcase className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white leading-none hover:text-indigo-400 transition-colors">
                      <Link href={`/orgs/${org.id}`}>{org.name}</Link>
                    </h3>
                    <span className="text-xs text-slate-500 font-mono">slug: {org.slug}</span>
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-xs text-slate-400">
                  <Calendar className="h-3.5 w-3.5 text-slate-500" />
                  <span>Created {new Date(org.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              
              <div className="mt-6 flex gap-2">
                <Link href={`/orgs/${org.id}`} className="flex-1">
                  <Button variant="secondary" className="w-full text-xs py-2">
                    Open Projects
                  </Button>
                </Link>
                <Link href={`/orgs/${org.id}/members`}>
                  <Button variant="ghost" className="text-xs py-2 flex items-center gap-1.5" title="Manage Members">
                    <UserPlus className="h-3.5 w-3.5" />
                    Members
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Org Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create New Organization">
        <form onSubmit={handleCreateOrg} className="space-y-4">
          {error && (
            <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-xs text-rose-400">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Organization Name</label>
            <input
              type="text"
              required
              value={newOrgName}
              onChange={(e) => autoGenerateSlug(e.target.value)}
              className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              placeholder="e.g. Acme Corporation"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Workspace Slug</label>
            <input
              type="text"
              required
              value={newOrgSlug}
              onChange={(e) => setNewOrgSlug(e.target.value)}
              className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm font-mono"
              placeholder="e.g. acme-corp"
            />
            <p className="text-[11px] text-slate-500">Slugs define your organization's URL workspace boundaries (lowercase letters, numbers, and hyphens).</p>
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={modalLoading}>
              Create Organization
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
