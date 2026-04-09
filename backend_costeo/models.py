from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend_costeo.historial import HistorialCambio
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
    codigo = Column(String, nullable=True, index=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    subtipo = Column(String, nullable=False)
    unidad = Column(String, nullable=True)
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
    metodo_precio = Column(String, default="gp")
    markup_cliente = Column(Float, nullable=True)
    markup_integrador = Column(Float, nullable=True)
    observaciones = Column(String, nullable=True)
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
    id = Column(Integer, primary_key=True, index=True)
    costo_item_id = Column(Integer, ForeignKey("costos_items.id"))
    fecha = Column(DateTime, default=datetime.utcnow)
    costo_fabrica = Column(Float, nullable=True)
    costo_fob = Column(Float, nullable=True)
    coeficiente = Column(Float, nullable=True)
    costo_item = relationship(
        "CostoItem",
        back_populates="historial"
    )
 
 
# =========================
# CATÁLOGO DE PRODUCTOS
# =========================
 
class CatalogoProducto(Base):
    __tablename__ = "catalogo_productos"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=True)
    nombre = Column(String, nullable=False)
    producto_codigo = Column(String, nullable=True)
    producto_nombre = Column(String, nullable=True)
    metodo_precio = Column(String, default="gp")
    gp_cliente = Column(Float, nullable=True)
    gp_integrador = Column(Float, nullable=True)
    markup_cliente = Column(Float, nullable=True)
    markup_integrador = Column(Float, nullable=True)
    eventuales = Column(Float, default=0)
    garantia = Column(Float, default=0)
    burden = Column(Float, default=0)
    costo_directo = Column(Float, nullable=True)
    costo_total = Column(Float, nullable=True)
    precio_cliente = Column(Float, nullable=True)
    precio_integrador = Column(Float, nullable=True)
    observaciones = Column(String, nullable=True)
    creada_en = Column(DateTime, default=datetime.utcnow)
    precio_final = Column(Float, nullable=True)
    conjuntos = relationship(
        "CatalogoConjunto",
        back_populates="catalogo",
        cascade="all, delete-orphan"
    )
 
 
class CatalogoConjunto(Base):
    __tablename__ = "catalogo_conjuntos"
    id = Column(Integer, primary_key=True)
    catalogo_id = Column(Integer, ForeignKey("catalogo_productos.id"))
    lista_codigo = Column(String, ForeignKey("listas_precios.codigo"))
    cantidad = Column(Float, default=1)
    lista = relationship("ListaPrecioConfig", lazy="joined")
    catalogo = relationship("CatalogoProducto", back_populates="conjuntos")
 
 
# =========================
# COTIZACIONES POR PROYECTO
# =========================
 
class Cotizacion(Base):
    __tablename__ = "cotizaciones"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=True)
    nombre = Column(String, nullable=False)
    cliente = Column(String, nullable=False)
    producto_codigo = Column(String, nullable=True)
    producto_nombre = Column(String, nullable=True)
    metodo_precio = Column(String, default="gp")
    gp_cliente = Column(Float, nullable=True)
    gp_integrador = Column(Float, nullable=True)
    markup_cliente = Column(Float, nullable=True)
    markup_integrador = Column(Float, nullable=True)
    eventuales = Column(Float, default=0)
    garantia = Column(Float, default=0)
    burden = Column(Float, default=0)
    costo_directo = Column(Float, nullable=True)
    costo_total = Column(Float, nullable=True)
    precio_cliente = Column(Float, nullable=True)
    precio_integrador = Column(Float, nullable=True)
    observaciones = Column(String, nullable=True)
    creada_en = Column(DateTime, default=datetime.utcnow)
    precio_final = Column(Float, nullable=True)
    conjuntos = relationship(
        "CotizacionConjunto",
        back_populates="cotizacion",
        cascade="all, delete-orphan"
    )
 
 
class CotizacionConjunto(Base):
    __tablename__ = "cotizacion_conjuntos"
    id = Column(Integer, primary_key=True)
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"))
    lista_codigo = Column(String, ForeignKey("listas_precios.codigo"))
    cantidad = Column(Float, default=1)
    lista = relationship("ListaPrecioConfig", lazy="joined")
    cotizacion = relationship("Cotizacion", back_populates="conjuntos")
 
