# DCM CRM Replica (Backend + Frontend)

## Levantar entorno local (paso a paso)

### 1) Backend
```bash
cd crm-replica/backend
cp .env.example .env
npm install
npm run prisma:generate
npm run prisma:migrate
npm run seed
npm test
npm run dev
```
Backend: `http://localhost:4000`

### 2) Frontend
En otra terminal:
```bash
cd crm-replica/frontend
cp .env.example .env.local
npm install
npm run dev
```
Frontend: `http://localhost:3000`

## Script rápido (si usas dos terminales)
Terminal A:
```bash
cd crm-replica/backend && npm run dev
```
Terminal B:
```bash
cd crm-replica/frontend && npm run dev
```

## Docker Compose (opcional, desarrollo)
```bash
docker compose -f crm-replica/docker-compose.dev.yml up --build
```

Servicios:
- Postgres: `localhost:5432`
- Backend: `localhost:4000`
- Frontend: `localhost:3000`

## Seguridad frontend
- JWT en memoria (no localStorage).
- Guard de rutas privadas en App Router layout.
- Interceptor global para 401/403 con logout automático.
- Validación de formularios con RHF + Zod.

## Realtime
- Eventos suscritos: `orders:changed`, `orders:status_changed`, `dashboard:refresh`.
- Socket singleton para evitar conexiones duplicadas.
