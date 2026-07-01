# Dashboard KPIs Comerciales — Nexo Comercial S.A.

Stack: **Python · MySQL 8.0 · Power BI**

---

Proyecto de análisis y visualización de métricas comerciales para una distribuidora B2B ficticia.
Dos años de datos de ventas (2023–2024) modelados en esquema estrella sobre MySQL,
explorados con SQL y visualizados en un dashboard interactivo con 23 medidas DAX.

---

## Requisitos

- Python 3.10+
- MySQL Server 8.0+ corriendo localmente
- MySQL Workbench (para ejecutar las queries y explorar el modelo)
- Power BI Desktop

---

## Estructura

```
kpi-dashboard/
├── data/                         ← generado automáticamente (CSVs para Power BI)
├── sql/
│   ├── 01_star_schema.sql        ← DDL del modelo en MySQL
│   └── 02_queries_analisis.sql   ← 6 queries (CTEs + Window Functions)
├── powerbi/
│   └── kpi_dashboard.pbix        ← dashboard (ver guia_powerbi.md)
├── generar_datos.py
├── guia_powerbi.md               ← instrucciones Power BI + 23 medidas DAX + Service + RLS
├── requirements.txt
└── README.md
```

---

## Configuración

```bash
# 1. Instalar dependencias Python
pip install -r requirements.txt

# 2. Abrir generar_datos.py y cambiar MYSQL_PASSWORD por tu contraseña de root

# 3. Generar datos y cargar en MySQL
python generar_datos.py
```

Al terminar vas a ver:

```
Conectando a MySQL...
  Base de datos 'nexo_comercial' lista
Generando dimensiones...
Generando transacciones (15.000 filas)...

Cargando en MySQL...
  DimCalendario: 730 filas
  DimCliente: 500 filas
  DimProducto: 30 filas
  DimAgente: 15 filas
  FactVentas: 15.000 filas

Exportando CSVs para Power BI...
  ...

Base de datos: mysql://localhost/nexo_comercial
Listo.
```

---

## Esquema estrella

```
                    ┌──────────────────┐
                    │  DimCalendario   │
                    │  fecha (PK)      │
                    └────────┬─────────┘
                             │
 ┌──────────────┐   ┌────────┴────────┐   ┌──────────────┐
 │  DimCliente  │   │   FactVentas    │   │ DimProducto  │
 │  id_cliente  ├───┤  id_venta (PK)  ├───┤ id_producto  │
 │  segmento    │   │  fecha          │   │ categoria    │
 │  region...   │   │  id_cliente     │   │ precio_lista │
 └──────────────┘   │  id_producto    │   │ costo...     │
                    │  id_agente      │   └──────────────┘
 ┌──────────────┐   │  monto_total    │
 │  DimAgente   ├───┤  cantidad...    │
 │  id_agente   │   └─────────────────┘
 │  zona        │
 │  target...   │
 └──────────────┘
```

---

## SQL — Queries incluidas

| Query | Técnicas |
|---|---|
| Ventas MoM + YoY | `LAG`, CTE |
| Ranking agentes | `RANK`, `PARTITION BY` |
| Top productos por categoría | `RANK PARTITION`, share % |
| Segmentación RFM | `NTILE`, CTEs anidadas, `DATEDIFF` |
| Comparativa YTD | `SUM OVER ROWS UNBOUNDED`, `TIMESTAMPDIFF` |
| Cohort de retención | CTEs, `TIMESTAMPDIFF(MONTH, ...)` |

---

## Power BI

23 medidas DAX organizadas en 5 carpetas, dashboard de 5 páginas,
RLS por zona y publicado en Power BI Service.

Conexión a MySQL desde Power BI Desktop: requiere instalar
**MySQL Connector/NET 8.0** → https://dev.mysql.com/downloads/connector/net/

Ver todas las instrucciones en [`guia_powerbi.md`](guia_powerbi.md)

---

## Tecnologías

- Python 3.10+ · Pandas · NumPy · SQLAlchemy · PyMySQL
- MySQL 8.0 · MySQL Workbench
- Power BI Desktop + Power BI Service
- DAX (Data Analysis Expressions)

## Enlaces

- Dashboard interactivo (Power BI Service): https://app.powerbi.com/reportEmbed?reportId=13aabbbc-8eaf-4a67-9658-deb9febd38b3&autoAuth=true&ctid=e0a09e6c-a0b8-4459-a108-aba2c0ff8897
