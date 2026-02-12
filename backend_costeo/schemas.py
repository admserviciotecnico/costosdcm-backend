from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# =========================
# LISTA DE PRECIOS
# =========================

class ListaPrecioBase(BaseModel):
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


class ListaPrecioCreate(ListaPrecioBase):
    pass


class ListaPrecioResponse(ListaPrecioBase):
    creada_en: datetime

    class Config:
        from_attributes = True
