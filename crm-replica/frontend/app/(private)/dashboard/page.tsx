'use client';

import { useCallback, useEffect, useState } from 'react';
import { DashboardApi } from '@/lib/api/endpoints';
import { KpiCards } from '@/components/dashboard/kpi-cards';
import { useRealtime } from '@/hooks/use-realtime';

export default function DashboardPage() {
  const [data, setData] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try { setData(await DashboardApi.kpis()); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);
  useRealtime(load);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <KpiCards data={data} loading={loading} />
    </div>
  );
}
