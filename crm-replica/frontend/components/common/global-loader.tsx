'use client';

import { appStore } from '@/stores/app-store';

export function GlobalLoader() {
  const loading = appStore((s) => s.loadingCount > 0);
  if (!loading) return null;
  return (
    <div className="fixed inset-x-0 top-0 z-[190]">
      <div className="h-1 w-full animate-pulse bg-gradient-to-r from-blue-500 via-cyan-400 to-blue-500" />
    </div>
  );
}
