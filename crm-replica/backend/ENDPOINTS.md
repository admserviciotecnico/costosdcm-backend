# API Endpoints + ejemplos (backend robusto)

## Seguridad
- JWT Bearer obligatorio en endpoints protegidos.
- Rate limiting en `POST /api/auth/register` y `POST /api/auth/login`.
- Sanitización global de payloads.
- Validación estricta con Zod en todos los endpoints de escritura.

## Soft delete
- `Client`, `Equipment`, `ServiceOrder` usan `deleted_at`.
- Las consultas list/KPI excluyen registros con `deleted_at != null`.

## Auth
### POST `/api/auth/register`
```json
{ "first_name": "Admin", "last_name": "DCM", "email": "admin2@dcm.local", "password": "ChangeMe123!", "role": "admin" }
```

### POST `/api/auth/login`
```json
{ "email": "admin@dcm.local", "password": "ChangeMe123!" }
```

## Clients
### DELETE `/api/clients/:id`
- Bloquea borrado si el cliente tiene órdenes activas.
Response 400:
```json
{ "message": "Cannot delete client with active orders" }
```

## Service Orders
### GET `/api/orders`
- Paginación obligatoria por default (`page=1&pageSize=20`).
- `pageSize` máximo: `100`.
- Filtros: `status`, `technician`, `client`, `priority`, `from`, `to`.

### PATCH `/api/orders/:id`
- Técnico solo si está asignado.
- Técnico no puede modificar `fecha_programada`, `client_id`, `prioridad`, `prioridad_peso`.
- Validación estricta del flujo de estados.

### PUT `/api/orders/:id/technicians`
- Reasignación múltiple (admin).
- Registra auditoría en historial con campo `technicians` y valores anterior/nuevo.

## Auditoría (`ServiceOrderStatusHistory`)
Se registra para:
- cambio de estado,
- cambio de prioridad,
- cambio de fecha_programada,
- cambio de técnicos.
Campos: `campo_modificado`, `valor_anterior`, `valor_nuevo`, `comentario`.
