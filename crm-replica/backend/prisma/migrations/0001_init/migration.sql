CREATE TYPE "UserRole" AS ENUM ('admin', 'tecnico');
CREATE TYPE "OrderStatus" AS ENUM ('presupuesto_generado','oc_recibida','facturado','pago_recibido','documentacion_enviada','documentacion_aprobada','service_programado','en_ejecucion','completado','cancelado');
CREATE TYPE "Priority" AS ENUM ('baja', 'media', 'alta');
CREATE TYPE "EquipmentStatus" AS ENUM ('operativo','mantenimiento','fuera_servicio','en_revision');

CREATE TABLE "Role" (
  "id" TEXT PRIMARY KEY,
  "name" "UserRole" NOT NULL UNIQUE
);

CREATE TABLE "User" (
  "id" TEXT PRIMARY KEY,
  "first_name" TEXT NOT NULL,
  "last_name" TEXT NOT NULL,
  "email" TEXT NOT NULL UNIQUE,
  "password" TEXT NOT NULL,
  "phone" TEXT,
  "active" BOOLEAN NOT NULL DEFAULT TRUE,
  "role_id" TEXT NOT NULL REFERENCES "Role"("id"),
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "Client" (
  "id" TEXT PRIMARY KEY,
  "nombre_empresa" TEXT NOT NULL,
  "direccion" TEXT,
  "telefono" TEXT,
  "email" TEXT NOT NULL,
  "persona_contacto" TEXT,
  "fecha_vencimiento_documentacion" TIMESTAMP,
  "observaciones" TEXT,
  "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
  "deleted_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "Equipment" (
  "id" TEXT PRIMARY KEY,
  "client_id" TEXT NOT NULL REFERENCES "Client"("id"),
  "tipo_equipo" TEXT NOT NULL,
  "modelo" TEXT,
  "numero_serie" TEXT NOT NULL UNIQUE,
  "ubicacion_planta" TEXT,
  "estado_actual" "EquipmentStatus" NOT NULL DEFAULT 'operativo',
  "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
  "deleted_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "ServiceOrder" (
  "id" TEXT PRIMARY KEY,
  "client_id" TEXT NOT NULL REFERENCES "Client"("id"),
  "estado" "OrderStatus" NOT NULL DEFAULT 'presupuesto_generado',
  "prioridad" "Priority" NOT NULL DEFAULT 'media',
  "prioridad_peso" INTEGER NOT NULL DEFAULT 2,
  "fecha_programada" TIMESTAMP,
  "direccion_service" TEXT,
  "contacto_planta" TEXT,
  "telefono_contacto_planta" TEXT,
  "observaciones" TEXT,
  "observaciones_cierre" TEXT,
  "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
  "deleted_at" TIMESTAMP,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "ServiceOrderTechnician" (
  "id" TEXT PRIMARY KEY,
  "service_order_id" TEXT NOT NULL REFERENCES "ServiceOrder"("id") ON DELETE CASCADE,
  "technician_id" TEXT NOT NULL REFERENCES "User"("id") ON DELETE CASCADE,
  "fecha_asignacion" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "asignado_por" TEXT,
  UNIQUE("service_order_id", "technician_id")
);

CREATE TABLE "ServiceOrderStatusHistory" (
  "id" TEXT PRIMARY KEY,
  "service_order_id" TEXT NOT NULL REFERENCES "ServiceOrder"("id") ON DELETE CASCADE,
  "estado_anterior" "OrderStatus",
  "estado_nuevo" "OrderStatus" NOT NULL,
  "campo_modificado" TEXT,
  "valor_anterior" TEXT,
  "valor_nuevo" TEXT,
  "comentario" TEXT,
  "usuario_id" TEXT NOT NULL REFERENCES "User"("id"),
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "Notification" (
  "id" TEXT PRIMARY KEY,
  "user_id" TEXT NOT NULL REFERENCES "User"("id") ON DELETE CASCADE,
  "service_order_id" TEXT REFERENCES "ServiceOrder"("id") ON DELETE SET NULL,
  "title" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "read" BOOLEAN NOT NULL DEFAULT FALSE,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "Attachment" (
  "id" TEXT PRIMARY KEY,
  "service_order_id" TEXT NOT NULL REFERENCES "ServiceOrder"("id") ON DELETE CASCADE,
  "file_name" TEXT NOT NULL,
  "file_url" TEXT NOT NULL,
  "mime_type" TEXT,
  "uploaded_by" TEXT NOT NULL,
  "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX "Client_is_active_deleted_at_idx" ON "Client"("is_active","deleted_at");
CREATE INDEX "Equipment_client_id_idx" ON "Equipment"("client_id");
CREATE INDEX "Equipment_is_active_deleted_at_idx" ON "Equipment"("is_active","deleted_at");
CREATE INDEX "ServiceOrder_fecha_programada_idx" ON "ServiceOrder"("fecha_programada");
CREATE INDEX "ServiceOrder_estado_idx" ON "ServiceOrder"("estado");
CREATE INDEX "ServiceOrder_client_id_idx" ON "ServiceOrder"("client_id");
CREATE INDEX "ServiceOrder_active_filter_idx" ON "ServiceOrder"("is_active","deleted_at","estado","prioridad","fecha_programada");
CREATE INDEX "ServiceOrderTechnician_service_order_id_idx" ON "ServiceOrderTechnician"("service_order_id");
CREATE INDEX "ServiceOrderTechnician_technician_id_idx" ON "ServiceOrderTechnician"("technician_id");
CREATE INDEX "ServiceOrderStatusHistory_service_order_id_created_at_idx" ON "ServiceOrderStatusHistory"("service_order_id", "created_at");
CREATE INDEX "ServiceOrderStatusHistory_campo_modificado_idx" ON "ServiceOrderStatusHistory"("campo_modificado");
CREATE INDEX "Attachment_service_order_id_idx" ON "Attachment"("service_order_id");
