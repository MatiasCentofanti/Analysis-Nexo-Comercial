-- =============================================================================
-- Nexo Comercial S.A. — Queries de análisis
-- Motor: MySQL 8.0+
-- Cubre: CTEs, Window Functions (LAG, RANK, NTILE, SUM OVER), JOINs
-- =============================================================================

USE nexo_comercial;


-- ── QUERY 1: Ventas mensuales con variación MoM y YoY ────────────────────────
-- Técnicas: CTE, LAG() Window Function

WITH ventas_mes AS (
    SELECT
        DATE_FORMAT(v.fecha, '%Y-%m')    AS anio_mes,
        YEAR(v.fecha)                    AS anio,
        MONTH(v.fecha)                   AS mes,
        c.nombre_mes,
        SUM(v.monto_total)               AS ventas_total,
        COUNT(*)                         AS transacciones,
        COUNT(DISTINCT v.id_cliente)     AS clientes_unicos,
        ROUND(AVG(v.monto_total), 0)     AS ticket_promedio
    FROM FactVentas v
    JOIN DimCalendario c ON v.fecha = c.fecha
    WHERE v.estado = 'Completada'
    GROUP BY DATE_FORMAT(v.fecha, '%Y-%m'), YEAR(v.fecha), MONTH(v.fecha), c.nombre_mes
),
con_lag AS (
    SELECT *,
        LAG(ventas_total, 1)  OVER (ORDER BY anio_mes) AS ventas_mes_anterior,
        LAG(ventas_total, 12) OVER (ORDER BY anio_mes) AS ventas_mismo_mes_anio_ant
    FROM ventas_mes
)
SELECT
    anio_mes,
    nombre_mes,
    anio,
    ROUND(ventas_total, 0)                                                          AS ventas_total,
    transacciones,
    clientes_unicos,
    ticket_promedio,
    ROUND(ventas_mes_anterior, 0)                                                   AS mes_anterior,
    ROUND((ventas_total - ventas_mes_anterior) / ventas_mes_anterior * 100, 2)      AS variacion_mom_pct,
    ROUND((ventas_total - ventas_mismo_mes_anio_ant) / ventas_mismo_mes_anio_ant * 100, 2) AS variacion_yoy_pct
FROM con_lag
ORDER BY anio_mes;


-- ── QUERY 2: Ranking de agentes con cumplimiento de target ───────────────────
-- Técnicas: CTE, RANK() global y por zona (PARTITION BY), JOIN

WITH ventas_agente_mes AS (
    SELECT
        v.id_agente,
        DATE_FORMAT(v.fecha, '%Y-%m') AS anio_mes,
        SUM(v.monto_total)            AS ventas_mes
    FROM FactVentas v
    WHERE v.estado = 'Completada'
    GROUP BY v.id_agente, DATE_FORMAT(v.fecha, '%Y-%m')
),
resumen AS (
    SELECT
        a.id_agente,
        a.nombre                           AS agente,
        a.zona,
        a.gerente,
        a.target_mensual,
        ROUND(SUM(m.ventas_mes), 0)        AS ventas_total,
        ROUND(AVG(m.ventas_mes), 0)        AS ventas_prom_mensual,
        COUNT(m.anio_mes)                  AS meses_con_ventas
    FROM ventas_agente_mes m
    JOIN DimAgente a ON m.id_agente = a.id_agente
    GROUP BY a.id_agente, a.nombre, a.zona, a.gerente, a.target_mensual
)
SELECT
    agente,
    zona,
    gerente,
    ventas_total,
    ventas_prom_mensual,
    target_mensual,
    ROUND(ventas_prom_mensual / target_mensual * 100, 1)              AS cumplimiento_pct,
    RANK()       OVER (ORDER BY ventas_total DESC)                    AS ranking_general,
    RANK()       OVER (PARTITION BY zona ORDER BY ventas_total DESC)  AS ranking_en_zona,
    DENSE_RANK() OVER (ORDER BY ROUND(ventas_prom_mensual / target_mensual, 4) DESC) AS ranking_cumplimiento
FROM resumen
ORDER BY ranking_general;


-- ── QUERY 3: Top 3 productos por categoría ───────────────────────────────────
-- Técnicas: CTE, RANK() con PARTITION BY, share del total

WITH ventas_prod AS (
    SELECT
        p.id_producto,
        p.nombre                                        AS producto,
        p.categoria,
        p.subcategoria,
        SUM(v.monto_total)                              AS ingresos_total,
        SUM(v.cantidad)                                 AS unidades,
        SUM(v.monto_total) - SUM(v.cantidad * p.costo) AS margen_bruto,
        COUNT(DISTINCT v.id_cliente)                    AS clientes_unicos
    FROM FactVentas v
    JOIN DimProducto p ON v.id_producto = p.id_producto
    WHERE v.estado = 'Completada'
    GROUP BY p.id_producto, p.nombre, p.categoria, p.subcategoria
),
con_ranking AS (
    SELECT *,
        RANK() OVER (PARTITION BY categoria ORDER BY ingresos_total DESC) AS rank_cat,
        ROUND(margen_bruto / ingresos_total * 100, 1)                    AS margen_pct,
        ROUND(ingresos_total / SUM(ingresos_total) OVER () * 100, 2)     AS share_total_pct
    FROM ventas_prod
)
SELECT
    categoria,
    producto,
    subcategoria,
    ROUND(ingresos_total, 0) AS ingresos_total,
    unidades,
    margen_pct,
    share_total_pct,
    clientes_unicos,
    rank_cat
FROM con_ranking
WHERE rank_cat <= 3
ORDER BY categoria, rank_cat;


-- ── QUERY 4: Segmentación RFM de clientes ────────────────────────────────────
-- Técnicas: CTEs anidadas, NTILE, CASE WHEN, DATEDIFF

WITH fecha_tope AS (
    SELECT MAX(fecha) AS ultima FROM FactVentas WHERE estado = 'Completada'
),
rfm_base AS (
    SELECT
        c.id_cliente,
        c.nombre,
        c.segmento,
        c.region,
        COUNT(*)                                                    AS frecuencia,
        ROUND(SUM(v.monto_total), 0)                               AS valor_total,
        ROUND(AVG(v.monto_total), 0)                               AS ticket_promedio,
        MAX(v.fecha)                                               AS ultima_compra,
        DATEDIFF((SELECT ultima FROM fecha_tope), MAX(v.fecha))    AS dias_sin_comprar
    FROM FactVentas v
    JOIN DimCliente c ON v.id_cliente = c.id_cliente
    WHERE v.estado = 'Completada'
    GROUP BY c.id_cliente, c.nombre, c.segmento, c.region
),
con_quintiles AS (
    SELECT *,
        NTILE(4) OVER (ORDER BY frecuencia        DESC) AS q_frecuencia,
        NTILE(4) OVER (ORDER BY valor_total       DESC) AS q_valor,
        NTILE(4) OVER (ORDER BY dias_sin_comprar      ) AS q_recencia
    FROM rfm_base
),
clasificados AS (
    SELECT *,
        CASE
            WHEN q_recencia = 1 AND q_frecuencia = 1 AND q_valor = 1 THEN 'Champions'
            WHEN q_valor <= 2 AND q_recencia <= 2                    THEN 'Leales de Alto Valor'
            WHEN q_recencia = 1 AND q_frecuencia >= 3               THEN 'Nuevos Prometedores'
            WHEN q_frecuencia >= 3 AND q_recencia >= 3              THEN 'En Riesgo'
            WHEN q_recencia = 4                                     THEN 'Perdidos'
            ELSE                                                         'Potenciales'
        END AS segmento_rfm
    FROM con_quintiles
)
SELECT
    segmento_rfm,
    COUNT(*)                        AS cantidad_clientes,
    ROUND(AVG(valor_total), 0)      AS valor_prom,
    ROUND(AVG(frecuencia), 1)       AS frecuencia_prom,
    ROUND(AVG(dias_sin_comprar), 0) AS dias_inactividad_prom,
    ROUND(SUM(valor_total), 0)      AS valor_total_segmento,
    ROUND(
        SUM(valor_total) / SUM(SUM(valor_total)) OVER () * 100, 2
    )                               AS share_revenue_pct
FROM clasificados
GROUP BY segmento_rfm
ORDER BY valor_total_segmento DESC;


-- ── QUERY 5: Comparativa YTD 2023 vs 2024 ───────────────────────────────────
-- Técnicas: CTE, SUM() OVER con ROWS UNBOUNDED PRECEDING, LEFT JOIN

WITH ventas_x_mes AS (
    SELECT
        YEAR(fecha)                  AS anio,
        MONTH(fecha)                 AS mes,
        SUM(monto_total)             AS ventas_mes
    FROM FactVentas
    WHERE estado = 'Completada'
    GROUP BY YEAR(fecha), MONTH(fecha)
),
acumulado AS (
    SELECT
        anio,
        mes,
        ventas_mes,
        SUM(ventas_mes) OVER (
            PARTITION BY anio
            ORDER BY mes
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS ytd
    FROM ventas_x_mes
)
SELECT
    a24.mes,
    ROUND(a24.ventas_mes, 0)                                           AS ventas_2024,
    ROUND(a23.ventas_mes, 0)                                           AS ventas_2023,
    ROUND((a24.ventas_mes - a23.ventas_mes) / a23.ventas_mes * 100, 2) AS crecimiento_mes_pct,
    ROUND(a24.ytd, 0)                                                  AS ytd_2024,
    ROUND(a23.ytd, 0)                                                  AS ytd_2023,
    ROUND((a24.ytd - a23.ytd) / a23.ytd * 100, 2)                     AS crecimiento_ytd_pct
FROM acumulado a24
LEFT JOIN acumulado a23
    ON a24.mes = a23.mes AND a23.anio = 2023
WHERE a24.anio = 2024
ORDER BY a24.mes;


-- ── QUERY 6: Cohort de retención (primeros 12 meses) ─────────────────────────
-- Técnicas: CTEs encadenadas, TIMESTAMPDIFF, PERIOD_DIFF

WITH primera_compra AS (
    SELECT
        id_cliente,
        MIN(fecha)                                           AS primera_fecha,
        DATE_FORMAT(MIN(fecha), '%Y-%m')                    AS cohorte
    FROM FactVentas
    WHERE estado = 'Completada'
    GROUP BY id_cliente
),
actividad AS (
    SELECT
        v.id_cliente,
        p.cohorte,
        DATE_FORMAT(v.fecha, '%Y-%m')                        AS mes_compra,
        TIMESTAMPDIFF(MONTH, p.primera_fecha, v.fecha)       AS mes_desde_primera_compra
    FROM FactVentas v
    JOIN primera_compra p ON v.id_cliente = p.id_cliente
    WHERE v.estado = 'Completada'
),
tamano_cohorte AS (
    SELECT cohorte, COUNT(DISTINCT id_cliente) AS clientes_iniciales
    FROM primera_compra
    GROUP BY cohorte
)
SELECT
    a.cohorte,
    t.clientes_iniciales,
    a.mes_desde_primera_compra                                      AS mes,
    COUNT(DISTINCT a.id_cliente)                                    AS clientes_activos,
    ROUND(COUNT(DISTINCT a.id_cliente) / t.clientes_iniciales * 100, 1) AS tasa_retencion_pct
FROM actividad a
JOIN tamano_cohorte t ON a.cohorte = t.cohorte
WHERE
    a.mes_desde_primera_compra BETWEEN 0 AND 11
    AND a.cohorte BETWEEN '2023-01' AND '2023-09'
GROUP BY a.cohorte, t.clientes_iniciales, a.mes_desde_primera_compra
ORDER BY a.cohorte, a.mes_desde_primera_compra;
