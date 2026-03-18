from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend_costeo.database import Base

class HistorialCambio(Base):
    __tablename__ = "historial_cambios"
    id = Column(Integer, primary_key=True)
    usuario_email = Column(String, nullable=False)
    usuario_nombre = Column(String)
    accion = Column(String, nullable=False)  # "crear", "editar", "eliminar"
    entidad = Column(String, nullable=False)  # "costo_item", "producto", "lista_precio"
    entidad_id = Column(String)
    entidad_nombre = Column(String)
    campo = Column(String)
    valor_anterior = Column(String)
    valor_nuevo = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)


def registrar_cambio(
    db: Session,
    usuario: dict,
    accion: str,
    entidad: str,
    entidad_id: str,
    entidad_nombre: str,
    campo: str = None,
    valor_anterior=None,
    valor_nuevo=None
):
    db.add(HistorialCambio(
        usuario_email=usuario.get("email"),
        usuario_nombre=f"{usuario.get('nombre', '')} {usuario.get('apellido', '')}".strip(),
        accion=accion,
        entidad=entidad,
        entidad_id=str(entidad_id),
        entidad_nombre=entidad_nombre,
        campo=campo,
        valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
        valor_nuevo=str(valor_nuevo) if valor_nuevo is not None else None,
    ))