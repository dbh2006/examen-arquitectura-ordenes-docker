SET QUOTED_IDENTIFIER ON;
GO

SET ANSI_NULLS ON;
GO

IF DB_ID('OrdenesDB') IS NULL
BEGIN
    CREATE DATABASE OrdenesDB;
END
GO

USE OrdenesDB;
GO

-- Tabla principal de órdenes
IF OBJECT_ID('dbo.ordenes', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ordenes (
        id INT IDENTITY(1,1) PRIMARY KEY,
        cliente NVARCHAR(150) NOT NULL,
        fecha DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
        estado NVARCHAR(20) NOT NULL DEFAULT 'Pendiente',
        total DECIMAL(12,2) NOT NULL DEFAULT 0,
        CONSTRAINT CK_ordenes_estado
            CHECK (estado IN ('Pendiente', 'Pagada', 'Anulada'))
    );
END
GO

-- Tabla de detalles de las órdenes
IF OBJECT_ID('dbo.orden_detalle', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.orden_detalle (
        id INT IDENTITY(1,1) PRIMARY KEY,
        orden_id INT NOT NULL,
        producto NVARCHAR(150) NOT NULL,
        cantidad INT NOT NULL,
        precio_unitario DECIMAL(12,2) NOT NULL,
        subtotal AS (
            CONVERT(DECIMAL(12,2), cantidad * precio_unitario)
        ) PERSISTED,
        CONSTRAINT FK_orden_detalle_ordenes
            FOREIGN KEY (orden_id)
            REFERENCES dbo.ordenes(id),
        CONSTRAINT CK_detalle_cantidad CHECK (cantidad > 0),
        CONSTRAINT CK_detalle_precio CHECK (precio_unitario >= 0)
    );
END
GO


-- Insertar datos iniciales una sola vez
IF NOT EXISTS (SELECT 1 FROM dbo.ordenes)
BEGIN
    INSERT INTO dbo.ordenes (cliente, fecha, estado)
    VALUES
    ('Fernanda Ferrari', '2026-11-10', 'Pendiente'),
    ('Martin Cruz', '2026-11-11', 'Pagada'),
    ('Daniela Hernandez', '2026-11-12', 'Pendiente'),
    ('David Moncada', '2026-11-13', 'Pagada'),
    ('Cecilia Nuñez', '2026-11-14', 'Anulada');

    DECLARE @id1 INT, @id2 INT, @id3 INT, @id4 INT, @id5 INT;

    SELECT @id1 = id FROM dbo.ordenes WHERE cliente = 'Fernanda Ferrari';
    SELECT @id2 = id FROM dbo.ordenes WHERE cliente = 'Martin Cruz';
    SELECT @id3 = id FROM dbo.ordenes WHERE cliente = 'Daniela Hernandez';
    SELECT @id4 = id FROM dbo.ordenes WHERE cliente = 'David Moncada';
    SELECT @id5 = id FROM dbo.ordenes WHERE cliente = 'Cecilia Nuñez';

    INSERT INTO dbo.orden_detalle
        (orden_id, producto, cantidad, precio_unitario)
    VALUES
    (@id1, 'Teclado Gamer', 2, 1250.00),
    (@id1, 'Mouse inalambrico', 1, 650.00),

    (@id2, 'Monitor LED 24 pulgadas', 1, 4200.00),
    (@id2, 'Soporte para monitor', 1, 850.00),

    (@id3, 'Memoria USB 32GB', 3, 320.00),
    (@id3, 'Hub USB tipo C', 1, 780.00),

    (@id4, 'Disco SSD NVMe 1TB', 1, 2450.00),
    (@id4, 'Memoria RAM DDR4 16GB', 2, 1150.00),

    (@id5, 'Camara web Full HD', 1, 1650.00),
    (@id5, 'Microfono', 1, 1350.00);
END;


    -- Calcular totales de las órdenes
    UPDATE o
    SET total = (
        SELECT COALESCE(SUM(d.subtotal), 0)
        FROM dbo.orden_detalle d
        WHERE d.orden_id = o.id
    )
    FROM dbo.ordenes o;
END
GO

-- Comprobar los datos
SELECT * FROM dbo.ordenes;
SELECT * FROM dbo.orden_detalle;
GO
