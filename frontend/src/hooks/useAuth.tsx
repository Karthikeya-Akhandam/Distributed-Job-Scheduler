'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { jwtDecode } from 'jwt-decode';
import { api } from '@/lib/api';
import { User } from '@/lib/types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (token: string, refreshToken: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const decoded: any = jwtDecode(token);
          // Simple client side expiry check
          if (decoded.exp * 1000 < Date.now()) {
            logout();
          } else {
            // Load current user profile from /auth/me
            const response = await api.get('/auth/me');
            setUser(response.data);
          }
        } catch (err) {
          logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = (token: string, refreshToken: string) => {
    localStorage.setItem('token', token);
    localStorage.setItem('refresh_token', refreshToken);
    try {
      const decoded: any = jwtDecode(token);
      api.get('/auth/me').then((response) => {
        setUser(response.data);
        router.push('/');
      });
    } catch (e) {
      logout();
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
