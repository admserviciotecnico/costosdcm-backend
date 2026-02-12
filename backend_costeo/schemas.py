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


from pydantic import BaseModel
from typing import List, Optional

class ListaPrecioCreate(BaseModel):
    nombre: str   # 🔥 AGREGAR ESTO

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

    # si estás recibiendo items
    items: Optional[list] = []




class ListaPrecioResponse(ListaPrecioCreate):
    codigo: str
    creada_en: datetime

    class Config:
        from_attributes = True
