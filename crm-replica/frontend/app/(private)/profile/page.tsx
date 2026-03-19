'use client';

import { authStore } from '@/stores/auth-store';

export default function ProfilePage() {
  const user = authStore((s) => s.user);
  return (
    <div className="space-y-2">
      <h1 className="text-3xl font-bold">Mi Perfil</h1>
      <p>{user?.first_name} {user?.last_name}</p>
      <p className="text-slate-500">{user?.email}</p>
      <p className="text-xs uppercase">{user?.role}</p>
    </div>
  );
}
