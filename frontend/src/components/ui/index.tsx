'use client';

import React from 'react';
import clsx from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading,
  className,
  disabled,
  ...props
}) => {
  return (
    <button
      disabled={disabled || isLoading}
      className={clsx(
        'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]',
        {
          'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/10 hover:shadow-indigo-500/20': variant === 'primary',
          'bg-slate-800 hover:bg-slate-700/80 text-slate-100 border border-slate-700/80': variant === 'secondary',
          'bg-rose-600 hover:bg-rose-500 text-white shadow-md shadow-rose-600/10': variant === 'danger',
          'hover:bg-slate-800 text-slate-400 hover:text-slate-200': variant === 'ghost',
          'px-3 py-1.5 text-xs': size === 'sm',
          'px-4 py-2.5 text-sm': size === 'md',
          'px-5 py-3 text-base': size === 'lg',
        },
        className
      )}
      {...props}
    >
      {isLoading ? (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent mr-2"></span>
      ) : null}
      {children}
    </button>
  );
};

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, hoverEffect, className, ...props }) => {
  return (
    <div
      className={clsx(
        'bg-slate-900 border border-slate-800/80 rounded-2xl p-6 transition-all duration-300',
        {
          'hover:border-slate-700 hover:shadow-lg hover:shadow-slate-950/40 hover:-translate-y-0.5': hoverEffect,
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  color?: 'emerald' | 'amber' | 'indigo' | 'slate' | 'rose' | 'sky';
}

export const Badge: React.FC<BadgeProps> = ({ children, color = 'slate', className, ...props }) => {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-lg tracking-wide',
        {
          'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': color === 'emerald',
          'bg-amber-500/10 text-amber-400 border border-amber-500/20': color === 'amber',
          'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20': color === 'indigo',
          'bg-rose-500/10 text-rose-400 border border-rose-500/20': color === 'rose',
          'bg-sky-500/10 text-sky-400 border border-sky-500/20': color === 'sky',
          'bg-slate-800 text-slate-300 border border-slate-700': color === 'slate',
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4 animate-fade-in">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 relative">
        <h3 className="text-lg font-bold text-white mb-4">{title}</h3>
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-850"
        >
          <span className="sr-only">Close</span>
          &times;
        </button>
        <div className="space-y-4">{children}</div>
      </div>
    </div>
  );
};
