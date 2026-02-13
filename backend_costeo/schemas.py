from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


# =========================
# LISTA DE PRECIOS
# =========================

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

    items: Optional[List[dict]] = None


class ListaPrecioResponse(BaseModel):
    codigo: str
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

    creada_en: datetime

    model_config = ConfigDict(from_attributes=True)