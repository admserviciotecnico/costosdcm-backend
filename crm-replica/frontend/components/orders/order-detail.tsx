'use client';

import { useEffect, useMemo, useState } from 'react';
import { OrderHistory, ServiceOrder } from '@/types/domain';
import { OrdersApi } from '@/lib/api/endpoints';
import { authStore } from '@/stores/auth-store';
import { ConfirmModal } from '@/components/common/confirm-modal';
import { appStore } from '@/stores/app-store';

const adminWorkflow: Record<string, string[]> = {
  presupuesto_generado: ['oc_recibida', 'cancelado'],
  oc_recibida: ['facturado', 'cancelado'],
  facturado: ['pago_recibido', 'cancelado'],
  pago_recibido: ['documentacion_enviada'],
  documentacion_enviada: ['documentacion_aprobada'],
  documentacion_aprobada: ['service_programado'],
  service_programado: ['en_ejecucion', 'cancelado'],
  en_ejecucion: ['completado'],
  completado: [],
  cancelado: []
};

export function OrderDetail({ order, onClose, onRefresh }: { order: ServiceOrder | null; onClose: () => void; onRefresh: () => void }) {
  const [history, setHistory] = useState<OrderHistory[]>([]);
  const [confirmComplete, setConfirmComplete] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const user = authStore((s) => s.user);
  const toast = appStore((s) => s.pushToast);

  useEffect(() => {
    if (!order) return;
    OrdersApi.history(order.id).then(setHistory);
  }, [order]);

  const isTech = user?.role === 'tecnico';
  const isAdmin = user?.role === 'admin';
  const canStart = isTech && order?.estado === 'service_programado';
  const canComplete = isTech && order?.estado === 'en_ejecucion';
  const adminAllowed = useMemo(() => (order ? adminWorkflow[order.estado] || [] : []), [order]);

  if (!order) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/40 flex justify-end" onClick={onClose}>
        <div className="w-full max-w-xl bg-white dark:bg-slate-900 h-full p-5 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
          <h2 className="font-bold text-xl mb-3">Detalle #{order.id.slice(0, 8)}</h2>
          <p className="text-sm mb-2">Estado: {order.estado}</p>
          {order.deleted_at && <p className="mb-4 inline-block rounded bg-amber-100 text-amber-800 px-2 py-1 text-xs">Orden soft-deleted</p>}

          <div className="space-y-2 mb-4">
            {canStart && (
              <button className="px-3 py-2 rounded bg-orange-600 text-white" onClick={async () => { await OrdersApi.patch(order.id, { estado: 'en_ejecucion' }); toast({ type: 'success', message: 'Orden en ejecución' }); onRefresh(); }}>
                Iniciar ejecución
              </button>
            )}
            {canComplete && (
              <button className="px-3 py-2 rounded bg-green-600 text-white" onClick={() => setConfirmComplete(true)}>
                Marcar completado
              </button>
            )}
            {isAdmin && (
              <div className="flex flex-wrap gap-2">
                {adminAllowed.map((next) => (
                  <button key={next} className="px-2 py-1 rounded border" onClick={async () => { await OrdersApi.patch(order.id, { estado: next }); toast({ type: 'success', message: `Estado cambiado a ${next}` }); onRefresh(); }}>
                    {next}
                  </button>
                ))}
                <button className="px-2 py-1 rounded border border-red-300 text-red-700" onClick={() => setConfirmDelete(true)}>Soft delete</button>
              </div>
            )}
          </div>

          <h3 className="font-semibold">Timeline auditoría</h3>
          <div className="mt-2 space-y-2">
            {history.map((h) => (
              <div key={h.id} className="rounded border p-2 text-sm">
                <p className="font-medium">{h.campo_modificado || 'estado'}: {h.valor_anterior || '-'} → {h.valor_nuevo || '-'}</p>
                <p className="text-slate-500">{h.comentario || '-'} · {new Date(h.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <ConfirmModal
        open={confirmComplete}
        title="Confirmar completado"
        message="¿Seguro que deseas marcar esta orden como completada?"
        onCancel={() => setConfirmComplete(false)}
        onConfirm={async () => {
          setConfirmComplete(false);
          await OrdersApi.patch(order.id, { estado: 'completado' });
          toast({ type: 'success', message: 'Orden completada' });
          onRefresh();
        }}
      />

      <ConfirmModal
        open={confirmDelete}
        title="Confirmar soft delete"
        message="La orden quedará desactivada y no aparecerá en listados/KPI."
        onCancel={() => setConfirmDelete(false)}
        onConfirm={async () => {
          setConfirmDelete(false);
          await OrdersApi.remove(order.id);
          toast({ type: 'info', message: 'Orden eliminada lógicamente' });
          onClose();
          onRefresh();
        }}
      />
    </>
  );
}
