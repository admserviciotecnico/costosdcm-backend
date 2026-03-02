'use client';

import React, { memo, useMemo } from 'react';
import { ServiceOrder } from '@/types/domain';
import { PriorityBadge, StatusBadge } from '@/components/common/badges';
import { EmptyState } from '@/components/common/empty-state';

function OrdersTableComponent({ orders, onClick }: { orders: ServiceOrder[]; onClick: (o: ServiceOrder) => void }) {
  const rows = useMemo(
    () =>
      orders.map((o) => {
        const delayed = o.fecha_programada
          ? new Date(o.fecha_programada) < new Date() && !['completado', 'cancelado'].includes(o.estado)
          : false;
        return { ...o, delayed };
      }),
    [orders]
  );

  if (!rows.length) {
    return <EmptyState title="Sin órdenes para mostrar" subtitle="Ajusta filtros o crea nuevas órdenes." />;
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
      <table className="w-full text-sm">
        <thead className="text-left bg-slate-50 dark:bg-slate-800">
          <tr>
            <th className="p-3">ID</th>
            <th className="p-3">Cliente</th>
            <th className="p-3">Estado</th>
            <th className="p-3">Técnicos</th>
            <th className="p-3">Prioridad</th>
            <th className="p-3">Fecha</th>
            <th className="p-3">Demorado</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((o) => (
            <tr key={o.id} onClick={() => onClick(o)} className="cursor-pointer border-t hover:bg-slate-50 dark:hover:bg-slate-800/30">
              <td className="p-3 font-mono">#{o.id.slice(0, 8)}</td>
              <td className="p-3">{o.client?.nombre_empresa || o.client_id}</td>
              <td className="p-3">
                <StatusBadge value={o.estado} />
              </td>
              <td className="p-3">{o.technicians?.length || 0}</td>
              <td className="p-3">
                <PriorityBadge value={o.prioridad} />
              </td>
              <td className="p-3">{o.fecha_programada ? new Date(o.fecha_programada).toLocaleDateString() : '-'}</td>
              <td className="p-3">{o.delayed ? <span className="text-red-600 font-semibold">Sí</span> : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export const OrdersTable = memo(OrdersTableComponent);
