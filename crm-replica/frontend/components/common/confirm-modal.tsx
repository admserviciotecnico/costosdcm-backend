'use client';

export function ConfirmModal({ open, title, message, onCancel, onConfirm }: { open: boolean; title: string; message: string; onCancel: () => void; onConfirm: () => void }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[210] bg-black/50 grid place-items-center p-4">
      <div className="w-full max-w-md rounded-xl bg-white dark:bg-slate-900 border p-5 space-y-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-sm text-slate-500">{message}</p>
        <div className="flex justify-end gap-2">
          <button className="px-3 py-2 rounded border" onClick={onCancel}>Cancelar</button>
          <button className="px-3 py-2 rounded bg-red-600 text-white" onClick={onConfirm}>Confirmar</button>
        </div>
      </div>
    </div>
  );
}
