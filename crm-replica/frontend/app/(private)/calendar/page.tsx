'use client';

import { useEffect, useMemo, useState } from 'react';
import { OrdersApi } from '@/lib/api/endpoints';
import { eachDayOfInterval, endOfMonth, format, startOfMonth } from 'date-fns';
import { ServiceOrder } from '@/types/domain';
import { EmptyState } from '@/components/common/empty-state';

export default function CalendarPage() {
  const [date] = useState(new Date());
  const [orders, setOrders] = useState<ServiceOrder[]>([]);

  useEffect(() => {
    OrdersApi.list({ page: 1, pageSize: 100 }).then((d) => setOrders(d.items));
  }, [date]);

  const days = useMemo(() => eachDayOfInterval({ start: startOfMonth(date), end: endOfMonth(date) }), [date]);

  if (!orders.length) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold">Calendario</h1>
        <EmptyState title="Sin eventos programados" subtitle="Cuando asignes fecha_programada a órdenes, aparecerán aquí." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">Calendario</h1>
      <div className="grid grid-cols-7 gap-2">
        {days.map((d) => {
          const count = orders.filter((o) => o.fecha_programada && new Date(o.fecha_programada).toDateString() === d.toDateString()).length;
          return (
            <div key={d.toISOString()} className="rounded border bg-white dark:bg-slate-900 p-2 min-h-24">
              <p className="font-semibold">{format(d, 'd')}</p>
              <p className="text-xs">{count} servicios</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
