import json
from pathlib import Path
from sqlalchemy.orm import Session

from backend_costeo.database import SessionLocal
from backend_costeo.models import Producto, CostoItem, ListaPrecioConfig

BASE_DIR = Path(__file__).resolve().parent
SEED_DIR = BASE_DIR / "data_seed"

def load_json(filename):
    path = SEED_DIR / filename
    if not path.exists():
        print(f"⚠️ Archivo {filename} no encontrado")
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def seed_costos_only(db: Session):
    try:
        costos_json = load_json("costos_generales_full.json")
        count = 0

        for tipo, subtipos in costos_json.items():
            for subtipo, contenido in subtipos.items():

                if isinstance(contenido, list):
                    for item in contenido:
                        nuevo = CostoItem(
                            codigo=item.get("codigo") or None,
                            nombre=item.get("denominacion"),
                            tipo=tipo,
                            subtipo=subtipo,
                            unidad=item.get("unidad"),
                            coeficiente=item.get("coeficiente"),
                            costo_fob=item.get("costo_fob"),
                            costo_fabrica=item.get("costo_fabrica"),
                        )
                        db.add(nuevo)
                        count += 1

                elif isinstance(contenido, dict):
                    for variante, items in contenido.items():
                        for item in items:
                            nuevo = CostoItem(
                                codigo=item.get("codigo") or None,
                                nombre=item.get("denominacion"),
                                tipo=tipo,
                                subtipo=f"{subtipo} - {variante}",
                                unidad=item.get("unidad"),
                                coeficiente=item.get("coeficiente"),
                                costo_fob=item.get("costo_fob"),
                                costo_fabrica=item.get("costo_fabrica"),
                            )
                            db.add(nuevo)
                            count += 1

        db.commit()
        print(f"✅ {count} ítems de costo recargados correctamente")

    except Exception as e:
        db.rollback()
        print("❌ Error en reload costos:", e)
        raise

def seed_if_empty():
    db: Session = SessionLocal()

    try:
        if db.query(Producto).first():
            print("📦 Base de datos ya inicializada, seed omitido")
            return

        print("🌱 Inicializando base de datos desde JSON...")

        # =========================
        # PRODUCTOS (JSON ANIDADO)
        # =========================
        productos_json = load_json("productos_catalogo.json")

        for linea, series in productos_json.items():
            for serie, productos in series.items():
                for producto in productos:
                    db.add(Producto(
                        codigo=producto["codigo"],
                        nombre=producto["nombre"],
                        linea=linea,
                        serie=serie
                    ))

        # =========================
        # COSTOS (JSON ANIDADO)
        # =========================
        costos_json = load_json("costos_generales_full.json")

        for tipo, subtipos in costos_json.items():

            for subtipo, contenido in subtipos.items():

                # Caso normal: lista directa de items
                if isinstance(contenido, list):

                    for item in contenido:

                        codigo_item = item.get("codigo") or None

                        # ✅ Si tiene código, verificar duplicado antes de insertar
                        if codigo_item:
                            existente = db.query(CostoItem).filter_by(codigo=codigo_item).first()
                        else:
                            existente = None  # Sin código → siempre insertar

                        if existente:
                            # 🔄 ACTUALIZAR
                            existente.nombre = item.get("denominacion")
                            existente.tipo = tipo
                            existente.subtipo = subtipo
                            existente.unidad = item.get("unidad")
                            existente.coeficiente = item.get("coeficiente")
                            existente.costo_fob = item.get("costo_fob")
                            existente.costo_fabrica = item.get("costo_fabrica")
                        else:
                            # ➕ CREAR (con o sin código)
                            nuevo = CostoItem(
                                codigo=codigo_item,
                                nombre=item.get("denominacion"),
                                tipo=tipo,
                                subtipo=subtipo,
                                unidad=item.get("unidad"),
                                coeficiente=item.get("coeficiente"),
                                costo_fob=item.get("costo_fob"),
                                costo_fabrica=item.get("costo_fabrica"),
                            )
                            db.add(nuevo)
                            db.flush()

                # Caso con tercer nivel (variante)
                elif isinstance(contenido, dict):

                    for variante, items in contenido.items():

                        for item in items:

                            codigo_item = item.get("codigo") or None
                            subtipo_completo = f"{subtipo} - {variante}"

                            # ✅ Si tiene código, verificar duplicado antes de insertar
                            if codigo_item:
                                existente = db.query(CostoItem).filter_by(codigo=codigo_item).first()
                            else:
                                existente = None  # Sin código → siempre insertar

                            if existente:
                                # 🔄 ACTUALIZAR
                                existente.nombre = item.get("denominacion")
                                existente.tipo = tipo
                                existente.subtipo = subtipo_completo
                                existente.unidad = item.get("unidad")
                                existente.coeficiente = item.get("coeficiente")
                                existente.costo_fob = item.get("costo_fob")
                                existente.costo_fabrica = item.get("costo_fabrica")
                            else:
                                # ➕ CREAR (con o sin código)
                                nuevo = CostoItem(
                                    codigo=codigo_item,
                                    nombre=item.get("denominacion"),
                                    tipo=tipo,
                                    subtipo=subtipo_completo,
                                    unidad=item.get("unidad"),
                                    coeficiente=item.get("coeficiente"),
                                    costo_fob=item.get("costo_fob"),
                                    costo_fabrica=item.get("costo_fabrica"),
                                )
                                db.add(nuevo)
                                db.flush()

        db.commit()
        print("✅ Seed completado correctamente")

    except Exception as e:
        db.rollback()
        print("❌ Error en seed:", e)

    finally:
        db.close()