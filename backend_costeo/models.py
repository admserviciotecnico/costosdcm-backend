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

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, index=True)
    subtipo = Column(String, index=True)
    item = Column(Integer, nullable=True)
    codigo = Column(String, nullable=True)
    denominacion = Column(String)
    unidad = Column(String)

    costo_fabrica = Column(Float, nullable=True)
    costo_fob = Column(Float, nullable=True)
    coeficiente = Column(Float, nullable=True)

    historial = relationship(
    "CostoHistorial",
    back_populates="costo_item",
    cascade="all, delete-orphan"
)


class ListaPrecioConfig(Base):
    __tablename__ = "listas_precios"

    id = Column(Integer, primary_key=True, index=True)

    # Producto asociado
    producto_codigo = Column(String, index=True, nullable=False)
    producto_nombre = Column(String, nullable=False)

    # Parámetros de cálculo
    eventuales = Column(Float, nullable=False)
    garantia = Column(Float, nullable=False)
    burden = Column(Float, nullable=False)
    gp_cliente = Column(Float, nullable=False)
    gp_integrador = Column(Float, nullable=False)

    # Resultados
    costo_directo = Column(Float, nullable=False)
    costo_total = Column(Float, nullable=False)
    precio_cliente = Column(Float, nullable=False)
    precio_integrador = Column(Float, nullable=False)

    # Metadata
    creada_en = Column(DateTime, default=datetime.utcnow)


class CostoHistorial(Base):
    __tablename__ = "costos_historial"

    id = Column(Integer, primary_key=True, index=True)
    costo_item_id = Column(Integer, ForeignKey("costos_items.id"))
    fecha = Column(DateTime, default=datetime.utcnow)

    costo_fabrica = Column(Float, nullable=True)
    costo_fob = Column(Float, nullable=True)
    coeficiente = Column(Float, nullable=True)

    costo_item = relationship("CostoItem", back_populates="historial")
