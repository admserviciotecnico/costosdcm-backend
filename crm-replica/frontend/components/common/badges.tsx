import { OrderStatus, Priority } from '@/types/domain';

export function StatusBadge({ value }: { value: OrderStatus }) {
  return <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">{value.replace(/_/g, ' ')}</span>;
}

export function PriorityBadge({ value }: { value: Priority }) {
  const color = value === 'alta' ? 'bg-red-100 text-red-800' : value === 'media' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800';
  return <span className={`px-2 py-1 text-xs rounded ${color}`}>{value}</span>;
}
