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

        for item in costos_json:

            normalizado = {
                "codigo": item.get("codigo"),
                "denominacion": item.get("nombre"),
                "tipo": item.get("categoria"),   # 👈 aquí el fix
                "subtipo": item.get("subtipo"),
                "unidad": item.get("unidad"),
                "costo_fabrica": item.get("costo_fabrica", 0),
                "costo_fob": item.get("costo_fob", 0),
                "coeficiente": item.get("coeficiente", 1),
            }

        db.add(CostoItem(**normalizado))


        db.commit()
        print("✅ Seed completado correctamente")

    except Exception as e:
        db.rollback()
        print("❌ Error en seed:", e)

    finally:
        db.close()
