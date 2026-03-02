'use client';

import Link from 'next/link';
import { LayoutDashboard, ClipboardList, Calendar, Users, Package, UserCircle } from 'lucide-react';
import { authStore } from '@/stores/auth-store';

const links = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/orders', label: 'Pedidos', icon: ClipboardList },
  { href: '/calendar', label: 'Calendario', icon: Calendar },
  { href: '/clients', label: 'Clientes', icon: Users, admin: true },
  { href: '/equipments', label: 'Equipos', icon: Package, admin: true },
  { href: '/profile', label: 'Mi Perfil', icon: UserCircle }
];

export function Sidebar() {
  const user = authStore((s) => s.user);
  return (
    <aside className="w-72 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 p-4 h-screen sticky top-0">
      <h1 className="text-xl font-bold mb-6">DCM Solution</h1>
      <nav className="space-y-1">
        {links.filter((l) => !l.admin || user?.role === 'admin').map((l) => (
          <Link key={l.href} href={l.href} className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-800">
            <l.icon className="h-4 w-4" /> {l.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
