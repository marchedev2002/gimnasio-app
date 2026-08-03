-- =========================================================
-- Base de datos: Gimnasio
-- Ejecutar este script completo en MySQL Workbench
-- (Archivo -> Open SQL Script -> seleccionar este archivo -> Rayo/Ejecutar)
-- =========================================================

CREATE DATABASE IF NOT EXISTS gimnasio_db;
USE gimnasio_db;

-- ---------------------------------------------------------
-- Tabla MES: catálogo de meses (para no repetir texto)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS MES (
    id_mes INT PRIMARY KEY,
    nombre_mes VARCHAR(20) NOT NULL
);

INSERT INTO MES (id_mes, nombre_mes) VALUES
(1,'Enero'),(2,'Febrero'),(3,'Marzo'),(4,'Abril'),
(5,'Mayo'),(6,'Junio'),(7,'Julio'),(8,'Agosto'),
(9,'Septiembre'),(10,'Octubre'),(11,'Noviembre'),(12,'Diciembre')
ON DUPLICATE KEY UPDATE nombre_mes = VALUES(nombre_mes);

-- ---------------------------------------------------------
-- Tabla PRECIO: los distintos planes/precios de membresía
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS PRECIO (
    id_precio INT AUTO_INCREMENT PRIMARY KEY,
    tipo_membresia VARCHAR(50) NOT NULL,
    monto DECIMAL(10,2) NOT NULL
);

INSERT INTO PRECIO (tipo_membresia, monto) VALUES
('Musculación', 15000.00),
('Musculación + Clases', 20000.00),
('Solo Clases', 12000.00);

-- ---------------------------------------------------------
-- Tabla USUARIO: datos del socio del gimnasio
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS USUARIO (
    dni VARCHAR(15) PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL,
    apellido VARCHAR(60) NOT NULL,
    telefono VARCHAR(30),
    email VARCHAR(100),
    foto VARCHAR(255)  -- nombre del archivo de imagen, ej: 12345678.jpg
);

-- ---------------------------------------------------------
-- Tabla PAGO: registro de cada pago realizado
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS PAGO (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    dni VARCHAR(15) NOT NULL,
    id_mes INT NOT NULL,
    anio INT NOT NULL,
    id_precio INT NOT NULL,
    fecha_pago DATE NOT NULL,
    FOREIGN KEY (dni) REFERENCES USUARIO(dni),
    FOREIGN KEY (id_mes) REFERENCES MES(id_mes),
    FOREIGN KEY (id_precio) REFERENCES PRECIO(id_precio)
);

-- ---------------------------------------------------------
-- Datos de ejemplo para probar el sistema
-- ---------------------------------------------------------
INSERT INTO USUARIO (dni, nombre, apellido, telefono, email, foto) VALUES
('40123456', 'Juan', 'Perez', '341-5551234', 'juan.perez@mail.com', NULL),
('38987654', 'Maria', 'Gomez', '341-5555678', 'maria.gomez@mail.com', NULL);

-- Juan pagó el mes actual (ejemplo julio 2026) -> membresía AL DIA
INSERT INTO PAGO (dni, id_mes, anio, id_precio, fecha_pago) VALUES
('40123456', 7, 2026, 1, '2026-07-05');

-- Maria pagó junio pero no julio -> membresía VENCIDA
INSERT INTO PAGO (dni, id_mes, anio, id_precio, fecha_pago) VALUES
('38987654', 6, 2026, 2, '2026-06-03');
