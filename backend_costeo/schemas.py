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
    model_config = ConfigDict(from_attributes=True)
    items: list[ListaPrecioItemResponse] = []



