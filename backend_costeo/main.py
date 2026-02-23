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
import httpx
from backend_costeo.auth import get_rol_usuario, solo_admin, admin_o_vendedor

try:
    # Cuando se ejecuta dentro del paquete (Render)
    from backend_costeo.database import engine, SessionLocal
    from backend_costeo.models import (
    Base,
    Producto,
    CostoItem,
    CostoHistorial,
    ListaPrecioConfig,
    ListaPrecioItem,  # 🔥 AGREGAR ESTO
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
        ListaPrecioItem,  # 🔥 AGREGAR AQUÍ TAMBIÉN
    )


# --- Ajuste automático de imports según entorno (Render o local) ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR.parent) not in sys.path:
    sys.path.append(str(BASE_DIR.parent))

app = FastAPI(title="API Costeo DCM")

origins = [
    "https://costosdcm.base44.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8001",         # para pruebas locales
    "http://127.0.0.1:8001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoint raíz para verificar que el backend está activo ---
@app.get("/")
def root():
    return {"message": "Backend de Costeo DCM activo ✅"}

import os
from pathlib import Path

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
def listar_productos(db: Session = Depends(get_db), usuario: dict = Depends(admin_o_vendedor)):
    return db.query(Producto).all()


@app.get("/api/costos")
def listar_costos(db: Session = Depends(get_db), usuario: dict = Depends(admin_o_vendedor)):
    return db.query(CostoItem).all()


from datetime import datetime

@app.post("/api/costos")
def crear_costo_item(item_data: dict, db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):
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
def eliminar_costo(item_id: int, db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):
    item = db.query(CostoItem).filter(CostoItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    db.delete(item)
    db.commit()
    return {"ok": True}


@app.post("/api/costeos")
def guardar_costeo_alias(data: ListaPrecioCreate, db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):
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
def historial_costos(item_id: int, db: Session = Depends(get_db), usuario: dict = Depends(admin_o_vendedor)):
    return (
        db.query(CostoHistorial)
        .filter(CostoHistorial.costo_item_id == item_id)
        .order_by(CostoHistorial.fecha.desc())
        .all()
    )


from sqlalchemy import func

@app.post("/api/lista-precios", response_model=ListaPrecioResponse)
def crear_lista(data: ListaPrecioCreate, db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):

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
    nombre=data.nombre,
    producto_codigo=data.producto_codigo,
    producto_nombre=data.producto_nombre,
    eventuales=data.eventuales,
    garantia=data.garantia,
    burden=data.burden,
    gp_cliente=data.gp_cliente,
    gp_integrador=data.gp_integrador,
    costo_directo=data.costo_directo,
    costo_total=data.costo_total,
    precio_cliente=data.precio_cliente,
    precio_integrador=data.precio_integrador,
    )

    # 🔥 Guardar items si vienen
    if data.items:
        for item in data.items:

            nuevo_item = ListaPrecioItem(
                lista_codigo=nuevo_codigo,
                item_id=item.get("item_id"),
                cantidad=item.get("cantidad"),
            )

            db.add(nuevo_item)

    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return nueva



@app.get("/api/lista-precios/{codigo}", response_model=ListaPrecioResponse)
def obtener_lista(codigo: str, db: Session = Depends(get_db), usuario: dict = Depends(admin_o_vendedor)):
    lista = db.query(ListaPrecioConfig).filter(
        ListaPrecioConfig.codigo == codigo
    ).first()

    if not lista:
        raise HTTPException(status_code=404, detail="Lista no encontrada")

    items_response = []
    for lp_item in lista.items:
        costo_item = lp_item.item
        if costo_item:
            costo_unit = costo_item.costo_fabrica or 0
            items_response.append({
                "item_id": lp_item.item_id,
                "codigo": costo_item.codigo,
                "nombre": costo_item.nombre,
                "tipo": costo_item.tipo,
                "subtipo": costo_item.subtipo,
                "unidad": costo_item.unidad,
                "cantidad": lp_item.cantidad,
                "costo_unit": costo_unit,
                "total": round(costo_unit * (lp_item.cantidad or 0), 4),
            })

    return {
        **{col.name: getattr(lista, col.name) for col in lista.__table__.columns},
        "items": items_response,
    }


from sqlalchemy.orm import joinedload

@app.get("/api/lista-precios", response_model=list[ListaPrecioResponse])
def listar_listas(db: Session = Depends(get_db), usuario: dict = Depends(admin_o_vendedor)):

    listas = (
        db.query(ListaPrecioConfig)
        .options(
            joinedload(ListaPrecioConfig.items)
            .joinedload(ListaPrecioItem.item)
        )
        .all()
    )

    resultado = []
    for lista in listas:
        items_response = []
        for lp_item in lista.items:
            costo_item = lp_item.item
            if costo_item:
                costo_unit = costo_item.costo_fabrica or 0
                items_response.append({
                    "item_id": lp_item.item_id,
                    "codigo": costo_item.codigo,
                    "nombre": costo_item.nombre,
                    "tipo": costo_item.tipo,
                    "subtipo": costo_item.subtipo,
                    "unidad": costo_item.unidad,
                    "costo_unit": costo_unit,
                    "cantidad": lp_item.cantidad,
                    "total": costo_unit * (lp_item.cantidad or 0),
                })

        lista_dict = {col.name: getattr(lista, col.name) for col in lista.__table__.columns}
        lista_dict["items"] = items_response
        resultado.append(lista_dict)

    return resultado



@app.delete("/api/lista-precios/{lista_id}")
def eliminar_lista_precios(lista_id: int, db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):
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
def actualizar_costo_item(item_id: int, datos: dict, db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):

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

@app.put("/api/lista-precios/{lista_codigo}")
def actualizar_lista(lista_codigo: str, data: dict, db: Session = Depends(get_db), usuario: dict = Depends(admin_o_vendedor)):

    lista = db.query(ListaPrecioConfig).filter(
        ListaPrecioConfig.codigo == lista_codigo
    ).first()

    if not lista:
        raise HTTPException(status_code=404, detail="Lista no encontrada")

    campos_config = {
        "nombre", "producto_codigo", "producto_nombre",
        "eventuales", "garantia", "burden",
        "gp_cliente", "gp_integrador",
        "costo_directo", "costo_total",
        "precio_cliente", "precio_integrador"
    }
    for campo in campos_config:
        if campo in data and data[campo] is not None:  # ← nunca sobreescribir con None
            setattr(lista, campo, data[campo])

    if "items" in data:
        db.query(ListaPrecioItem).filter(
            ListaPrecioItem.lista_codigo == lista_codigo
        ).delete()

        for item in data["items"]:
            db.add(ListaPrecioItem(
                lista_codigo=lista_codigo,
                item_id=item.get("item_id"),
                cantidad=item.get("cantidad"),
            ))

    db.commit()
    db.refresh(lista)
    return {"ok": True, "mensaje": "Configuración actualizada correctamente"}

@app.post("/api/productos")
def crear_producto(producto: dict, db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):
    nuevo = Producto(**producto)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo



@app.put("/api/productos/{producto_id}")
def actualizar_producto(
    producto_id: int,
    datos: dict,
    db: Session = Depends(get_db), 
    usuario: dict = Depends(solo_admin)
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
    db: Session = Depends(get_db), 
    usuario: dict = Depends(solo_admin)
):
    prod = db.query(Producto).filter(Producto.id == producto_id).first()

    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(prod)
    db.commit()
    return {"ok": True, "mensaje": "Producto eliminado correctamente"}

@app.post("/api/auth/registro")
async def registro(datos: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('SUPABASE_URL')}/auth/v1/signup",
            headers={
                "apikey": os.getenv("SUPABASE_KEY"),
                "Content-Type": "application/json"
            },
            json={
                "email": datos.get("email"),
                "password": datos.get("password"),
                "data": {
                    "nombre": datos.get("nombre"),
                    "apellido": datos.get("apellido")
                }
            }
        )
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail="Error al registrar usuario")
    return {"ok": True, "mensaje": "Usuario registrado correctamente."}


@app.post("/api/auth/login")
async def login(datos: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('SUPABASE_URL')}/auth/v1/token?grant_type=password",
            headers={
                "apikey": os.getenv("SUPABASE_KEY"),
                "Content-Type": "application/json"
            },
            json={
                "email": datos.get("email"),
                "password": datos.get("password")
            }
        )
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    data = response.json()
    return {
        "access_token": data.get("access_token"),
        "token_type": "bearer"
    }


@app.get("/api/auth/me")
async def me(usuario: dict = Depends(get_rol_usuario)):
    return usuario


@app.get("/api/usuarios")
async def listar_usuarios(usuario: dict = Depends(solo_admin)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{os.getenv('SUPABASE_URL')}/rest/v1/usuarios?select=*&order=creado_en.desc",
            headers={
                "apikey": os.getenv("SUPABASE_KEY"),
                "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}"
            }
        )
    return response.json()


@app.put("/api/usuarios/{user_id}/rol")
async def cambiar_rol(user_id: str, datos: dict, usuario: dict = Depends(solo_admin)):
    nuevo_rol = datos.get("rol")
    if nuevo_rol not in ("admin", "vendedor"):
        raise HTTPException(status_code=400, detail="Rol inválido")
    async with httpx.AsyncClient() as client:
        await client.patch(
            f"{os.getenv('SUPABASE_URL')}/rest/v1/usuarios?id=eq.{user_id}",
            headers={
                "apikey": os.getenv("SUPABASE_KEY"),
                "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            json={"rol": nuevo_rol}
        )
    return {"ok": True, "mensaje": f"Rol actualizado a {nuevo_rol}"}

@app.post("/api/auth/cambiar-password")
async def cambiar_password(datos: dict, usuario: dict = Depends(get_rol_usuario)):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{os.getenv('SUPABASE_URL')}/auth/v1/user",
            headers={
                "apikey": os.getenv("SUPABASE_KEY"),
                "Authorization": f"Bearer {datos.get('access_token')}",
                "Content-Type": "application/json"
            },
            json={"password": datos.get("nueva_password")}
        )
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Error al cambiar contraseña")
    return {"ok": True, "mensaje": "Contraseña actualizada correctamente"}

@app.get("/api/parametros/coeficiente-blue")
def obtener_coeficiente_blue(
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    from sqlalchemy import text
    result = db.execute(
        text("SELECT valor FROM parametros WHERE clave = 'coeficiente_blue'")
    ).fetchone()
    return {"coeficiente_blue": result[0] if result else 0}


@app.put("/api/parametros/coeficiente-blue")
def actualizar_coeficiente_blue(
    datos: dict,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_admin)
):
    from sqlalchemy import text

    porcentaje_blue = datos.get("coeficiente_blue")
    if porcentaje_blue is None or porcentaje_blue < 0:
        raise HTTPException(status_code=400, detail="Valor inválido")

    # 1️⃣ Guardar el nuevo coeficiente_blue en la tabla parametros
    db.execute(text("""
        UPDATE parametros SET valor = :valor, actualizado_en = NOW()
        WHERE clave = 'coeficiente_blue'
    """), {"valor": porcentaje_blue})

    # 2️⃣ Recalcular costo_fabrica de ítems importados
    # costo_fabrica = costo_fob × coeficiente_original × (1 + coeficiente_blue/100)
    items_afectados = db.query(CostoItem).filter(
        CostoItem.tipo == "Electronica",
        CostoItem.coeficiente > 1
    ).all()

    for item in items_afectados:
        if item.costo_fob:
            nuevo_costo = round(
                item.costo_fob * item.coeficiente * (1 + porcentaje_blue / 100), 4
            )
            # Guardar historial antes de modificar
            db.add(CostoHistorial(
                costo_item_id=item.id,
                costo_fabrica=item.costo_fabrica,
                costo_fob=item.costo_fob,
                coeficiente=item.coeficiente,
            ))
            item.costo_fabrica = nuevo_costo

    db.flush()

    # 3️⃣ Recalcular todas las listas de precios
    listas = db.query(ListaPrecioConfig).options(
        joinedload(ListaPrecioConfig.items).joinedload(ListaPrecioItem.item)
    ).all()

    for lista in listas:
        costo_directo = sum(
            (lp_item.item.costo_fabrica or 0) * (lp_item.cantidad or 0)
            for lp_item in lista.items
            if lp_item.item
        )
        eventuales = (lista.eventuales or 0) / 100
        garantia = (lista.garantia or 0) / 100
        burden = (lista.burden or 0) / 100
        gp_cliente = (lista.gp_cliente or 0) / 100
        gp_integrador = (lista.gp_integrador or 0) / 100

        costo_total = costo_directo * (1 + eventuales) * (1 + garantia) * (1 + burden)
        precio_cliente = costo_total / (1 - gp_cliente) if gp_cliente < 1 else 0
        precio_integrador = costo_total / (1 - gp_integrador) if gp_integrador < 1 else 0

        lista.costo_directo = round(costo_directo, 4)
        lista.costo_total = round(costo_total, 4)
        lista.precio_cliente = round(precio_cliente, 4)
        lista.precio_integrador = round(precio_integrador, 4)

    db.commit()

    return {
        "ok": True,
        "mensaje": f"Coeficiente blue actualizado a {porcentaje_blue}%",
        "items_actualizados": len(items_afectados),
        "listas_recalculadas": len(listas)
    }

@app.post("/api/admin/reload-costos")
def reload_costos(db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):
    from backend_costeo.seed import seed_costos_only
    seed_costos_only(db)
    return {"ok": True, "mensaje": "Ítems de costo recargados desde JSON"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)

