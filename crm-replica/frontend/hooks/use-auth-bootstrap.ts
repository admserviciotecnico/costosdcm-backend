'use client';

import { useEffect } from 'react';
import { AuthApi } from '@/lib/api/endpoints';
import { authStore } from '@/stores/auth-store';

export function useAuthBootstrap() {
  const token = authStore((s) => s.token);
  const setUser = authStore((s) => s.setUser);
  const logout = authStore((s) => s.logout);

  useEffect(() => {
    if (!token) return;
    AuthApi.me().then(setUser).catch(logout);
  }, [token, setUser, logout]);
}
