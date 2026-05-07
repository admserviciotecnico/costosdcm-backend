from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
from backend_costeo.historial import HistorialCambio, registrar_cambio
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from backend_costeo.schemas import (
    ListaPrecioCreate,
    ListaPrecioResponse,
    CatalogoProductoCreate,
    CatalogoProductoResponse,
    CotizacionCreate,
    CotizacionResponse,
)
import httpx
from backend_costeo.auth import get_rol_usuario, solo_admin, admin_o_vendedor
 
try:
    from backend_costeo.database import engine, SessionLocal
    from backend_costeo.models import (
        Base,
        Producto,
        CostoItem,
        CostoHistorial,
        ListaPrecioConfig,
        ListaPrecioItem,
        CatalogoProducto,
        CatalogoConjunto,
        CatalogoItem,
        Cotizacion,
        CotizacionConjunto,
        CotizacionItem,
    )
 
except ModuleNotFoundError:
    from database import engine, SessionLocal
    from models import (
        Base,
        Producto,
        CostoItem,
        CostoHistorial,
        ListaPrecioConfig,
        ListaPrecioItem,
        CatalogoProducto,
        CatalogoConjunto,
        CatalogoItem,
        Cotizacion,
        CotizacionConjunto,
        CotizacionItem,
    )
 
 
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
    "http://localhost:8001",
    "http://127.0.0.1:8001"
]
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
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
        mapping = {
            "denominacion": "nombre",
            "costoFabrica": "costo_fabrica",
            "costoFOB": "costo_fob",
            "coef": "coeficiente",
            "unidad_medida": "unidad",
        }
        normalizado = {}
        for k, v in item_data.items():
            normalizado[mapping.get(k, k)] = v
 
        nuevo_item = CostoItem(**normalizado)
        db.add(nuevo_item)
        db.flush()
 
        db.add(CostoHistorial(
            costo_item_id=nuevo_item.id,
            costo_fabrica=nuevo_item.costo_fabrica,
            costo_fob=nuevo_item.costo_fob,
            coeficiente=nuevo_item.coeficiente,
        ))
 
        registrar_cambio(db, usuario, "crear", "costo_item", nuevo_item.id, nuevo_item.nombre)
 
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
 
    registrar_cambio(db, usuario, "eliminar", "costo_item", item.id, item.nombre)
 
    db.delete(item)
    db.commit()
    return {"ok": True}
 
 
@app.post("/api/costeos")
def guardar_costeo_alias(data: ListaPrecioCreate, db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):
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
 
def calcular_precios(costo_total, metodo, gp_cliente, gp_integrador, markup_cliente=None, markup_integrador=None):
    if metodo == "markup":
        precio_cliente = round(costo_total * (1 + (markup_cliente or 0) / 100), 4)
        precio_integrador = round(costo_total * (1 + (markup_integrador or 0) / 100), 4)
    else:
        gp_c = (gp_cliente or 0) / 100
        gp_i = (gp_integrador or 0) / 100
        precio_cliente = round(costo_total / (1 - gp_c), 4) if gp_c < 1 else 0
        precio_integrador = round(costo_total / (1 - gp_i), 4) if gp_i < 1 else 0
    return precio_cliente, precio_integrador
 
 
def construir_conjuntos_response(conjuntos):
    """Helper para construir la respuesta de conjuntos con datos de la lista de precios."""
    resultado = []
    for c in conjuntos:
        lista = c.lista
        resultado.append({
            "id": c.id,
            "lista_codigo": c.lista_codigo,
            "cantidad": c.cantidad,
            "nombre_conjunto": lista.nombre if lista else None,
            "precio_cliente_conjunto": lista.precio_cliente if lista else None,
            "precio_integrador_conjunto": lista.precio_integrador if lista else None,
            "costo_directo_conjunto": lista.costo_directo if lista else None,
        })
    return resultado


def construir_items_costo_response(items):
    """Helper para construir la respuesta de ítems de costo individuales (cotizaciones)."""
    resultado = []
    for ci in items:
        item = ci.item
        if item:
            costo_unit = item.costo_fabrica or 0
            resultado.append({
                "id": ci.id,
                "item_id": ci.item_id,
                "cantidad": ci.cantidad,
                "nombre": item.nombre,
                "codigo": item.codigo,
                "tipo": item.tipo,
                "subtipo": item.subtipo,
                "unidad": item.unidad,
                "costo_unit": costo_unit,
                "total": round(costo_unit * (ci.cantidad or 0), 4),
            })
    return resultado


def construir_items_catalogo_response(items):
    """Helper para construir la respuesta de ítems de costo individuales (catálogo)."""
    resultado = []
    for ci in items:
        item = ci.item
        if item:
            costo_unit = item.costo_fabrica or 0
            resultado.append({
                "id": ci.id,
                "item_id": ci.item_id,
                "cantidad": ci.cantidad,
                "nombre": item.nombre,
                "codigo": item.codigo,
                "tipo": item.tipo,
                "subtipo": item.subtipo,
                "unidad": item.unidad,
                "costo_unit": costo_unit,
                "total": round(costo_unit * (ci.cantidad or 0), 4),
            })
    return resultado

 
@app.post("/api/lista-precios", response_model=ListaPrecioResponse)
def crear_lista(data: ListaPrecioCreate, db: Session = Depends(get_db), usuario: dict = Depends(solo_admin)):
 
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
        metodo_precio=data.metodo_precio or "gp",
        markup_cliente=data.markup_cliente,
        markup_integrador=data.markup_integrador,
        costo_directo=data.costo_directo,
        costo_total=data.costo_total,
        precio_cliente=data.precio_cliente,
        precio_integrador=data.precio_integrador,
        observaciones=data.observaciones,
    )
 
    if data.items:
        for item in data.items:
            nuevo_item = ListaPrecioItem(
                lista_codigo=nuevo_codigo,
                item_id=item.get("item_id"),
                cantidad=item.get("cantidad"),
            )
            db.add(nuevo_item)
 
    db.add(nueva)
    registrar_cambio(db, usuario, "crear", "lista_precio", nuevo_codigo, data.nombre)
 
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
 
 
@app.delete("/api/lista-precios/{codigo}")
def eliminar_lista_precios(
    codigo: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_admin)
):
    lista = db.query(ListaPrecioConfig).filter(
        ListaPrecioConfig.codigo == codigo
    ).first()
 
    if not lista:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
 
    registrar_cambio(db, usuario, "eliminar", "lista_precio", lista.codigo, lista.nombre)
 
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
 
    for campo, valor in datos.items():
        if hasattr(item, campo):
            valor_anterior = getattr(item, campo)
            setattr(item, campo, valor)
            if str(valor_anterior) != str(valor):
                registrar_cambio(
                    db, usuario, "editar", "costo_item",
                    item.id, item.nombre,
                    campo=campo,
                    valor_anterior=valor_anterior,
                    valor_nuevo=valor
                )
 
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
        "metodo_precio", "markup_cliente", "markup_integrador",
        "costo_directo", "costo_total",
        "precio_cliente", "precio_integrador", "observaciones"
    }
    for campo in campos_config:
        if campo in data and data[campo] is not None:
            valor_anterior = getattr(lista, campo)
            nuevo_valor = data[campo]
            setattr(lista, campo, nuevo_valor)
            if str(valor_anterior) != str(nuevo_valor):
                registrar_cambio(
                    db, usuario, "editar", "lista_precio",
                    lista_codigo, lista.nombre,
                    campo=campo,
                    valor_anterior=valor_anterior,
                    valor_nuevo=nuevo_valor
                )
 
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
    db.flush()
 
    registrar_cambio(db, usuario, "crear", "producto", nuevo.id, nuevo.nombre)
 
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
            valor_anterior = getattr(prod, campo)
            setattr(prod, campo, valor)
            if str(valor_anterior) != str(valor):
                registrar_cambio(
                    db, usuario, "editar", "producto",
                    prod.id, prod.nombre,
                    campo=campo,
                    valor_anterior=valor_anterior,
                    valor_nuevo=valor
                )
 
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
 
    registrar_cambio(db, usuario, "eliminar", "producto", prod.id, prod.nombre)
 
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
 
    porcentaje_blue = datos.get("coeficiente_blue") if datos.get("coeficiente_blue") is not None else datos.get("coeficiente")
 
    if porcentaje_blue is None or porcentaje_blue < 0:
        raise HTTPException(status_code=400, detail="Valor inválido")
 
    db.execute(text("""
        UPDATE parametros SET valor = :valor, actualizado_en = NOW()
        WHERE clave = 'coeficiente_blue'
    """), {"valor": porcentaje_blue})
 
    items_afectados = db.query(CostoItem).filter(
        CostoItem.tipo == "Electronica",
        CostoItem.coeficiente > 1
    ).all()
 
    for item in items_afectados:
        if item.costo_fob:
            nuevo_costo = round(
                item.costo_fob * item.coeficiente * (1 + porcentaje_blue / 100), 4
            )
            db.add(CostoHistorial(
                costo_item_id=item.id,
                costo_fabrica=item.costo_fabrica,
                costo_fob=item.costo_fob,
                coeficiente=item.coeficiente,
            ))
            item.costo_fabrica = nuevo_costo
 
    db.flush()
 
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
        costo_total = costo_directo * (1 + eventuales + garantia + burden)
        precio_cliente, precio_integrador = calcular_precios(
            costo_total=costo_total,
            metodo=lista.metodo_precio or "gp",
            gp_cliente=lista.gp_cliente,
            gp_integrador=lista.gp_integrador,
            markup_cliente=lista.markup_cliente,
            markup_integrador=lista.markup_integrador
        )
        lista.costo_directo = round(costo_directo, 4)
        lista.costo_total = round(costo_total, 4)
        lista.precio_cliente = precio_cliente
        lista.precio_integrador = precio_integrador
 
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
 
 
# --- Endpoints de historial de cambios ---
 
@app.get("/api/historial")
def obtener_historial(
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_admin)
):
    return db.query(HistorialCambio).order_by(
        HistorialCambio.fecha.desc()
    ).limit(500).all()
 
 
@app.get("/api/historial/{entidad}/{entidad_id}")
def obtener_historial_entidad(
    entidad: str,
    entidad_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    return db.query(HistorialCambio).filter(
        HistorialCambio.entidad == entidad,
        HistorialCambio.entidad_id == entidad_id
    ).order_by(HistorialCambio.fecha.desc()).all()
 
 
# =========================
# CATÁLOGO DE PRODUCTOS
# =========================
 
@app.get("/api/catalogo", response_model=list[CatalogoProductoResponse])
def listar_catalogo(
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    productos = db.query(CatalogoProducto).options(
        joinedload(CatalogoProducto.conjuntos).joinedload(CatalogoConjunto.lista),
        joinedload(CatalogoProducto.items_costo).joinedload(CatalogoItem.item),
    ).all()
 
    resultado = []
    for prod in productos:
        prod_dict = {col.name: getattr(prod, col.name) for col in prod.__table__.columns}
        prod_dict["conjuntos"] = construir_conjuntos_response(prod.conjuntos)
        prod_dict["items_costo"] = construir_items_catalogo_response(prod.items_costo)
        resultado.append(prod_dict)
 
    return resultado
 
 
@app.get("/api/catalogo/{catalogo_id}", response_model=CatalogoProductoResponse)
def obtener_catalogo(
    catalogo_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    try:
        prod = db.query(CatalogoProducto).options(
            joinedload(CatalogoProducto.conjuntos).joinedload(CatalogoConjunto.lista),
            joinedload(CatalogoProducto.items_costo).joinedload(CatalogoItem.item),
        ).filter(CatalogoProducto.id == int(catalogo_id)).first()
    except ValueError:
        prod = db.query(CatalogoProducto).options(
            joinedload(CatalogoProducto.conjuntos).joinedload(CatalogoConjunto.lista),
            joinedload(CatalogoProducto.items_costo).joinedload(CatalogoItem.item),
        ).filter(CatalogoProducto.codigo == catalogo_id).first()

    if not prod:
        raise HTTPException(status_code=404, detail="Producto de catálogo no encontrado")

    prod_dict = {col.name: getattr(prod, col.name) for col in prod.__table__.columns}
    prod_dict["conjuntos"] = construir_conjuntos_response(prod.conjuntos)
    prod_dict["items_costo"] = construir_items_catalogo_response(prod.items_costo)
    return prod_dict
 
 
@app.post("/api/catalogo", response_model=CatalogoProductoResponse)
def crear_catalogo(
    data: CatalogoProductoCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_admin)
):
    ultimo = db.query(CatalogoProducto).order_by(CatalogoProducto.id.desc()).first()
    nuevo_codigo = f"CAT{(ultimo.id + 1):03d}" if ultimo else "CAT001"
 
    costo_directo = 0.0
    conjuntos_data = []
    if data.conjuntos:
        for c in data.conjuntos:
            lista = db.query(ListaPrecioConfig).filter(
                ListaPrecioConfig.codigo == c.lista_codigo
            ).first()
            if lista:
                costo_directo += (lista.costo_directo or 0) * c.cantidad
                conjuntos_data.append((c.lista_codigo, c.cantidad))

    items_costo_data = []
    if data.items_costo:
        for it in data.items_costo:
            costo_item = db.query(CostoItem).filter(
                CostoItem.id == it.get("item_id")
            ).first()
            if costo_item:
                costo_directo += (costo_item.costo_fabrica or 0) * it.get("cantidad", 1)
                items_costo_data.append((it.get("item_id"), it.get("cantidad", 1)))
 
    eventuales = (data.eventuales or 0) / 100
    garantia = (data.garantia or 0) / 100
    burden = (data.burden or 0) / 100
    costo_total = costo_directo * (1 + eventuales + garantia + burden)
    precio_cliente, precio_integrador = calcular_precios(
        costo_total=costo_total,
        metodo=data.metodo_precio or "gp",
        gp_cliente=data.gp_cliente,
        gp_integrador=data.gp_integrador,
        markup_cliente=data.markup_cliente,
        markup_integrador=data.markup_integrador
    )
 
    nuevo = CatalogoProducto(
        codigo=nuevo_codigo,
        nombre=data.nombre,
        producto_codigo=data.producto_codigo,
        producto_nombre=data.producto_nombre,
        metodo_precio=data.metodo_precio or "gp",
        gp_cliente=data.gp_cliente,
        gp_integrador=data.gp_integrador,
        markup_cliente=data.markup_cliente,
        markup_integrador=data.markup_integrador,
        eventuales=data.eventuales,
        garantia=data.garantia,
        burden=data.burden,
        costo_directo=round(costo_directo, 4),
        costo_total=round(costo_total, 4),
        precio_cliente=precio_cliente,
        precio_integrador=precio_integrador,
        observaciones=data.observaciones,
        precio_final=data.precio_final,
    )
    db.add(nuevo)
    db.flush()
 
    for lista_codigo, cantidad in conjuntos_data:
        db.add(CatalogoConjunto(
            catalogo_id=nuevo.id,
            lista_codigo=lista_codigo,
            cantidad=cantidad,
        ))

    for item_id, cantidad in items_costo_data:
        db.add(CatalogoItem(
            catalogo_id=nuevo.id,
            item_id=item_id,
            cantidad=cantidad,
        ))
 
    registrar_cambio(db, usuario, "crear", "catalogo", nuevo.id, nuevo.nombre)
    db.commit()
    db.refresh(nuevo)
 
    prod_dict = {col.name: getattr(nuevo, col.name) for col in nuevo.__table__.columns}
    prod_dict["conjuntos"] = construir_conjuntos_response(nuevo.conjuntos)
    prod_dict["items_costo"] = construir_items_catalogo_response(nuevo.items_costo)
    return prod_dict
 
 
@app.put("/api/catalogo/{catalogo_id}")
def actualizar_catalogo(
    catalogo_id: str,
    data: dict,
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    try:
        prod = db.query(CatalogoProducto).filter(
            CatalogoProducto.id == int(catalogo_id)
        ).first()
    except ValueError:
        prod = db.query(CatalogoProducto).filter(
            CatalogoProducto.codigo == catalogo_id
        ).first()

    if not prod:
        raise HTTPException(status_code=404, detail="Producto de catálogo no encontrado")

    campos = {
        "nombre", "producto_codigo", "producto_nombre", "metodo_precio",
        "gp_cliente", "gp_integrador", "markup_cliente", "markup_integrador",
        "eventuales", "garantia", "burden", "observaciones", "precio_final"
    }
    for campo in campos:
        if campo in data and data[campo] is not None:
            setattr(prod, campo, data[campo])

    if "conjuntos" in data or "items_costo" in data:
        costo_directo = 0.0

        if "conjuntos" in data:
            db.query(CatalogoConjunto).filter(
                CatalogoConjunto.catalogo_id == prod.id
            ).delete()

            for c in data["conjuntos"]:
                lista = db.query(ListaPrecioConfig).filter(
                    ListaPrecioConfig.codigo == c.get("lista_codigo")
                ).first()
                if lista:
                    costo_directo += (lista.costo_directo or 0) * c.get("cantidad", 1)
                db.add(CatalogoConjunto(
                    catalogo_id=prod.id,
                    lista_codigo=c.get("lista_codigo"),
                    cantidad=c.get("cantidad", 1),
                ))

        if "items_costo" in data:
            db.query(CatalogoItem).filter(
                CatalogoItem.catalogo_id == prod.id
            ).delete()

            for it in data["items_costo"]:
                costo_item = db.query(CostoItem).filter(
                    CostoItem.id == it.get("item_id")
                ).first()
                if costo_item:
                    costo_directo += (costo_item.costo_fabrica or 0) * it.get("cantidad", 1)
                    db.add(CatalogoItem(
                        catalogo_id=prod.id,
                        item_id=it.get("item_id"),
                        cantidad=it.get("cantidad", 1),
                    ))

        eventuales = (prod.eventuales or 0) / 100
        garantia = (prod.garantia or 0) / 100
        burden = (prod.burden or 0) / 100
        costo_total = costo_directo * (1 + eventuales + garantia + burden)
        precio_cliente, precio_integrador = calcular_precios(
            costo_total=costo_total,
            metodo=prod.metodo_precio or "gp",
            gp_cliente=prod.gp_cliente,
            gp_integrador=prod.gp_integrador,
            markup_cliente=prod.markup_cliente,
            markup_integrador=prod.markup_integrador
        )
        prod.costo_directo = round(costo_directo, 4)
        prod.costo_total = round(costo_total, 4)
        prod.precio_cliente = precio_cliente
        prod.precio_integrador = precio_integrador

    registrar_cambio(db, usuario, "editar", "catalogo", prod.id, prod.nombre)
    db.commit()
    db.refresh(prod)
    return {"ok": True, "mensaje": "Producto de catálogo actualizado correctamente"}
 
@app.delete("/api/catalogo/{catalogo_id}")
def eliminar_catalogo(
    catalogo_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_admin)
):
    try:
        prod = db.query(CatalogoProducto).filter(
            CatalogoProducto.id == int(catalogo_id)
        ).first()
    except ValueError:
        prod = db.query(CatalogoProducto).filter(
            CatalogoProducto.codigo == catalogo_id
        ).first()

    if not prod:
        raise HTTPException(status_code=404, detail="Producto de catálogo no encontrado")

    registrar_cambio(db, usuario, "eliminar", "catalogo", prod.id, prod.nombre)
    db.delete(prod)
    db.commit()
    return {"ok": True}
 
# =========================
# COTIZACIONES POR PROYECTO
# =========================
 
@app.get("/api/cotizaciones", response_model=list[CotizacionResponse])
def listar_cotizaciones(
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    cotizaciones = db.query(Cotizacion).options(
        joinedload(Cotizacion.conjuntos).joinedload(CotizacionConjunto.lista),
        joinedload(Cotizacion.items_costo).joinedload(CotizacionItem.item),
    ).all()
 
    resultado = []
    for cot in cotizaciones:
        cot_dict = {col.name: getattr(cot, col.name) for col in cot.__table__.columns}
        cot_dict["conjuntos"] = construir_conjuntos_response(cot.conjuntos)
        cot_dict["items_costo"] = construir_items_costo_response(cot.items_costo)
        resultado.append(cot_dict)
 
    return resultado
 
 
@app.get("/api/cotizaciones/{cotizacion_id}", response_model=CotizacionResponse)
def obtener_cotizacion(
    cotizacion_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    try:
        cot = db.query(Cotizacion).options(
            joinedload(Cotizacion.conjuntos).joinedload(CotizacionConjunto.lista),
            joinedload(Cotizacion.items_costo).joinedload(CotizacionItem.item),
        ).filter(Cotizacion.id == int(cotizacion_id)).first()
    except ValueError:
        cot = db.query(Cotizacion).options(
            joinedload(Cotizacion.conjuntos).joinedload(CotizacionConjunto.lista),
            joinedload(Cotizacion.items_costo).joinedload(CotizacionItem.item),
        ).filter(Cotizacion.codigo == cotizacion_id).first()

    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    cot_dict = {col.name: getattr(cot, col.name) for col in cot.__table__.columns}
    cot_dict["conjuntos"] = construir_conjuntos_response(cot.conjuntos)
    cot_dict["items_costo"] = construir_items_costo_response(cot.items_costo)
    return cot_dict
 
 
@app.post("/api/cotizaciones", response_model=CotizacionResponse)
def crear_cotizacion(
    data: CotizacionCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_admin)
):
    ultimo = db.query(Cotizacion).order_by(Cotizacion.id.desc()).first()
    nuevo_codigo = f"COT{(ultimo.id + 1):03d}" if ultimo else "COT001"
 
    costo_directo = 0.0
    conjuntos_data = []
    if data.conjuntos:
        for c in data.conjuntos:
            lista = db.query(ListaPrecioConfig).filter(
                ListaPrecioConfig.codigo == c.lista_codigo
            ).first()
            if lista:
                costo_directo += (lista.costo_directo or 0) * c.cantidad
                conjuntos_data.append((c.lista_codigo, c.cantidad))

    items_costo_data = []
    if data.items_costo:
        for it in data.items_costo:
            costo_item = db.query(CostoItem).filter(
                CostoItem.id == it.get("item_id")
            ).first()
            if costo_item:
                costo_directo += (costo_item.costo_fabrica or 0) * it.get("cantidad", 1)
                items_costo_data.append((it.get("item_id"), it.get("cantidad", 1)))
 
    eventuales = (data.eventuales or 0) / 100
    garantia = (data.garantia or 0) / 100
    burden = (data.burden or 0) / 100
    costo_total = costo_directo * (1 + eventuales + garantia + burden)
    precio_cliente, precio_integrador = calcular_precios(
        costo_total=costo_total,
        metodo=data.metodo_precio or "gp",
        gp_cliente=data.gp_cliente,
        gp_integrador=data.gp_integrador,
        markup_cliente=data.markup_cliente,
        markup_integrador=data.markup_integrador
    )
 
    nueva = Cotizacion(
        codigo=nuevo_codigo,
        nombre=data.nombre,
        cliente=data.cliente,
        producto_codigo=data.producto_codigo,
        producto_nombre=data.producto_nombre,
        metodo_precio=data.metodo_precio or "gp",
        gp_cliente=data.gp_cliente,
        gp_integrador=data.gp_integrador,
        markup_cliente=data.markup_cliente,
        markup_integrador=data.markup_integrador,
        eventuales=data.eventuales,
        garantia=data.garantia,
        burden=data.burden,
        costo_directo=round(costo_directo, 4),
        costo_total=round(costo_total, 4),
        precio_cliente=precio_cliente,
        precio_integrador=precio_integrador,
        observaciones=data.observaciones,
        precio_final=data.precio_final,
    )
    db.add(nueva)
    db.flush()
 
    for lista_codigo, cantidad in conjuntos_data:
        db.add(CotizacionConjunto(
            cotizacion_id=nueva.id,
            lista_codigo=lista_codigo,
            cantidad=cantidad,
        ))

    for item_id, cantidad in items_costo_data:
        db.add(CotizacionItem(
            cotizacion_id=nueva.id,
            item_id=item_id,
            cantidad=cantidad,
        ))
 
    registrar_cambio(db, usuario, "crear", "cotizacion", nueva.id, nueva.nombre)
    db.commit()
    db.refresh(nueva)
 
    cot_dict = {col.name: getattr(nueva, col.name) for col in nueva.__table__.columns}
    cot_dict["conjuntos"] = construir_conjuntos_response(nueva.conjuntos)
    cot_dict["items_costo"] = construir_items_costo_response(nueva.items_costo)
    return cot_dict
 

@app.put("/api/cotizaciones/{cotizacion_id}")
def actualizar_cotizacion(
    cotizacion_id: str,
    data: dict,
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    try:
        cot = db.query(Cotizacion).filter(
            Cotizacion.id == int(cotizacion_id)
        ).first()
    except ValueError:
        cot = db.query(Cotizacion).filter(
            Cotizacion.codigo == cotizacion_id
        ).first()

    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    campos = {
        "nombre", "cliente", "producto_codigo", "producto_nombre", "metodo_precio",
        "gp_cliente", "gp_integrador", "markup_cliente", "markup_integrador",
        "eventuales", "garantia", "burden", "observaciones", "precio_final"
    }
    for campo in campos:
        if campo in data and data[campo] is not None:
            setattr(cot, campo, data[campo])

    if "conjuntos" in data or "items_costo" in data:
        costo_directo = 0.0

        if "conjuntos" in data:
            db.query(CotizacionConjunto).filter(
                CotizacionConjunto.cotizacion_id == cot.id
            ).delete()

            for c in data["conjuntos"]:
                lista = db.query(ListaPrecioConfig).filter(
                    ListaPrecioConfig.codigo == c.get("lista_codigo")
                ).first()
                if lista:
                    costo_directo += (lista.costo_directo or 0) * c.get("cantidad", 1)
                db.add(CotizacionConjunto(
                    cotizacion_id=cot.id,
                    lista_codigo=c.get("lista_codigo"),
                    cantidad=c.get("cantidad", 1),
                ))

        if "items_costo" in data:
            db.query(CotizacionItem).filter(
                CotizacionItem.cotizacion_id == cot.id
            ).delete()
            for it in data["items_costo"]:
                costo_item = db.query(CostoItem).filter(
                    CostoItem.id == it.get("item_id")
                ).first()
                if costo_item:
                    costo_directo += (costo_item.costo_fabrica or 0) * it.get("cantidad", 1)
                    db.add(CotizacionItem(
                        cotizacion_id=cot.id,
                        item_id=it.get("item_id"),
                        cantidad=it.get("cantidad", 1),
                    ))

        eventuales = (cot.eventuales or 0) / 100
        garantia = (cot.garantia or 0) / 100
        burden = (cot.burden or 0) / 100
        costo_total = costo_directo * (1 + eventuales + garantia + burden)
        precio_cliente, precio_integrador = calcular_precios(
            costo_total=costo_total,
            metodo=cot.metodo_precio or "gp",
            gp_cliente=cot.gp_cliente,
            gp_integrador=cot.gp_integrador,
            markup_cliente=cot.markup_cliente,
            markup_integrador=cot.markup_integrador
        )
        cot.costo_directo = round(costo_directo, 4)
        cot.costo_total = round(costo_total, 4)
        cot.precio_cliente = precio_cliente
        cot.precio_integrador = precio_integrador

    registrar_cambio(db, usuario, "editar", "cotizacion", cot.id, cot.nombre)
    db.commit()
    db.refresh(cot)
    return {"ok": True, "mensaje": "Cotización actualizada correctamente"}
 
 
@app.delete("/api/cotizaciones/{cotizacion_id}")
def eliminar_cotizacion(
    cotizacion_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(solo_admin)
):
    try:
        cot = db.query(Cotizacion).filter(
            Cotizacion.id == int(cotizacion_id)
        ).first()
    except ValueError:
        cot = db.query(Cotizacion).filter(
            Cotizacion.codigo == cotizacion_id
        ).first()

    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    registrar_cambio(db, usuario, "eliminar", "cotizacion", cot.id, cot.nombre)
    db.delete(cot)
    db.commit()
    return {"ok": True}
 
# =========================
# BLOQUEOS DE EDICIÓN
# =========================
 
@app.post("/api/locks/{entidad}/{entidad_id}")
def adquirir_lock(
    entidad: str,
    entidad_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    from sqlalchemy import text
    from datetime import timedelta
 
    result = db.execute(text("""
        SELECT usuario_email, usuario_nombre, adquirido_en
        FROM edicion_locks
        WHERE entidad = :entidad AND entidad_id = :entidad_id
        AND adquirido_en > NOW() - INTERVAL '30 minutes'
    """), {"entidad": entidad, "entidad_id": entidad_id}).fetchone()
 
    if result and result[0] != usuario.get("email"):
        raise HTTPException(
            status_code=423,
            detail=f"Este elemento está siendo editado por {result[1] or result[0]}"
        )
 
    db.execute(text("""
        INSERT INTO edicion_locks (entidad, entidad_id, usuario_email, usuario_nombre, adquirido_en)
        VALUES (:entidad, :entidad_id, :email, :nombre, NOW())
        ON CONFLICT (entidad, entidad_id)
        DO UPDATE SET usuario_email = :email, usuario_nombre = :nombre, adquirido_en = NOW()
    """), {
        "entidad": entidad,
        "entidad_id": entidad_id,
        "email": usuario.get("email"),
        "nombre": f"{usuario.get('nombre', '')} {usuario.get('apellido', '')}".strip()
    })
    db.commit()
    return {"ok": True, "mensaje": "Lock adquirido"}
 
 
@app.delete("/api/locks/{entidad}/{entidad_id}")
def liberar_lock(
    entidad: str,
    entidad_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    from sqlalchemy import text
    db.execute(text("""
        DELETE FROM edicion_locks
        WHERE entidad = :entidad AND entidad_id = :entidad_id
        AND usuario_email = :email
    """), {
        "entidad": entidad,
        "entidad_id": entidad_id,
        "email": usuario.get("email")
    })
    db.commit()
    return {"ok": True, "mensaje": "Lock liberado"}
 
 
@app.get("/api/locks/{entidad}/{entidad_id}")
def verificar_lock(
    entidad: str,
    entidad_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(admin_o_vendedor)
):
    from sqlalchemy import text
    result = db.execute(text("""
        SELECT usuario_email, usuario_nombre, adquirido_en
        FROM edicion_locks
        WHERE entidad = :entidad AND entidad_id = :entidad_id
        AND adquirido_en > NOW() - INTERVAL '30 minutes'
    """), {"entidad": entidad, "entidad_id": entidad_id}).fetchone()
 
    if not result:
        return {"bloqueado": False}
 
    es_propio = result[0] == usuario.get("email")
    return {
        "bloqueado": not es_propio,
        "usuario_email": result[0],
        "usuario_nombre": result[1],
        "adquirido_en": result[2],
        "es_propio": es_propio
    }
 
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
