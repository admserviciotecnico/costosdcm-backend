from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend_costeo.database import Base


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True)
    denominacion = Column(String)
    linea = Column(String, index=True)
    serie = Column(String, index=True)


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

    historial = relationship("CostoHistorial", back_populates="costo_item")


class CostoHistorial(Base):
    __tablename__ = "costos_historial"

    id = Column(Integer, primary_key=True, index=True)
    costo_item_id = Column(Integer, ForeignKey("costos_items.id"))
    fecha = Column(DateTime, default=datetime.utcnow)

    costo_fabrica = Column(Float, nullable=True)
    costo_fob = Column(Float, nullable=True)
    coeficiente = Column(Float, nullable=True)

    costo_item = relationship("CostoItem", back_populates="historial")
