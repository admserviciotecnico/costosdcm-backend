from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from backend_costeo.schemas import (
    ListaPrecioCreate,
    ListaPrecioResponse
)


import os

if os.path.exists("costeo.db"):
    os.remove("costeo.db")

try:
    # Cuando se ejecuta dentro del paquete (Render)
    from backend_costeo.database import engine, SessionLocal
    from backend_costeo.models import (
        Base,
        Producto,
        CostoItem,
        CostoHistorial,
        ListaPrecioConfig,
    )
except ModuleNotFoundError:
    # Cuando se ejecuta localmente
    from database import engine, SessionLocal
    from models import (
        Base,
        Producto,
        CostoItem,
        CostoHistorial,
        ListaPrecioConfig,
    )

# --- Ajuste automático de imports según entorno (Render o local) ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR.parent) not in sys.path:
    sys.path.append(str(BASE_DIR.parent))

app = FastAPI(title="API Costeo DCM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://costosdcm.base44.app",  # dominio de tu app frontend
        "http://localhost:8001",         # para pruebas locales
        "http://127.0.0.1:8001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ListaPrecioCreate(BaseModel):
    producto_codigo: str
    producto_nombre: str
    eventuales: float
    garantia: float
    burden: float
    gp_cliente: float
    gp_integrador: float
    costo_directo: float
    costo_total: float
    precio_cliente: float
    precio_integrador: float


# --- Endpoint raíz para verificar que el backend está activo ---
@app.get("/")
def root():
    return {"message": "Backend de Costeo DCM activo ✅"}

import os
from pathlib import Path

DB_PATH = "/data/costeo.db"

if os.getenv("RESET_DB") == "true":
    if Path(DB_PATH).exists():
        os.remove(DB_PATH)
        print("🗑 Base de datos eliminada automáticamente")

Base.metadata.create_all(bind=engine)

from backend_costeo.seed import seed_if_empty

seed_if_empty()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/productos")
def listar_productos(db: Session = Depends(get_db)):
    return db.query(Producto).all()


@app.get("/api/costos")
def listar_costos(db: Session = Depends(get_db)):
    return db.query(CostoItem).all()


from datetime import datetime

@app.post("/api/costos")
def crear_costo_item(item_data: dict, db: Session = Depends(get_db)):
    try:
        # 🧩 Normalizar campos para que coincidan con el modelo
        mapping = {
            "nombre": "denominacion",
            "costoFabrica": "costo_fabrica",
            "costoFOB": "costo_fob",
            "coef": "coeficiente",
            "unidad_medida": "unidad",
        }
        normalizado = {}
        for k, v in item_data.items():
            normalizado[mapping.get(k, k)] = v

        # 🧠 Crear el objeto
        nuevo_item = CostoItem(**normalizado)
        db.add(nuevo_item)
        db.flush()  # asigna el ID antes de crear historial

        # 🕓 Registrar historial inicial
        db.add(CostoHistorial(
            costo_item_id=nuevo_item.id,
            costo_fabrica=nuevo_item.costo_fabrica,
            costo_fob=nuevo_item.costo_fob,
            coeficiente=nuevo_item.coeficiente,
        ))

        db.commit()
        db.refresh(nuevo_item)
        return {"success": True, "data": nuevo_item.id}

    except Exception as e:
        db.rollback()
        print("💥 Error al crear ítem de costo:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/costos/{item_id}")
def eliminar_costo(item_id: int, db: Session = Depends(get_db)):
    item = db.query(CostoItem).filter(CostoItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    db.delete(item)
    db.commit()
    return {"ok": True}


@app.post("/api/costeos")
def guardar_costeo_alias(data: ListaPrecioCreate, db: Session = Depends(get_db)):
    """
    Alias de compatibilidad:
    Guarda configuraciones de Lista de Precios
    usando el endpoint histórico /api/costeos
    """
    nueva = ListaPrecioConfig(**data.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return {
        "ok": True,
        "mensaje": "Configuración de precios guardada correctamente",
        "id": nueva.id,
    }


@app.get("/api/costos/{item_id}/historial")
def historial_costos(item_id: int, db: Session = Depends(get_db)):
    return (
        db.query(CostoHistorial)
        .filter(CostoHistorial.costo_item_id == item_id)
        .order_by(CostoHistorial.fecha.desc())
        .all()
    )


from sqlalchemy import func

@app.post("/api/lista-precios", response_model=ListaPrecioResponse)
def crear_lista(data: ListaPrecioCreate, db: Session = Depends(get_db)):

    # 🔹 Obtener último código
    ultima = db.query(ListaPrecioConfig).order_by(
        ListaPrecioConfig.codigo.desc()
    ).first()

    if ultima:
        ultimo_num = int(ultima.codigo.replace("DCM", ""))
        nuevo_codigo = f"DCM{ultimo_num + 1:03d}"
    else:
        nuevo_codigo = "DCM001"

    nueva = ListaPrecioConfig(
        codigo=nuevo_codigo,
        **data.model_dump()
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return nueva



@app.get("/api/lista-precios/producto/{codigo}")
def listar_por_producto(codigo: str, db: Session = Depends(get_db)):
    return (
        db.query(ListaPrecioConfig)
        .filter(ListaPrecioConfig.producto_codigo == codigo)
        .order_by(ListaPrecioConfig.creada_en.desc())
        .all()
    )

@app.get("/api/lista-precios", response_model=list[ListaPrecioResponse])
def listar_listas(db: Session = Depends(get_db)):
    return db.query(ListaPrecioConfig).all()


@app.delete("/api/lista-precios/{lista_id}")
def eliminar_lista_precios(lista_id: int, db: Session = Depends(get_db)):
    lista = db.query(ListaPrecioConfig).filter(ListaPrecioConfig.id == lista_id).first()

    if not lista:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")

    db.delete(lista)
    db.commit()
    return {"ok": True}

class CostoUpdate(BaseModel):
    costo_fabrica: Optional[float] = None
    costo_fob: Optional[float] = None
    coeficiente: Optional[float] = None

@app.put("/api/costos/{item_id}")
def actualizar_costo_item(item_id: int, datos: dict, db: Session = Depends(get_db)):

    item = db.query(CostoItem).filter(CostoItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    # --- 1️⃣ Guardar historial solo si se modifican valores de costo ---
    campos_costo = {"costo_fabrica", "costo_fob", "coeficiente"}
    modificar_historial = any(campo in datos for campo in campos_costo)

    if modificar_historial:
        historial = CostoHistorial(
            costo_item_id=item.id,
            costo_fabrica=item.costo_fabrica,
            costo_fob=item.costo_fob,
            coeficiente=item.coeficiente,
        )
        db.add(historial)

    # --- 2️⃣ Actualizar campos del modelo ---
    for campo, valor in datos.items():
        if hasattr(item, campo):
            setattr(item, campo, valor)

    # --- 3️⃣ Guardar cambios ---
    db.commit()
    db.refresh(item)

    mensaje = "Ítem actualizado correctamente"
    if modificar_historial:
        mensaje += " y guardado en historial"

    return {"ok": True, "mensaje": mensaje, "item": item.id}


@app.post("/api/productos")
def crear_producto(producto: dict, db: Session = Depends(get_db)):
    nuevo = Producto(**producto)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo



@app.put("/api/productos/{producto_id}")
def actualizar_producto(
    producto_id: int,
    datos: dict,
    db: Session = Depends(get_db)
):
    prod = db.query(Producto).filter(Producto.id == producto_id).first()

    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for campo, valor in datos.items():
        if hasattr(prod, campo):
            setattr(prod, campo, valor)

    db.commit()
    db.refresh(prod)
    return prod

@app.delete("/api/productos/{producto_id}")
def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db)
):
    prod = db.query(Producto).filter(Producto.id == producto_id).first()

    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(prod)
    db.commit()
    return {"ok": True, "mensaje": "Producto eliminado correctamente"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)

