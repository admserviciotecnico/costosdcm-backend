from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

# --- Ajuste automático de imports según entorno (Render o local) ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR.parent) not in sys.path:
    sys.path.append(str(BASE_DIR.parent))

try:
    # Cuando se ejecuta dentro del paquete (Render)
    from backend_costeo.database import engine, SessionLocal
    from backend_costeo.models import Base, Producto, CostoItem, CostoHistorial
except ModuleNotFoundError:
    # Cuando se ejecuta localmente (PyInstaller)
    from database import engine, SessionLocal
    from models import Base, Producto, CostoItem, CostoHistorial


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


# --- Endpoint raíz para verificar que el backend está activo ---
@app.get("/")
def root():
    return {"message": "Backend de Costeo DCM activo ✅"}

Base.metadata.create_all(bind=engine)


@app.get("/api/productos")
def listar_productos():
    db = SessionLocal()
    productos = db.query(Producto).all()
    db.close()
    return productos

@app.get("/api/costos")
def listar_costos():
    db = SessionLocal()
    items = db.query(CostoItem).all()
    db.close()
    return items

from datetime import datetime

@app.post("/api/costos")
def crear_costo(item: dict):
    db = SessionLocal()
    nuevo = CostoItem(**item)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    db.close()
    return nuevo


@app.delete("/api/costos/{item_id}")
def eliminar_costo(item_id: int):
    db = SessionLocal()
    item = db.query(CostoItem).filter(CostoItem.id == item_id).first()
    if not item:
        db.close()
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    db.delete(item)
    db.commit()
    db.close()
    return {"ok": True, "mensaje": "Ítem eliminado correctamente"}

costeos_guardados = []

@app.post("/api/costeos")
def guardar_costeo(costeo: dict):
    costeo["fecha"] = datetime.now().isoformat()
    costeos_guardados.append(costeo)
    return {
        "ok": True,
        "mensaje": "Costeo guardado correctamente",
        "id": len(costeos_guardados) - 1
    }

@app.get("/api/costos/{item_id}/historial")
def historial_costos(item_id: int):
    db = SessionLocal()
    hist = db.query(CostoHistorial)\
        .filter(CostoHistorial.costo_item_id == item_id)\
        .order_by(CostoHistorial.fecha.desc())\
        .all()
    db.close()
    return hist


class CostoUpdate(BaseModel):
    costo_fabrica: Optional[float] = None
    costo_fob: Optional[float] = None
    coeficiente: Optional[float] = None


@app.put("/api/costos/{item_id}")
def actualizar_costo_item(item_id: int, datos: dict):
    db = SessionLocal()
    item = db.query(CostoItem).filter(CostoItem.id == item_id).first()

    if not item:
        db.close()
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
    db.close()

    mensaje = "Ítem actualizado correctamente"
    if modificar_historial:
        mensaje += " y guardado en historial"

    return {"ok": True, "mensaje": mensaje, "item": item.id}


@app.post("/api/productos")
def crear_producto(producto: dict):
    db = SessionLocal()
    nuevo = Producto(**producto)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    db.close()
    return nuevo


@app.put("/api/productos/{producto_id}")
def actualizar_producto(producto_id: int, datos: dict):
    db = SessionLocal()
    prod = db.query(Producto).filter(Producto.id == producto_id).first()
    if not prod:
        db.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for campo, valor in datos.items():
        setattr(prod, campo, valor)

    db.commit()
    db.refresh(prod)
    db.close()
    return prod


@app.delete("/api/productos/{producto_id}")
def eliminar_producto(producto_id: int):
    db = SessionLocal()
    prod = db.query(Producto).filter(Producto.id == producto_id).first()
    if not prod:
        db.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(prod)
    db.commit()
    db.close()
    return {"ok": True, "mensaje": "Producto eliminado correctamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)

