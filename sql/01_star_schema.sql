-- =============================================================================
-- Nexo Comercial S.A. — Esquema estrella
-- Motor: MySQL 8.0+
-- Ejecutar en MySQL Workbench o desde terminal: mysql -u root -p < 01_star_schema.sql
-- =============================================================================

CREATE DATABASE IF NOT EXISTS nexo_comercial
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE nexo_comercial;


-- ── DIMENSIÓN CALENDARIO ──────────────────────────────────────────────────────
DROP TABLE IF EXISTS FactVentas;
DROP TABLE IF EXISTS DimCalendario;
DROP TABLE IF EXISTS DimCliente;
DROP TABLE IF EXISTS DimProducto;
DROP TABLE IF EXISTS DimAgente;

CREATE TABLE DimCalendario (
    fecha           DATE         NOT NULL,
    anio            SMALLINT,
    trimestre       TINYINT,
    trimestre_label VARCHAR(3),
    mes             TINYINT,
    nombre_mes      VARCHAR(20),
    semana          TINYINT,
    dia             TINYINT,
    dia_semana_num  TINYINT,
    dia_semana      VARCHAR(15),
    es_fin_semana   TINYINT,
    anio_mes        VARCHAR(7),
    PRIMARY KEY (fecha)
) ENGINE=InnoDB;

CREATE INDEX idx_cal_anio_mes ON DimCalendario(anio_mes);
CREATE INDEX idx_cal_anio     ON DimCalendario(anio);


-- ── DIMENSIÓN AGENTE ──────────────────────────────────────────────────────────
CREATE TABLE DimAgente (
    id_agente      VARCHAR(6)     NOT NULL,
    nombre         VARCHAR(100),
    zona           VARCHAR(30),
    gerente        VARCHAR(100),
    target_mensual DECIMAL(12,2),
    fecha_ingreso  DATE,
    PRIMARY KEY (id_agente)
) ENGINE=InnoDB;

CREATE INDEX idx_agente_zona ON DimAgente(zona);


-- ── DIMENSIÓN PRODUCTO ────────────────────────────────────────────────────────
CREATE TABLE DimProducto (
    id_producto  VARCHAR(6)    NOT NULL,
    nombre       VARCHAR(100),
    categoria    VARCHAR(30),
    subcategoria VARCHAR(30),
    precio_lista DECIMAL(12,2),
    costo        DECIMAL(12,2),
    PRIMARY KEY (id_producto)
) ENGINE=InnoDB;

CREATE INDEX idx_prod_cat ON DimProducto(categoria);


-- ── DIMENSIÓN CLIENTE ─────────────────────────────────────────────────────────
CREATE TABLE DimCliente (
    id_cliente VARCHAR(8)   NOT NULL,
    nombre     VARCHAR(150),
    segmento   VARCHAR(15),
    ciudad     VARCHAR(50),
    region     VARCHAR(20),
    fecha_alta DATE,
    PRIMARY KEY (id_cliente)
) ENGINE=InnoDB;

CREATE INDEX idx_cli_segmento ON DimCliente(segmento);
CREATE INDEX idx_cli_region   ON DimCliente(region);


-- ── TABLA DE HECHOS ───────────────────────────────────────────────────────────
CREATE TABLE FactVentas (
    id_venta        VARCHAR(9)    NOT NULL,
    fecha           DATE,
    id_cliente      VARCHAR(8),
    id_producto     VARCHAR(6),
    id_agente       VARCHAR(6),
    zona            VARCHAR(30),
    cantidad        SMALLINT,
    precio_unitario DECIMAL(12,2),
    descuento_pct   DECIMAL(5,2),
    monto_total     DECIMAL(14,2),
    tipo_pago       VARCHAR(25),
    estado          VARCHAR(12),
    PRIMARY KEY (id_venta),
    FOREIGN KEY (fecha)       REFERENCES DimCalendario(fecha),
    FOREIGN KEY (id_cliente)  REFERENCES DimCliente(id_cliente),
    FOREIGN KEY (id_producto) REFERENCES DimProducto(id_producto),
    FOREIGN KEY (id_agente)   REFERENCES DimAgente(id_agente)
) ENGINE=InnoDB;

CREATE INDEX idx_fact_fecha    ON FactVentas(fecha);
CREATE INDEX idx_fact_agente   ON FactVentas(id_agente);
CREATE INDEX idx_fact_cliente  ON FactVentas(id_cliente);
CREATE INDEX idx_fact_producto ON FactVentas(id_producto);
CREATE INDEX idx_fact_estado   ON FactVentas(estado);
