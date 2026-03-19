'use client';

import { useEffect, useState } from 'react';
import { EquipmentsApi } from '@/lib/api/endpoints';
import { Equipment } from '@/types/domain';
import { EmptyState } from '@/components/common/empty-state';
import { ConfirmModal } from '@/components/common/confirm-modal';

export default function EquipmentsPage() {
  const [items, setItems] = useState<Equipment[]>([]);
  const [toDelete, setToDelete] = useState<Equipment | null>(null);

  const load = () => EquipmentsApi.list().then(setItems);
  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">Equipos</h1>
      {!items.length ? (
        <EmptyState title="No hay equipos" subtitle="Asocia equipos a clientes para gestionar órdenes de servicio." />
      ) : (
        <div className="grid md:grid-cols-3 gap-3">
          {items.map((eq) => (
            <div key={eq.id} className="rounded-xl border p-4 bg-white dark:bg-slate-900">
              <p className="font-semibold">{eq.tipo_equipo}</p>
              <p className="text-sm">{eq.numero_serie}</p>
              <button className="mt-3 text-sm text-red-600" onClick={() => setToDelete(eq)}>Soft delete</button>
            </div>
          ))}
        </div>
      )}

      <ConfirmModal
        open={!!toDelete}
        title="Eliminar equipo"
        message="Se realizará soft delete de este equipo."
        onCancel={() => setToDelete(null)}
        onConfirm={async () => {
          if (!toDelete) return;
          await EquipmentsApi.remove(toDelete.id);
          setToDelete(null);
          load();
        }}
      />
    </div>
  );
}
