'use client';

import { useEffect } from 'react';
import { appStore } from '@/stores/app-store';

export function Toaster() {
  const toasts = appStore((s) => s.toasts);
  const remove = appStore((s) => s.removeToast);

  useEffect(() => {
    const timers = toasts.map((t) => setTimeout(() => remove(t.id), 3500));
    return () => timers.forEach(clearTimeout);
  }, [toasts, remove]);

  return (
    <div className="fixed right-4 top-4 z-[200] space-y-2">
      {toasts.map((t) => (
        <div key={t.id} className={`rounded-lg px-4 py-3 text-sm shadow-lg border ${t.type === 'error' ? 'bg-red-50 border-red-200 text-red-700' : t.type === 'success' ? 'bg-green-50 border-green-200 text-green-700' : 'bg-slate-50 border-slate-200 text-slate-700'}`}>
          {t.message}
        </div>
      ))}
    </div>
  );
}
