import { Inbox } from 'lucide-react';

export function EmptyState({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-10 text-center">
      <Inbox className="mx-auto h-8 w-8 text-slate-400" />
      <p className="mt-3 font-semibold">{title}</p>
      <p className="text-sm text-slate-500">{subtitle}</p>
    </div>
  );
}
