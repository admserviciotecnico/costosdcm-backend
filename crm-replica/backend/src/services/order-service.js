import crypto from 'crypto';
import {
  computePriorityWeight,
  validateStateTransition,
  validateTechnicianRestrictedFields,
  isStructuralChange
} from './order-rules.js';

export function createOrder({ orders, data, actorRole }) {
  if (actorRole !== 'admin') throw new Error('FORBIDDEN');
  const order = {
    id: crypto.randomUUID(),
    estado: data.estado || 'presupuesto_generado',
    prioridad: data.prioridad || 'media',
    prioridad_peso: computePriorityWeight(data.prioridad || 'media'),
    client_id: data.client_id,
    fecha_programada: data.fecha_programada || null,
    is_active: true
  };
  orders.push(order);
  return order;
}

export function assignTechnicians({ assignments, orderId, technicianIds }) {
  technicianIds.forEach((techId) => {
    if (!assignments.some((a) => a.service_order_id === orderId && a.technician_id === techId)) {
      assignments.push({ id: crypto.randomUUID(), service_order_id: orderId, technician_id: techId });
    }
  });
  return assignments.filter((a) => a.service_order_id === orderId);
}

export function canTechnicianAccessOrder({ assignments, orderId, technicianId }) {
  return assignments.some((a) => a.service_order_id === orderId && a.technician_id === technicianId);
}

export function updateOrder({ order, patch, role }) {
  if (role === 'tecnico') {
    const restricted = validateTechnicianRestrictedFields(patch);
    if (!restricted.ok) throw new Error(restricted.reason);
  }

  const transition = validateStateTransition({ role, currentState: order.estado, nextState: patch.estado });
  if (!transition.ok) throw new Error(transition.reason);

  const prev = { ...order };
  Object.assign(order, patch);
  if (patch.prioridad) order.prioridad_peso = computePriorityWeight(patch.prioridad);

  return {
    order,
    stateChanged: !!patch.estado && patch.estado !== prev.estado,
    structuralChanged: isStructuralChange(prev, patch)
  };
}
