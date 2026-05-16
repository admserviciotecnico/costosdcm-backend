'use client';

import { LogOut, Moon, Sun } from 'lucide-react';
import { authStore } from '@/stores/auth-store';
import { uiStore } from '@/stores/ui-store';

export function Header() {
  const user = authStore((s) => s.user);
  const logout = authStore((s) => s.logout);
  const dark = uiStore((s) => s.darkMode);
  const setDark = uiStore((s) => s.setDarkMode);

  return (
    <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 flex items-center justify-between">
      <p className="text-sm text-slate-500">{user ? `Hola, ${user.first_name}` : 'DCM CRM'}</p>
      <div className="flex items-center gap-2">
        <button onClick={() => setDark(!dark)} className="p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">{dark ? <Sun size={16} /> : <Moon size={16} />}</button>
        <button onClick={() => { logout(); window.location.href = '/login'; }} className="p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800"><LogOut size={16} /></button>
      </div>
    </header>
  );
}
