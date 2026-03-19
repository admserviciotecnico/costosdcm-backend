'use client';

import { ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authStore } from '@/stores/auth-store';
import { useAuthBootstrap } from '@/hooks/use-auth-bootstrap';

export function Protected({ children }: { children: ReactNode }) {
  const token = authStore((s) => s.token);
  const router = useRouter();
  useAuthBootstrap();

  useEffect(() => {
    if (!token) router.replace('/login');
  }, [token, router]);

  if (!token) return <div className="p-8">Verificando sesión...</div>;
  return <>{children}</>;
}
