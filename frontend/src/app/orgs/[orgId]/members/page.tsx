'use client';

import React, { useEffect, useState, use } from 'react';
import { api } from '@/lib/api';
import { Card, Button, Modal, Badge } from '@/components/ui';
import { OrgMember } from '@/lib/types';
import Link from 'next/link';
import { User, Shield, ArrowLeft, Plus, Trash } from 'lucide-react';

interface OrgMembersPageProps {
  params: Promise<{ orgId: string }>;
}

export default function OrgMembersPage({ params }: OrgMembersPageProps) {
  const { orgId } = use(params);
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [modalLoading, setModalLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchMembers = async () => {
    try {
      const response = await api.get(`/orgs/${orgId}/members`);
      setMembers(response.data);
    } catch (e) {
      console.error('Error fetching organization members:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, [orgId]);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    setError('');
    try {
      await api.post(`/orgs/${orgId}/members`, { 
        email: inviteEmail, 
        role: inviteRole 
      });
      setInviteEmail('');
      setIsModalOpen(false);
      fetchMembers();
    } catch (err: any) {
      setError(
        err.response?.data?.message || 
        err.response?.data?.detail?.message || 
        'Failed to add member to organization.'
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
      <div className="flex items-center gap-2">
        <Link href={`/orgs/${orgId}`} className="text-slate-400 hover:text-slate-200 flex items-center gap-1 text-sm font-semibold transition-colors">
          <ArrowLeft className="h-4 w-4" />
          Back to Organization Details
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">Workspace Members</h1>
          <p className="text-sm text-slate-400 mt-1">Review team members roles, invites, and manage access parameters</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add Member
        </Button>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider bg-slate-900/40">
                <th className="py-4 px-6">Name</th>
                <th className="py-4 px-6">Email</th>
                <th className="py-4 px-6">Role</th>
                <th className="py-4 px-6">Joined Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-sm text-slate-350">
              {members.map((member) => (
                <tr key={member.id} className="hover:bg-slate-900/25 transition-colors">
                  <td className="py-4 px-6 font-semibold text-slate-200">{member.user_name || 'System Member'}</td>
                  <td className="py-4 px-6">{member.user_email || 'N/A'}</td>
                  <td className="py-4 px-6">
                    <Badge color={member.role === 'owner' ? 'rose' : member.role === 'admin' ? 'amber' : member.role === 'member' ? 'indigo' : 'slate'}>
                      {member.role}
                    </Badge>
                  </td>
                  <td className="py-4 px-6 text-slate-500">{new Date(member.joined_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add Member Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Invite Member to Organization">
        <form onSubmit={handleAddMember} className="space-y-4">
          {error && (
            <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-xs text-rose-400">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Email Address</label>
            <input
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
              placeholder="team-member@example.com"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-350 uppercase tracking-wider">Organizational Role</label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="w-full rounded-xl bg-slate-800 border border-slate-700/80 px-4 py-2.5 text-slate-100 placeholder-slate-550 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
            >
              <option value="member">member (Read/Write queues & jobs)</option>
              <option value="admin">admin (Configure workspace boundaries)</option>
              <option value="viewer">viewer (Read-only dashboards)</option>
            </select>
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={modalLoading}>
              Add Member
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
