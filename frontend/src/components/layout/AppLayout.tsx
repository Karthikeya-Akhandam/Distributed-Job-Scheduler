'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { 
  Briefcase, 
  Activity, 
  Terminal, 
  Settings, 
  LogOut, 
  Layers, 
  AlertTriangle, 
  User, 
  ChevronRight,
  Menu,
  X
} from 'lucide-react';

interface SidebarProps {
  currentOrgId?: string;
  currentProjectId?: string;
}

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout, loading } = useAuth();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // If on login or register, do not show sidebar/navbar layout
  const isAuthPage = pathname === '/login' || pathname === '/register';

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-white">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  if (isAuthPage) {
    return <>{children}</>;
  }

  const navItems = [
    { name: 'Dashboard', href: '/', icon: Activity },
    { name: 'Organizations', href: '/orgs', icon: Briefcase },
    { name: 'Workers', href: '/workers', icon: Terminal },
    { name: 'Queues & Policies', href: '/queues', icon: Layers },
    { name: 'Dead Letter Queue', href: '/dlq', icon: AlertTriangle },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col bg-slate-900 border-r border-slate-800 shrink-0">
        <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800">
          <div className="p-2 bg-indigo-600 rounded-lg text-white">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-none text-white tracking-wide">Antigravity</h1>
            <span className="text-xs text-indigo-400 font-medium uppercase tracking-widest">Job Scheduler</span>
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                  isActive 
                    ? 'bg-indigo-600/90 text-white font-medium shadow-md shadow-indigo-600/10' 
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <item.icon className={`h-5 w-5 transition-transform duration-200 ${
                  isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200 group-hover:scale-105'
                }`} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* User profile section */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-3 px-2 py-1.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 text-indigo-400 border border-slate-700">
              <User className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-200 truncate">{user?.name}</p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="mt-4 flex w-full items-center gap-3 px-4 py-2.5 text-sm text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors font-medium"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Mobile layout */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="flex md:hidden items-center justify-between px-4 py-4 bg-slate-900 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-indigo-500" />
            <span className="font-bold text-white tracking-wide">Antigravity Scheduler</span>
          </div>
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800"
          >
            <Menu className="h-6 w-6" />
          </button>
        </header>

        {/* Mobile menu overlay */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 flex md:hidden bg-slate-950/80 backdrop-blur-sm">
            <div className="w-4/5 max-w-sm bg-slate-900 p-6 flex flex-col h-full shadow-2xl border-r border-slate-800">
              <div className="flex items-center justify-between pb-6 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Activity className="h-6 w-6 text-indigo-500" />
                  <span className="font-bold text-white">Antigravity</span>
                </div>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 text-slate-400 hover:text-slate-200 rounded-lg"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <nav className="flex-1 py-6 space-y-2">
                {navItems.map((item) => {
                  const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all ${
                        isActive 
                          ? 'bg-indigo-600 text-white font-medium' 
                          : 'text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
                      }`}
                    >
                      <item.icon className="h-5 w-5" />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>

              <div className="pt-6 border-t border-slate-800">
                <div className="flex items-center gap-3 px-2 py-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 text-indigo-400">
                    <User className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-slate-200 truncate">{user?.name}</p>
                    <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="mt-4 flex w-full items-center gap-3 px-4 py-3 text-sm text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors font-medium"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto px-4 py-6 md:p-8 bg-slate-950">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
