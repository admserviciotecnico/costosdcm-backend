import json
from pathlib import Path
from sqlalchemy.orm import Session

from backend_costeo.database import SessionLocal
from backend_costeo.models import Producto, CostoItem, ListaPrecioConfig

BASE_DIR = Path(__file__).resolve().parent
SEED_DIR = BASE_DIR.parent / "data_seed"

def load_json(filename):
    path = SEED_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_if_empty():
    db: Session = SessionLocal()

    try:
        # 🧪 Verificamos si ya hay datos
        if db.query(Producto).first():
            print("📦 Base de datos ya inicializada, seed omitido")
            return

        print("🌱 Inicializando base de datos desde JSON...")

        # Productos
        for item in load_json("producto_catalogo.json"):
            db.add(Producto(**item))

        # Costos
        for item in load_json("costos_generales_full.json"):
            db.add(CostoItem(**item))

        # Listas de precios (opcional)
        for item in load_json("listas_precios.json"):
            db.add(ListaPrecioConfig(**item))

        db.commit()
        print("✅ Seed completado correctamente")

    except Exception as e:
        db.rollback()
        print("❌ Error en seed:", e)
    finally:
        db.close()
