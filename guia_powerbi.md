# Guía Power BI — Dashboard KPIs Comerciales
### Nexo Comercial S.A.

---

## PASO 1 — Conectar los datos

Hay dos opciones. La **Opción A (MySQL directo)** es la que queda mejor para mostrar
en una entrevista porque conectás Power BI a un motor de base de datos real.

### Opción A — Conectar Power BI a MySQL (recomendada)

Antes de conectar, instalar el conector:
→ Descargar **MySQL Connector/NET 8.0** desde: https://dev.mysql.com/downloads/connector/net/

Después en Power BI Desktop:
1. **Inicio → Obtener datos → Base de datos MySQL**
2. Servidor: `localhost`
3. Base de datos: `nexo_comercial`
4. Modo de conectividad: **Importar**
5. Credenciales: usuario `root` + tu contraseña
6. En el navegador que aparece, seleccionar las 5 tablas con Ctrl+clic:
   `DimCalendario`, `DimCliente`, `DimProducto`, `DimAgente`, `FactVentas`
7. Clic en **Cargar**

### Opción B — Conectar desde los CSVs (más simple)

Si no podés instalar el conector MySQL:
1. **Inicio → Obtener datos → Texto o CSV**
2. Cargar los 5 archivos de `/data/` de a uno
3. Clic en **Cargar** en cada uno

---

## PASO 2 — Configurar el modelo (Vista Modelo)

Ir a **Vista Modelo** (ícono de tres tablas a la izquierda).

Crear estas relaciones arrastrando campo a campo:

| Desde (Many) | Hacia (One) | Cardinalidad |
|---|---|---|
| `FactVentas[fecha]` | `DimCalendario[fecha]` | Muchos a uno |
| `FactVentas[id_cliente]` | `DimCliente[id_cliente]` | Muchos a uno |
| `FactVentas[id_producto]` | `DimProducto[id_producto]` | Muchos a uno |
| `FactVentas[id_agente]` | `DimAgente[id_agente]` | Muchos a uno |

Dirección del filtro: **Único** en todas (de dimensión hacia hecho).

---

## PASO 3 — Columna calculada en DimCalendario

En la tabla `DimCalendario`, crear esta columna calculada
(clic derecho sobre la tabla → Nueva columna):

```dax
Fecha Completa = DATE(DimCalendario[anio], DimCalendario[mes], DimCalendario[dia])
```

Después marcar `DimCalendario[Fecha Completa]` como **tabla de fechas**:
Herramientas de tabla → Marcar como tabla de fechas → columna: `Fecha Completa`

Esto activa las funciones de inteligencia de tiempo (TOTALYTD, PREVIOUSMONTH, etc.)

---

## PASO 4 — Medidas DAX

Crear una tabla vacía para organizar las medidas:
**Modelado → Nueva tabla** → escribir: `_Medidas = {0}`

Hacer clic derecho sobre `_Medidas` → **Nueva medida** para cada una.

---

### 📁 Carpeta: Ventas Básicas

```dax
Total Ventas =
CALCULATE(
    SUM(FactVentas[monto_total]),
    FactVentas[estado] = "Completada"
)
```

```dax
Total Transacciones =
CALCULATE(
    COUNTROWS(FactVentas),
    FactVentas[estado] = "Completada"
)
```

```dax
Ticket Promedio =
DIVIDE([Total Ventas], [Total Transacciones])
```

```dax
Clientes Únicos =
CALCULATE(
    DISTINCTCOUNT(FactVentas[id_cliente]),
    FactVentas[estado] = "Completada"
)
```

```dax
Unidades Vendidas =
CALCULATE(
    SUM(FactVentas[cantidad]),
    FactVentas[estado] = "Completada"
)
```

---

### 📁 Carpeta: Tiempo

```dax
Ventas YTD =
TOTALYTD(
    [Total Ventas],
    DimCalendario[Fecha Completa]
)
```

```dax
Ventas MTD =
TOTALMTD(
    [Total Ventas],
    DimCalendario[Fecha Completa]
)
```

```dax
Ventas QTD =
TOTALQTD(
    [Total Ventas],
    DimCalendario[Fecha Completa]
)
```

```dax
Ventas Mes Anterior =
CALCULATE(
    [Total Ventas],
    PREVIOUSMONTH(DimCalendario[Fecha Completa])
)
```

```dax
Ventas Mismo Mes Año Ant =
CALCULATE(
    [Total Ventas],
    SAMEPERIODLASTYEAR(DimCalendario[Fecha Completa])
)
```

```dax
YTD Año Anterior =
CALCULATE(
    [Ventas YTD],
    SAMEPERIODLASTYEAR(DimCalendario[Fecha Completa])
)
```

---

### 📁 Carpeta: Variaciones

```dax
Var MoM $ =
[Total Ventas] - [Ventas Mes Anterior]
```

```dax
Var MoM % =
DIVIDE([Var MoM $], [Ventas Mes Anterior])
```

```dax
Var YoY $ =
[Total Ventas] - [Ventas Mismo Mes Año Ant]
```

```dax
Var YoY % =
DIVIDE([Var YoY $], [Ventas Mismo Mes Año Ant])
```

```dax
Crecimiento YTD % =
DIVIDE([Ventas YTD] - [YTD Año Anterior], [YTD Año Anterior])
```

---

### 📁 Carpeta: Márgenes

```dax
Costo Total =
CALCULATE(
    SUMX(
        FactVentas,
        FactVentas[cantidad] * RELATED(DimProducto[costo])
    ),
    FactVentas[estado] = "Completada"
)
```

```dax
Margen Bruto =
[Total Ventas] - [Costo Total]
```

```dax
Margen % =
DIVIDE([Margen Bruto], [Total Ventas])
```

---

### 📁 Carpeta: Agentes

```dax
Ventas Prom Mensual =
DIVIDE(
    [Total Ventas],
    DISTINCTCOUNT(DimCalendario[anio_mes])
)
```

```dax
Target Mensual Agente =
AVERAGEX(
    VALUES(DimAgente[nombre]),
    DimAgente[target_mensual]
)
```

```dax
Cumplimiento Target % =
DIVIDE([Ventas Prom Mensual], [Target Mensual Agente])
```

```dax
Ranking Agente =
RANKX(
    ALL(DimAgente[nombre]),
    [Total Ventas],
    ,
    DESC,
    DENSE
)
```

---

### 📁 Carpeta: Clientes

```dax
Valor Promedio Cliente =
DIVIDE([Total Ventas], [Clientes Únicos])
```

```dax
Tasa Anulación % =
DIVIDE(
    CALCULATE(COUNTROWS(FactVentas), FactVentas[estado] = "Anulada"),
    COUNTROWS(FactVentas)
)
```

---

## PASO 5 — Formatear las medidas

Seleccionar cada medida y asignar el formato correcto:

| Medida | Formato |
|---|---|
| Total Ventas, Margen Bruto, Costo Total | Moneda → $ Español (Argentina) → 0 decimales |
| Ticket Promedio, Valor Promedio Cliente | Moneda → 0 decimales |
| Var MoM %, Var YoY %, Margen %, Cumplimiento %, etc. | Porcentaje → 1 decimal |
| Ranking Agente | Número entero → 0 decimales |

---

## PASO 6 — Construir el dashboard (5 páginas)

### Página 1 — Resumen Ejecutivo

**Renombrar** la página: doble clic en la pestaña → "Resumen Ejecutivo"

Agregar estos visuales:

**Fila superior — 5 tarjetas KPI:**
- Tarjeta: `[Total Ventas]`
- Tarjeta: `[Total Transacciones]`
- Tarjeta: `[Ticket Promedio]`
- Tarjeta: `[Margen %]`
- Tarjeta: `[Clientes Únicos]`

**Centro izquierda — Gráfico de líneas:**
- Visual: Gráfico de líneas
- Eje X: `DimCalendario[anio_mes]`
- Valores: `[Total Ventas]` y `[Ventas Mismo Mes Año Ant]`
- Título: "Ventas Mensuales 2023 vs 2024"

**Centro derecha — Gráfico de barras:**
- Visual: Gráfico de barras agrupadas
- Eje Y: `DimProducto[categoria]`
- Valores: `[Total Ventas]`
- Ordenar: de mayor a menor

**Abajo izquierda — Treemap zonas:**
- Visual: Treemap
- Categoría: `DimAgente[zona]`
- Valores: `[Total Ventas]`

**Abajo derecha — Tabla resumen:**
- Visual: Tabla
- Columnas: `DimCalendario[anio]`, `[Total Ventas]`, `[Var YoY %]`, `[Margen %]`

**Slicers (segmentaciones):**
- Slicer: `DimCalendario[anio]` → estilo Botones
- Slicer: `DimCalendario[trimestre_label]` → estilo Lista desplegable

---

### Página 2 — Performance de Agentes

**Matriz principal:**
- Visual: Matriz
- Filas: `DimAgente[nombre]`, `DimAgente[zona]`
- Valores: `[Total Ventas]`, `[Ventas Prom Mensual]`, `[Target Mensual Agente]`, `[Cumplimiento Target %]`, `[Ranking Agente]`
- En Cumplimiento Target %: Formato condicional → escala de color (rojo < 80%, verde > 100%)

**Gráfico de barras horizontal:**
- Visual: Gráfico de barras horizontales
- Eje Y: `DimAgente[nombre]`
- Valores: `[Total Ventas]`
- Línea constante: agregar línea de referencia con el valor del target

**Gauge (indicador):**
- Visual: Medidor
- Valor: `[Cumplimiento Target %]`
- Mínimo: 0, Máximo: 1.5 (150%)
- Destino: 1 (100%)

**Slicers:**
- `DimAgente[zona]`
- `DimAgente[gerente]`
- `DimCalendario[anio_mes]` → estilo entre

---

### Página 3 — Análisis de Productos

**Treemap:**
- Categoría: `DimProducto[categoria]`
- Detalles: `DimProducto[subcategoria]`
- Valores: `[Total Ventas]`

**Gráfico de dispersión:**
- Eje X: `DimProducto[precio_lista]`
- Eje Y: `[Margen %]`
- Tamaño del burbujeo: `[Total Ventas]`
- Leyenda: `DimProducto[categoria]`
- Título: "Precio vs Margen por Producto"

**Gráfico de barras — Top 10 productos:**
- Eje Y: `DimProducto[nombre]`
- Valores: `[Total Ventas]`
- Filtro: Top N → 10 por `[Total Ventas]`

**Slicer:**
- `DimProducto[categoria]`

---

### Página 4 — Clientes

**3 tarjetas KPI:**
- `[Clientes Únicos]`
- `[Valor Promedio Cliente]`
- `[Tasa Anulación %]`

**Gráfico de barras — Por segmento:**
- Eje X: `DimCliente[segmento]`
- Valores: `[Total Ventas]`, `[Clientes Únicos]`

**Gráfico de barras — Por región:**
- Eje X: `DimCliente[region]`
- Valores: `[Total Ventas]`

**Tabla detalle:**
- Columnas: `DimCliente[segmento]`, `DimCliente[region]`, `[Total Ventas]`, `[Clientes Únicos]`, `[Ticket Promedio]`

---

### Página 5 — Tendencias

**Gráfico de área — YTD comparativo:**
- Eje X: `DimCalendario[mes]`
- Valores: `[Ventas YTD]` y `[YTD Año Anterior]`
- Leyenda: automática

**Gráfico de columnas — Variación MoM %:**
- Eje X: `DimCalendario[anio_mes]`
- Valores: `[Var MoM %]`
- Formato condicional: barras rojas si negativo

**4 tarjetas KPI:**
- `[Ventas YTD]`
- `[Crecimiento YTD %]`
- `[Var MoM %]`
- `[Var YoY %]`

**Slicer:**
- `DimCalendario[anio]` → 2023 / 2024

---

## PASO 7 — Row Level Security (RLS)

Esto permite que cada gerente vea solo los datos de su zona.

### Crear los roles

En Power BI Desktop:
**Modelado → Administrar roles → Nuevo rol**

Crear uno por zona con esta lógica:

**Rol: AMBA**
```dax
[zona] = "AMBA"
```
Aplicar sobre la tabla: `FactVentas`

**Rol: Centro**
```dax
[zona] = "Centro"
```

**Rol: NOA_NEA**
```dax
[zona] = "NOA" || [zona] = "NEA"
```

**Rol: Patagonia_Cuyo**
```dax
[zona] = "Patagonia" || [zona] = "Cuyo"
```

**Rol: Gerencia_General** (ve todo — sin filtro DAX, dejar vacío)

### Probar los roles antes de publicar

**Modelado → Ver como → seleccionar un rol**
Verificar que los visuales muestren solo los datos del rol seleccionado.

---

## PASO 8 — Publicar en Power BI Service

### 8.1 Publicar desde Desktop

1. **Inicio → Publicar**
2. Iniciar sesión con cuenta Microsoft (puede ser cuenta gratuita de Outlook)
3. Seleccionar destino: **Mi área de trabajo**
4. Esperar confirmación → clic en el enlace para abrir en el navegador

### 8.2 Configurar RLS en el Service

1. Ir a **app.powerbi.com**
2. En **Mi área de trabajo** → buscar el Dataset (no el Report)
3. Clic en los tres puntos `...` → **Seguridad**
4. Para cada rol creado, agregar el email del usuario correspondiente:
   - Rol AMBA → agregar el email del gerente de AMBA
   - Rol Centro → agregar el email del gerente de Centro
   - etc.
5. Clic en **Guardar**

### 8.3 Compartir el dashboard (opción gratuita)

Para portfolio y para que lo vea un recruiter sin necesidad de cuenta Pro:

1. Abrir el **Report** (no el dataset) en app.powerbi.com
2. Clic en **Archivo → Insertar informe → Publicar en web (público)**
3. Clic en **Crear código de inserción**
4. Copiar el enlace y pegarlo en el README de GitHub

> ⚠️ "Publicar en web" hace el report público y visible para cualquiera.
> Solo usarlo con datos ficticios como en este proyecto. Nunca con datos reales.

### 8.4 Alternativa: captura para el CV

Si no querés dejar el report público:
1. Sacar capturas de cada página del dashboard
2. Subirlas a la carpeta `/powerbi/screenshots/` del repo
3. Referenciarlas en el README con `![Dashboard](powerbi/screenshots/pag1.png)`

---

## Checklist final antes de mandarlo al GitHub

- [ ] `python generar_datos.py` corrió sin errores
- [ ] Los 5 CSVs están en `/data/`
- [ ] El modelo en Power BI tiene las 4 relaciones configuradas
- [ ] `DimCalendario[Fecha Completa]` está marcada como tabla de fechas
- [ ] Las 23 medidas DAX están creadas y con formato correcto
- [ ] Las 5 páginas del dashboard están construidas
- [ ] RLS configurado y probado con "Ver como"
- [ ] Publicado en Power BI Service
- [ ] Link del report (o screenshots) en el README
- [ ] `git push` al repositorio
