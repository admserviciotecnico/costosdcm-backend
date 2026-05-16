import { Skeleton } from '@/components/common/skeleton';

export function KpiCards({ data, loading }: { data: Record<string, number> | null; loading: boolean }) {
  const keys = [
    ['Pedidos activos', 'total_orders'],
    ['En ejecución', 'in_progress'],
    ['Completados (mes)', 'completed_this_month'],
    ['Demorados', 'delayed'],
    ['Alta prioridad', 'high_priority']
  ] as const;

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
      {keys.map(([label, key]) => (
        <div key={key} className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4">
          <p className="text-sm text-slate-500">{label}</p>
          {loading ? <Skeleton className="h-8 w-12 mt-2" /> : <p className="text-3xl font-bold">{data?.[key] ?? 0}</p>}
        </div>
      ))}
    </div>
  );
}
