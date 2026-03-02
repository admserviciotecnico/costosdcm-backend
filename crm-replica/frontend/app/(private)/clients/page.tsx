'use client';

import { useEffect, useState } from 'react';
import { ClientsApi } from '@/lib/api/endpoints';
import { Client } from '@/types/domain';
import { EmptyState } from '@/components/common/empty-state';
import { ConfirmModal } from '@/components/common/confirm-modal';

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [toDelete, setToDelete] = useState<Client | null>(null);

  const load = () => ClientsApi.list().then(setClients);
  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">Clientes</h1>
      {!clients.length ? (
        <EmptyState title="No hay clientes" subtitle="Crea un cliente para comenzar a gestionar documentación y órdenes." />
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {clients.map((c) => (
            <div key={c.id} className="rounded-xl border p-4 bg-white dark:bg-slate-900">
              <p className="font-semibold">{c.nombre_empresa}</p>
              <p className="text-sm text-slate-500">{c.email}</p>
              <button className="mt-3 text-sm text-red-600" onClick={() => setToDelete(c)}>Soft delete</button>
            </div>
          ))}
        </div>
      )}

      <ConfirmModal
        open={!!toDelete}
        title="Eliminar cliente"
        message="Se realizará soft delete. Si tiene órdenes activas, el backend lo bloqueará."
        onCancel={() => setToDelete(null)}
        onConfirm={async () => {
          if (!toDelete) return;
          await ClientsApi.remove(toDelete.id);
          setToDelete(null);
          load();
        }}
      />
    </div>
  );
}
