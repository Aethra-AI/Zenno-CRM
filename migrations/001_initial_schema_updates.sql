-- Migración: 001_initial_schema_updates.sql
-- Descripción: Actualización inicial del esquema para soportar la nueva interfaz
-- Fecha: 2025-09-19

-- 1. Modificar tabla afiliados para agregar nuevos campos
ALTER TABLE afiliados 
ADD COLUMN IF NOT EXISTS puntuacion INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS fuente_reclutamiento VARCHAR(50),
ADD COLUMN IF NOT EXISTS disponibilidad VARCHAR(50),
ADD COLUMN IF NOT EXISTS salario_deseado DECIMAL(10,2),
MODIFY COLUMN habilidades JSON;

-- 2. Crear tabla de puntuaciones de candidatos
CREATE TABLE IF NOT EXISTS puntuaciones_candidato (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_afiliado INT NOT NULL,
    puntuacion INT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(255),
    usuario_id INT NOT NULL,
    FOREIGN KEY (id_afiliado) REFERENCES afiliados(id_afiliado) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Crear tabla de interacciones
CREATE TABLE IF NOT EXISTS interacciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_afiliado INT NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    notas TEXT,
    usuario_id INT,
    siguiente_accion VARCHAR(255),
    fecha_siguiente_accion DATETIME,
    completada BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (id_afiliado) REFERENCES afiliados(id_afiliado) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Crear tabla de documentos
CREATE TABLE IF NOT EXISTS documentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_afiliado INT NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(512) NOT NULL,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    es_publico BOOLEAN DEFAULT FALSE,
    usuario_id INT,
    FOREIGN KEY (id_afiliado) REFERENCES afiliados(id_afiliado) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_afiliados_estado ON afiliados(estado);
CREATE INDEX IF NOT EXISTS idx_afiliados_puntuacion ON afiliados(puntuacion);
CREATE INDEX IF NOT EXISTS idx_interacciones_afiliado ON interacciones(id_afiliado);
CREATE INDEX IF NOT EXISTS idx_interacciones_fecha ON interacciones(fecha);
CREATE INDEX IF NOT EXISTS idx_documentos_afiliado ON documentos(id_afiliado);
CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON documentos(tipo);

-- 6. Actualizar la tabla de afiliados con datos iniciales (si es necesario)
-- Por ejemplo, calcular puntuaciones iniciales basadas en datos existentes
-- UPDATE afiliados SET puntuacion = 50 WHERE puntuacion IS NULL;

-- 7. Crear un trigger para actualizar automáticamente el campo ultimo_contacto
DELIMITER //
CREATE TRIGGER IF NOT EXISTS after_interaccion_insert
AFTER INSERT ON interacciones
FOR EACH ROW
BEGIN
    UPDATE afiliados 
    SET ultimo_contacto = NEW.fecha 
    WHERE id_afiliado = NEW.id_afiliado;
END//
DELIMITER ;

-- 8. Agregar comentarios descriptivos a las tablas y columnas
ALTER TABLE afiliados 
COMMENT 'Almacena información de los candidatos/afiliados al sistema';

ALTER TABLE puntuaciones_candidato
COMMENT 'Registra el histórico de puntuaciones de los candidatos';

ALTER TABLE interacciones
COMMENT 'Registra todas las interacciones con los candidatos';

ALTER TABLE documentos
COMMENT 'Almacena información sobre documentos adjuntos de los candidatos';
