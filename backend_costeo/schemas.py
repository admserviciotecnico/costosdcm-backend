from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
 
 
# =========================
# LISTA DE PRECIOS
# =========================
 
class ListaPrecioItemResponse(BaseModel):
    item_id: int | None = None
    codigo: str | None = None
    nombre: str | None = None
    tipo: str | None = None
    subtipo: str | None = None
    unidad: str | None = None
    costo_unit: float | None = None
    cantidad: float | None = None
    total: float | None = None
    model_config = ConfigDict(from_attributes=True)
 
 
class ListaPrecioCreate(BaseModel):
    nombre: str
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
    metodo_precio: Optional[str] = "gp"
    markup_cliente: Optional[float] = None
    markup_integrador: Optional[float] = None
    items: Optional[List[dict]] = None
    observaciones: Optional[str] = None
 
 
class ListaPrecioResponse(BaseModel):
    codigo: str
    nombre: str
    producto_codigo: Optional[str] = None
    producto_nombre: Optional[str] = None
    eventuales: Optional[float] = None
    garantia: Optional[float] = None
    burden: Optional[float] = None
    gp_cliente: Optional[float] = None
    gp_integrador: Optional[float] = None
    costo_directo: Optional[float] = None
    costo_total: Optional[float] = None
    precio_cliente: Optional[float] = None
    precio_integrador: Optional[float] = None
    metodo_precio: Optional[str] = "gp"
    markup_cliente: Optional[float] = None
    markup_integrador: Optional[float] = None
    creada_en: datetime
    observaciones: Optional[str] = None
    items: list[ListaPrecioItemResponse] = []
    model_config = ConfigDict(from_attributes=True)
 
 
# =========================
# CATÁLOGO DE PRODUCTOS
# =========================
 
class CatalogoConjuntoItem(BaseModel):
    lista_codigo: str
    cantidad: float = 1
 
 
class CatalogoConjuntoResponse(BaseModel):
    id: int
    lista_codigo: str
    cantidad: float
    nombre_conjunto: Optional[str] = None
    precio_cliente_conjunto: Optional[float] = None
    precio_integrador_conjunto: Optional[float] = None
    costo_directo_conjunto: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)
 
 
class CatalogoProductoCreate(BaseModel):
    nombre: str
    producto_codigo: Optional[str] = None
    producto_nombre: Optional[str] = None
    metodo_precio: Optional[str] = "gp"
    gp_cliente: Optional[float] = 0
    gp_integrador: Optional[float] = 0
    markup_cliente: Optional[float] = None
    markup_integrador: Optional[float] = None
    eventuales: Optional[float] = 0
    garantia: Optional[float] = 0
    burden: Optional[float] = 0
    observaciones: Optional[str] = None
    conjuntos: Optional[List[CatalogoConjuntoItem]] = None
    precio_final: Optional[float] = None
 
 
class CatalogoProductoResponse(BaseModel):
    id: int
    codigo: Optional[str] = None
    nombre: str
    producto_codigo: Optional[str] = None
    producto_nombre: Optional[str] = None
    metodo_precio: Optional[str] = "gp"
    gp_cliente: Optional[float] = None
    gp_integrador: Optional[float] = None
    markup_cliente: Optional[float] = None
    markup_integrador: Optional[float] = None
    eventuales: Optional[float] = None
    garantia: Optional[float] = None
    burden: Optional[float] = None
    costo_directo: Optional[float] = None
    costo_total: Optional[float] = None
    precio_cliente: Optional[float] = None
    precio_integrador: Optional[float] = None
    observaciones: Optional[str] = None
    creada_en: datetime
    conjuntos: List[CatalogoConjuntoResponse] = []
    model_config = ConfigDict(from_attributes=True)
    precio_final: Optional[float] = None
 
 
# =========================
# COTIZACIONES POR PROYECTO
# =========================
 
class CotizacionConjuntoItem(BaseModel):
    lista_codigo: str
    cantidad: float = 1
 
 
class CotizacionConjuntoResponse(BaseModel):
    id: int
    lista_codigo: str
    cantidad: float
    nombre_conjunto: Optional[str] = None
    precio_cliente_conjunto: Optional[float] = None
    precio_integrador_conjunto: Optional[float] = None
    costo_directo_conjunto: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)
 
 
class CotizacionCreate(BaseModel):
    nombre: str
    cliente: str
    producto_codigo: Optional[str] = None
    producto_nombre: Optional[str] = None
    metodo_precio: Optional[str] = "gp"
    gp_cliente: Optional[float] = 0
    gp_integrador: Optional[float] = 0
    markup_cliente: Optional[float] = None
    markup_integrador: Optional[float] = None
    eventuales: Optional[float] = 0
    garantia: Optional[float] = 0
    burden: Optional[float] = 0
    items_costo: Optional[List[dict]] = None
    observaciones: Optional[str] = None
    conjuntos: Optional[List[CotizacionConjuntoItem]] = None
    precio_final: Optional[float] = None
 
 
class CotizacionResponse(BaseModel):
    id: int
    codigo: Optional[str] = None
    nombre: str
    cliente: str
    producto_codigo: Optional[str] = None
    producto_nombre: Optional[str] = None
    metodo_precio: Optional[str] = "gp"
    gp_cliente: Optional[float] = None
    gp_integrador: Optional[float] = None
    markup_cliente: Optional[float] = None
    markup_integrador: Optional[float] = None
    eventuales: Optional[float] = None
    garantia: Optional[float] = None
    burden: Optional[float] = None
    costo_directo: Optional[float] = None
    costo_total: Optional[float] = None
    precio_cliente: Optional[float] = None
    precio_integrador: Optional[float] = None
    observaciones: Optional[str] = None
    items_costo: List[CotizacionItemResponse] = []
    creada_en: datetime
    conjuntos: List[CotizacionConjuntoResponse] = []
    model_config = ConfigDict(from_attributes=True)
    precio_final: Optional[float] = None
 

class CotizacionItemResponse(BaseModel):
    id: int
    item_id: int
    cantidad: float
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    tipo: Optional[str] = None
    subtipo: Optional[str] = None
    unidad: Optional[str] = None
    costo_unit: Optional[float] = None
    total: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)
