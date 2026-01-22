import json
import sys
from pathlib import Path

# --- 🔧 Asegurar que Python vea el paquete "backend_costeo" ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR.parent) not in sys.path:
    sys.path.append(str(BASE_DIR.parent))

# --- 🧠 Importaciones seguras según el entorno ---
try:
    # ✅ Cuando se ejecuta como parte del paquete
    from backend_costeo.database import engine, SessionLocal
    from backend_costeo.models import Base, Producto, CostoItem, CostoHistorial
except ModuleNotFoundError:
    # ✅ Cuando se ejecuta directamente o desde un .exe
    from database import engine, SessionLocal
    from models import Base, Producto, CostoItem, CostoHistorial


# --- 1️⃣ Detección del directorio base ---
if getattr(sys, 'frozen', False):
    # Cuando se ejecuta como .exe (PyInstaller)
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    # Cuando se ejecuta como script .py normal
    BASE_DIR = Path(__file__).resolve().parent

print(f"📁 Directorio base detectado: {BASE_DIR}")

DB_PATH = BASE_DIR / "costeo.db"
print(f"🗄️ Usando base de datos en: {DB_PATH}")


# --- 2️⃣ Crear tablas ---
print("🔄 Creando tablas si no existen...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()


# --- 3️⃣ Cargar productos ---
productos_path = BASE_DIR / "productos_catalogo.json"
if db.query(Producto).count() > 0:
    print("⚠️ Productos ya cargados, omitiendo esta sección.")
else:
    if productos_path.exists():
        print(f"📦 Importando productos desde {productos_path.name} ...")
        with open(productos_path, encoding="utf-8") as f:
            catalogo = json.load(f)

        count_prod = 0
        for linea, series in catalogo.items():  # 👈 "Control de acceso", "Parking", etc.
            for serie, productos in series.items():  # 👈 "GM-GS Series", "MC Series", etc.
                for p in productos:
                    # Asegurarse de usar "nombre" correctamente
                    nombre = p.get("nombre") or p.get("denominacion", "Sin nombre")

                    db.add(Producto(
                        codigo=p.get("codigo"),
                        nombre=nombre,              # ✅ ahora sí coincide con tu modelo
                        linea=linea,
                        serie=serie,
                        descripcion=nombre          # opcional, para completar el campo
                    ))
                    count_prod += 1

        db.commit()
        print(f"✅ {count_prod} productos importados correctamente.")
    else:
        print(f"⚠️ Archivo no encontrado: {productos_path}")


# --- 4️⃣ Cargar costos ---
costos_path = BASE_DIR / "costos_generales_full.json"
if db.query(CostoItem).count() > 0:
    print("⚠️ Ítems de costo ya cargados, omitiendo esta sección.")
else:
    if costos_path.exists():
        print(f"📦 Importando ítems de costo desde {costos_path.name} ...")
        with open(costos_path, encoding="utf-8") as f:
            costos = json.load(f)

        count_costos = 0
        for tipo, subtipos in costos.items():
            for subtipo, items in subtipos.items():
                for it in items:
                    costo = CostoItem(
                        tipo=tipo,
                        subtipo=subtipo,
                        item=it.get("item"),
                        codigo=it.get("codigo"),
                        denominacion=it.get("denominacion"),
                        unidad=it.get("unidad"),
                        costo_fabrica=it.get("costo_fabrica"),
                        costo_fob=it.get("costo_fob"),
                        coeficiente=it.get("coeficiente"),
                    )
                    db.add(costo)
                    db.flush()

                    # historial inicial
                    db.add(CostoHistorial(
                        costo_item_id=costo.id,
                        costo_fabrica=costo.costo_fabrica,
                        costo_fob=costo.costo_fob,
                        coeficiente=costo.coeficiente,
                    ))

                    count_costos += 1

        db.commit()
        print(f"✅ {count_costos} ítems de costo importados correctamente.")
    else:
        print(f"⚠️ Archivo no encontrado: {costos_path}")


db.close()
print("🎯 Base de datos inicializada correctamente.")
