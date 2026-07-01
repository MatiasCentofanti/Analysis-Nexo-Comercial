"""
Nexo Comercial S.A. — Generador de datos
Carga los datos en MySQL y exporta CSVs para Power BI.

Requisitos:
    pip install pandas numpy sqlalchemy pymysql

Antes de correr este script:
    1. Tener MySQL 8.0 corriendo
    2. Cambiar MYSQL_PASSWORD por tu contraseña de root
"""

import pandas as pd
import numpy as np
import random
import os
from sqlalchemy.engine import URL
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# ── CONFIGURACIÓN — cambiar solo MYSQL_PASSWORD ────────────────────────────────
MYSQL_USER     = "root"
MYSQL_PASSWORD = ""   # <-- acá va tu contraseña de MySQL
MYSQL_HOST     = "localhost"
MYSQL_PORT     = 3306
DB_NAME        = "nexo_comercial"
# ──────────────────────────────────────────────────────────────────────────────

np.random.seed(42)
random.seed(42)

os.makedirs("data", exist_ok=True)


def crear_db_si_no_existe():
    url = URL.create(
        drivername="mysql+pymysql",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
    )
    engine_sin_db = create_engine(url)
    with engine_sin_db.connect() as conn:
        conn.execute(text(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        ))
    print(f"  Base de datos '{DB_NAME}' lista")


def get_engine():
    url = URL.create(
        drivername="mysql+pymysql",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=DB_NAME,
        query={"charset": "utf8mb4"},
    )
    return create_engine(url)

# ── DIMENSIÓN CALENDARIO ───────────────────────────────────────────────────────

def crear_dim_calendario():
    MESES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    fechas = pd.date_range("2023-01-01", "2024-12-31", freq="D")
    cal = pd.DataFrame({"fecha": fechas})

    cal["anio"]            = cal["fecha"].dt.year
    cal["trimestre"]       = cal["fecha"].dt.quarter
    cal["trimestre_label"] = "Q" + cal["trimestre"].astype(str)
    cal["mes"]             = cal["fecha"].dt.month
    cal["nombre_mes"]      = cal["mes"].apply(lambda m: MESES[m - 1])
    cal["semana"]          = cal["fecha"].dt.isocalendar().week.astype(int)
    cal["dia"]             = cal["fecha"].dt.day
    cal["dia_semana_num"]  = cal["fecha"].dt.dayofweek
    cal["dia_semana"]      = cal["dia_semana_num"].apply(lambda d: DIAS[d])
    cal["es_fin_semana"]   = (cal["dia_semana_num"] >= 5).astype(int)
    cal["anio_mes"]        = (
        cal["anio"].astype(str) + "-" + cal["mes"].astype(str).str.zfill(2)
    )
    # MySQL DATE nativo (mejor que TEXT)
    cal["fecha"] = cal["fecha"].dt.date
    return cal


# ── DIMENSIÓN AGENTE ───────────────────────────────────────────────────────────

def crear_dim_agente():
    datos = [
        ("AG001", "Lucía Fernández",      "AMBA",      "Carlos Méndez",   280000, "2021-03-01"),
        ("AG002", "Martín Rodríguez",     "AMBA",      "Carlos Méndez",   260000, "2020-07-15"),
        ("AG003", "Paula González",       "AMBA",      "Carlos Méndez",   270000, "2022-01-10"),
        ("AG004", "Diego Martínez",       "AMBA",      "Carlos Méndez",   250000, "2021-09-01"),
        ("AG005", "Valentina López",      "Centro",    "Ana Suárez",      220000, "2020-03-15"),
        ("AG006", "Facundo Romero",       "Centro",    "Ana Suárez",      230000, "2022-06-01"),
        ("AG007", "Florencia Díaz",       "Centro",    "Ana Suárez",      210000, "2021-11-01"),
        ("AG008", "Ignacio Torres",       "NOA",       "Roberto Paz",     190000, "2020-01-15"),
        ("AG009", "Camila Ruiz",          "NOA",       "Roberto Paz",     185000, "2023-02-01"),
        ("AG010", "Sebastián Morales",    "NEA",       "Roberto Paz",     180000, "2022-08-01"),
        ("AG011", "Natalia Vargas",       "Patagonia", "Marcelo Ríos",    195000, "2021-05-15"),
        ("AG012", "Juan Pablo Herrera",   "Patagonia", "Marcelo Ríos",    200000, "2020-11-01"),
        ("AG013", "Sofía Castro",         "Cuyo",      "Marcelo Ríos",    205000, "2022-03-15"),
        ("AG014", "Lucas Peralta",        "Cuyo",      "Marcelo Ríos",    195000, "2023-01-10"),
        ("AG015", "Marina Ibáñez",        "AMBA",      "Carlos Méndez",   245000, "2021-07-01"),
    ]
    cols = ["id_agente", "nombre", "zona", "gerente", "target_mensual", "fecha_ingreso"]
    df = pd.DataFrame(datos, columns=cols)
    df["fecha_ingreso"] = pd.to_datetime(df["fecha_ingreso"]).dt.date
    return df


# ── DIMENSIÓN PRODUCTO ─────────────────────────────────────────────────────────

def crear_dim_producto():
    datos = [
        ("PR001", 'Laptop Pro 15"',        "Tecnología",   "Notebooks",      450000, 265000),
        ("PR002", 'Laptop Standard 14"',   "Tecnología",   "Notebooks",      280000, 163000),
        ("PR003", 'Monitor 27" 4K',        "Tecnología",   "Periféricos",    180000, 104000),
        ("PR004", 'Monitor 24" FHD',       "Tecnología",   "Periféricos",     95000,  54000),
        ("PR005", "Teclado Mecánico",      "Tecnología",   "Periféricos",     25000,  14000),
        ("PR006", "Mouse Inalámbrico",     "Tecnología",   "Periféricos",     12000,   6500),
        ("PR007", "Auriculares BT Pro",    "Tecnología",   "Audio",           35000,  19000),
        ("PR008", 'Tablet 10"',            "Tecnología",   "Tablets",        150000,  87000),
        ("PR009", "Proyector HD 3500lm",   "Tecnología",   "AV",             320000, 188000),
        ("PR010", "Hub USB-C 7 en 1",      "Tecnología",   "Periféricos",     18000,   9500),
        ("PR011", "Silla Ergonómica",      "Mobiliario",   "Asientos",       120000,  68000),
        ("PR012", "Escritorio Ejecutivo",  "Mobiliario",   "Escritorios",    180000, 100000),
        ("PR013", "Mesa de Reunión 8p",    "Mobiliario",   "Mesas",          350000, 200000),
        ("PR014", "Estantería Metálica",   "Mobiliario",   "Almacenamiento",  75000,  42000),
        ("PR015", "Armario con Llave",     "Mobiliario",   "Almacenamiento",  95000,  54000),
        ("PR016", "Resma Papel A4 x5",     "Papelería",    "Papel",            8500,   4200),
        ("PR017", "Carpeta Archivadora",   "Papelería",    "Archivos",         3200,   1500),
        ("PR018", "Set Bolígrafos x20",    "Papelería",    "Escritura",        2800,   1300),
        ("PR019", "Agenda Ejecutiva",      "Papelería",    "Organizadores",    4500,   2100),
        ("PR020", "Papel Afiche x50",      "Papelería",    "Papel",            6000,   2900),
        ("PR021", "Impresora Láser B/N",   "Equipamiento", "Impresión",      180000, 104000),
        ("PR022", "Impresora Color",       "Equipamiento", "Impresión",      250000, 147000),
        ("PR023", "Escáner Documental",    "Equipamiento", "Escaneo",        120000,  70000),
        ("PR024", "Cámara IP HD",          "Equipamiento", "Seguridad",       45000,  25000),
        ("PR025", "Teléfono IP",           "Equipamiento", "Comunicación",    28000,  15000),
        ("PR026", "Tóner Negro HP",        "Consumibles",  "Tóner",           22000,  11000),
        ("PR027", "Cartucho Color Epson",  "Consumibles",  "Cartuchos",        8500,   4000),
        ("PR028", "Resma Color A4",        "Consumibles",  "Papel",           12000,   5800),
        ("PR029", "Pila AA x20",           "Consumibles",  "Pilas",            3500,   1600),
        ("PR030", "Cable HDMI 2m",         "Consumibles",  "Cables",           4500,   2100),
    ]
    cols = ["id_producto", "nombre", "categoria", "subcategoria", "precio_lista", "costo"]
    return pd.DataFrame(datos, columns=cols)


# ── DIMENSIÓN CLIENTE ──────────────────────────────────────────────────────────

def crear_dim_cliente():
    prefijos = [
        "Grupo", "Constructora", "Consultora", "Servicios", "Distribuidora",
        "Comercial", "Inversiones", "Clínica", "Estudio", "Metalúrgica"
    ]
    cuerpos = [
        "García", "Rodríguez", "López", "Martínez", "González", "Pérez",
        "Sánchez", "Romero", "Torres", "Álvarez", "Morales", "Ruiz",
        "Castro", "Herrera", "Díaz", "Molina", "Ortega", "Medina"
    ]
    sufijos = [
        "S.A.", "S.R.L.", "& Asociados", "Unida S.A.", "del Plata S.R.L.",
        "Central", "Patagónica S.A.", "Andina S.R.L.", "del Norte", "e Hijos"
    ]
    regiones_ciudades = {
        "AMBA":      ["Buenos Aires", "La Plata", "Mar del Plata", "Quilmes", "Lanús"],
        "Centro":    ["Córdoba", "Rosario", "Santa Fe", "Paraná", "Río Cuarto"],
        "NOA":       ["Tucumán", "Salta", "Jujuy", "Santiago del Estero", "Catamarca"],
        "NEA":       ["Resistencia", "Corrientes", "Posadas", "Formosa", "Oberá"],
        "Patagonia": ["Neuquén", "Bariloche", "Comodoro Rivadavia", "Ushuaia", "Trelew"],
        "Cuyo":      ["Mendoza", "San Juan", "San Luis", "Villa Mercedes", "San Rafael"],
    }
    seg_region = {
        "AMBA":      {"Premium": 0.20, "B2B": 0.55, "B2C": 0.25},
        "Centro":    {"Premium": 0.12, "B2B": 0.58, "B2C": 0.30},
        "NOA":       {"Premium": 0.05, "B2B": 0.55, "B2C": 0.40},
        "NEA":       {"Premium": 0.03, "B2B": 0.52, "B2C": 0.45},
        "Patagonia": {"Premium": 0.08, "B2B": 0.57, "B2C": 0.35},
        "Cuyo":      {"Premium": 0.07, "B2B": 0.58, "B2C": 0.35},
    }
    filas = []
    for i in range(1, 501):
        region = random.choices(
            list(regiones_ciudades.keys()),
            weights=[0.40, 0.22, 0.12, 0.08, 0.10, 0.08]
        )[0]
        ciudad    = random.choice(regiones_ciudades[region])
        pesos_seg = seg_region[region]
        segmento  = random.choices(list(pesos_seg.keys()), weights=list(pesos_seg.values()))[0]
        nombre    = f"{random.choice(prefijos)} {random.choice(cuerpos)} {random.choice(sufijos)}"
        fecha_alta = (datetime(2019, 1, 1) + timedelta(days=random.randint(0, 365 * 4))).date()
        filas.append((f"CL{i:04d}", nombre, segmento, ciudad, region, fecha_alta))

    return pd.DataFrame(
        filas, columns=["id_cliente", "nombre", "segmento", "ciudad", "region", "fecha_alta"]
    )


# ── FACT VENTAS ────────────────────────────────────────────────────────────────

def crear_fact_ventas(dim_cal, dim_cli, dim_prod, dim_agente):
    fechas = pd.to_datetime(dim_cal["fecha"])

    peso_mes = {
        1: 0.70, 2: 0.70, 3: 0.80, 4: 0.85, 5: 0.88,
        6: 0.90, 7: 0.80, 8: 0.82, 9: 0.88, 10: 1.05,
        11: 1.25, 12: 1.40
    }
    pesos_fecha = np.array([
        peso_mes[d.month]
        * (1.15 if d.year == 2024 else 1.0)
        * (0.0  if d.dayofweek >= 5 else 1.0)
        for d in fechas
    ])
    pesos_fecha = pesos_fecha / pesos_fecha.sum()

    pesos_agente = np.array([
        3.8, 3.2, 2.9, 2.2, 2.1, 1.9, 1.6,
        1.5, 1.2, 1.2, 1.0, 1.0, 1.0, 0.75, 0.75
    ])
    pesos_agente = pesos_agente / pesos_agente.sum()

    peso_cat = {
        "Consumibles": 4.0, "Papelería": 3.5,
        "Tecnología": 2.0, "Equipamiento": 1.5, "Mobiliario": 1.0
    }
    pesos_prod = dim_prod["categoria"].map(peso_cat).values
    pesos_prod = pesos_prod / pesos_prod.sum()

    peso_seg = {"Premium": 4.5, "B2B": 2.0, "B2C": 1.0}
    pesos_cli = dim_cli["segmento"].map(peso_seg).values
    pesos_cli = pesos_cli / pesos_cli.sum()

    N = 15000
    idx_f = np.random.choice(len(fechas),     size=N, p=pesos_fecha)
    idx_a = np.random.choice(len(dim_agente), size=N, p=pesos_agente)
    idx_p = np.random.choice(len(dim_prod),   size=N, p=pesos_prod)
    idx_c = np.random.choice(len(dim_cli),    size=N, p=pesos_cli)

    tipos_pago   = ["Transferencia", "Tarjeta de crédito", "Cheque", "Efectivo"]
    pesos_pago   = [0.42, 0.30, 0.20, 0.08]

    filas = []
    for i in range(N):
        prod   = dim_prod.iloc[idx_p[i]]
        cli    = dim_cli.iloc[idx_c[i]]
        agente = dim_agente.iloc[idx_a[i]]
        fecha  = fechas[idx_f[i]].date()

        if prod["categoria"] in ("Consumibles", "Papelería"):
            cantidad = int(np.random.choice([1, 2, 3, 5, 10, 20], p=[0.15, 0.20, 0.25, 0.20, 0.15, 0.05]))
        elif prod["categoria"] in ("Tecnología", "Equipamiento"):
            cantidad = int(np.random.choice([1, 2, 3], p=[0.70, 0.20, 0.10]))
        else:
            cantidad = int(np.random.choice([1, 2, 3, 5], p=[0.50, 0.25, 0.15, 0.10]))

        if   cantidad >= 20: descuento = 0.15
        elif cantidad >= 10: descuento = 0.10
        elif cantidad >=  5: descuento = 0.05
        else:                descuento = 0.00

        precio_unitario = prod["precio_lista"] * (1 - descuento) * np.random.uniform(0.95, 1.05)
        monto_total     = round(precio_unitario * cantidad, 2)
        precio_unitario = round(precio_unitario, 2)
        tipo_pago       = random.choices(tipos_pago, weights=pesos_pago)[0]
        estado          = random.choices(["Completada", "Anulada"], weights=[0.965, 0.035])[0]

        filas.append({
            "id_venta":        f"VT{i + 1:06d}",
            "fecha":           fecha,
            "id_cliente":      cli["id_cliente"],
            "id_producto":     prod["id_producto"],
            "id_agente":       agente["id_agente"],
            "zona":            agente["zona"],
            "cantidad":        cantidad,
            "precio_unitario": precio_unitario,
            "descuento_pct":   descuento,
            "monto_total":     monto_total,
            "tipo_pago":       tipo_pago,
            "estado":          estado,
        })

    return pd.DataFrame(filas)


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    print("Conectando a MySQL...")
    crear_db_si_no_existe()
    engine = get_engine()

    print("Generando dimensiones...")
    dim_cal    = crear_dim_calendario()
    dim_agente = crear_dim_agente()
    dim_prod   = crear_dim_producto()
    dim_cli    = crear_dim_cliente()

    print("Generando transacciones (15.000 filas)...")
    fact_ventas = crear_fact_ventas(dim_cal, dim_cli, dim_prod, dim_agente)

    tablas = {
        "DimCalendario": dim_cal,
        "DimCliente":    dim_cli,
        "DimProducto":   dim_prod,
        "DimAgente":     dim_agente,
        "FactVentas":    fact_ventas,
    }

    # ── Cargar en MySQL ───────────────────────────────────────────────────────
    print("\nCargando en MySQL...")
    for nombre, df in tablas.items():
        df.to_sql(nombre, engine, if_exists="replace", index=False)
        print(f"  {nombre}: {len(df):,} filas")

    # ── Exportar CSVs para Power BI ───────────────────────────────────────────
    print("\nExportando CSVs para Power BI...")
    for nombre, df in tablas.items():
        path = f"data/{nombre}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  {path}")

    # ── Resumen ───────────────────────────────────────────────────────────────
    completadas = fact_ventas[fact_ventas["estado"] == "Completada"]
    print("\n=== RESUMEN ===")
    print(f"Total ventas    : $ {completadas['monto_total'].sum():,.0f}")
    print(f"Transacciones   : {len(completadas):,}")
    print(f"Ticket promedio : $ {completadas['monto_total'].mean():,.0f}")
    print(f"Ventas 2023     : $ {completadas[completadas['fecha'] < datetime(2024,1,1).date()]['monto_total'].sum():,.0f}")
    print(f"Ventas 2024     : $ {completadas[completadas['fecha'] >= datetime(2024,1,1).date()]['monto_total'].sum():,.0f}")
    print(f"\nBase de datos   : mysql://localhost/{DB_NAME}")
    print("Listo.")


if __name__ == "__main__":
    main()
