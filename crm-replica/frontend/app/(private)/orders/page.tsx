'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ClientsApi, OrdersApi, UsersApi } from '@/lib/api/endpoints';
import { ServiceOrder, User } from '@/types/domain';
import { OrdersTable } from '@/components/orders/orders-table';
import { OrderDetail } from '@/components/orders/order-detail';
import { useRealtime } from '@/hooks/use-realtime';
import { useDebouncedValue } from '@/hooks/use-debounced';
import { Skeleton } from '@/components/common/skeleton';

export default function OrdersPage() {
  const [orders, setOrders] = useState<ServiceOrder[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [clients, setClients] = useState<{ id: string; nombre_empresa: string }[]>([]);
  const [selected, setSelected] = useState<ServiceOrder | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', priority: '', client: '', technician: '', from: '', to: '' });

  const debouncedFilters = useDebouncedValue(filters, 350);

  const setFilter = useCallback((key: keyof typeof filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { page, pageSize: 20 };
      Object.entries(debouncedFilters).forEach(([k, v]) => {
        if (v) params[k] = v;
      });
      const data = await OrdersApi.list(params);
      setOrders(data.items);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  }, [debouncedFilters, page]);

  useEffect(() => {
    load();
    UsersApi.list().then(setUsers).catch(() => setUsers([]));
    ClientsApi.list().then((v) => setClients(v.map((c) => ({ id: c.id, nombre_empresa: c.nombre_empresa }))));
  }, [load]);

  useRealtime(load);

  const pages = useMemo(() => Math.max(1, Math.ceil(total / 20)), [total]);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">Órdenes de Servicio</h1>
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2 rounded-xl p-3 border bg-white dark:bg-slate-900">
        <input className="p-2 rounded border" placeholder="Estado" value={filters.status} onChange={(e) => setFilter('status', e.target.value)} />
        <input className="p-2 rounded border" placeholder="Prioridad" value={filters.priority} onChange={(e) => setFilter('priority', e.target.value)} />
        <select className="p-2 rounded border" value={filters.client} onChange={(e) => setFilter('client', e.target.value)}>
          <option value="">Cliente</option>
          {clients.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre_empresa}
            </option>
          ))}
        </select>
        <select className="p-2 rounded border" value={filters.technician} onChange={(e) => setFilter('technician', e.target.value)}>
          <option value="">Técnico</option>
          {users
            .filter((u) => u.role === 'tecnico')
            .map((u) => (
              <option key={u.id} value={u.id}>
                {u.first_name} {u.last_name}
              </option>
            ))}
        </select>
        <input type="date" className="p-2 rounded border" value={filters.from} onChange={(e) => setFilter('from', e.target.value)} />
        <input type="date" className="p-2 rounded border" value={filters.to} onChange={(e) => setFilter('to', e.target.value)} />
      </div>
      {loading ? <Skeleton className="h-72 w-full" /> : <OrdersTable orders={orders} onClick={setSelected} />}
      <div className="flex gap-2">
        <button className="px-3 py-1 rounded border" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Prev
        </button>
        <span className="px-2">
          {page}/{pages}
        </span>
        <button className="px-3 py-1 rounded border" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </div>
      <OrderDetail order={selected} onClose={() => setSelected(null)} onRefresh={load} />
    </div>
  );
}
