import test from 'node:test';
import assert from 'node:assert/strict';
import { loginUser, registerUser } from '../src/services/auth-service.js';
import { assignTechnicians, canTechnicianAccessOrder, createOrder, updateOrder } from '../src/services/order-service.js';

function fixture() {
  return {
    users: [],
    orders: [],
    assignments: []
  };
}

test('registro y login', () => {
  const db = fixture();
  const created = registerUser({ users: db.users, first_name: 'Admin', last_name: 'One', email: 'admin@test.com', password: 'Pass1234!', role: 'admin' });
  assert.ok(created.id);

  const login = loginUser({ users: db.users, email: 'admin@test.com', password: 'Pass1234!' });
  assert.equal(login.token_type, 'bearer');
  assert.ok(login.access_token.startsWith('test-token-'));
});

test('creación de orden por admin', () => {
  const db = fixture();
  const order = createOrder({
    orders: db.orders,
    actorRole: 'admin',
    data: { client_id: 'c1', prioridad: 'alta', estado: 'presupuesto_generado' }
  });
  assert.equal(order.prioridad_peso, 3);
  assert.equal(db.orders.length, 1);
});

test('asignación múltiple de técnicos', () => {
  const db = fixture();
  const order = createOrder({ orders: db.orders, actorRole: 'admin', data: { client_id: 'c1' } });
  const assigned = assignTechnicians({ assignments: db.assignments, orderId: order.id, technicianIds: ['t1', 't2'] });
  assert.equal(assigned.length, 2);
});

test('cambio de estado válido para técnico', () => {
  const order = { estado: 'service_programado', prioridad: 'media', prioridad_peso: 2 };
  const result = updateOrder({ order, role: 'tecnico', patch: { estado: 'en_ejecucion' } });
  assert.equal(result.stateChanged, true);
  assert.equal(order.estado, 'en_ejecucion');
});

test('cambio de estado inválido para técnico', () => {
  const order = { estado: 'service_programado', prioridad: 'media', prioridad_peso: 2 };
  assert.throws(() => updateOrder({ order, role: 'tecnico', patch: { estado: 'completado' } }));
});

test('técnico no asignado no puede acceder a orden', () => {
  const db = fixture();
  const order = createOrder({ orders: db.orders, actorRole: 'admin', data: { client_id: 'c1' } });
  assignTechnicians({ assignments: db.assignments, orderId: order.id, technicianIds: ['t1'] });

  assert.equal(canTechnicianAccessOrder({ assignments: db.assignments, orderId: order.id, technicianId: 't2' }), false);
});

test('técnico no puede modificar fecha_programada', () => {
  const order = { estado: 'service_programado', prioridad: 'media', prioridad_peso: 2, fecha_programada: '2026-01-01' };
  assert.throws(() => updateOrder({ order, role: 'tecnico', patch: { fecha_programada: '2026-02-01' } }));
});
