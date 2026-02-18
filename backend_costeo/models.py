from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from backend_costeo.database import Base
except ModuleNotFoundError:
    from database import Base

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    linea = Column(String, nullable=False)
    serie = Column(String, nullable=True)
    descripcion = Column(String, nullable=True)



class CostoItem(Base):
    __tablename__ = "costos_items"

    id = Column(Integer, primary_key=True)

    historial = relationship(
        "CostoHistorial",
        back_populates="item",
        cascade="all, delete-orphan"
    )





from sqlalchemy import Column, String, Float, DateTime

class ListaPrecioConfig(Base):
    __tablename__ = "listas_precios"

    codigo = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)

    producto_codigo = Column(String)
    producto_nombre = Column(String)

    eventuales = Column(Float)
    garantia = Column(Float)
    burden = Column(Float)
    gp_cliente = Column(Float)
    gp_integrador = Column(Float)

    costo_directo = Column(Float)
    costo_total = Column(Float)
    precio_cliente = Column(Float)
    precio_integrador = Column(Float)

    creada_en = Column(DateTime, default=datetime.utcnow)
   
    items = relationship(
    "ListaPrecioItem",
    back_populates="lista",
    cascade="all, delete-orphan"
    )

class ListaPrecioItem(Base):
    __tablename__ = "listas_precios_items"

    id = Column(Integer, primary_key=True)

    lista_codigo = Column(String, ForeignKey("listas_precios.codigo"))
    item_id = Column(Integer, ForeignKey("costos_items.id"))

    cantidad = Column(Float)

    item = relationship("CostoItem", lazy="joined")
    lista = relationship("ListaPrecioConfig", back_populates="items")


class CostoHistorial(Base):
    __tablename__ = "costos_historial"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("costos_items.id"))

    item = relationship(
        "CostoItem",
        back_populates="historial"
    )

