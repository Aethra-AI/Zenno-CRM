-- =====================================================
-- 🚀 MÓDULO B2 - Agregar columnas de trazabilidad
-- Base de datos: whatsapp_backend
-- =====================================================

USE whatsapp_backend;

-- =====================================================
-- 1. AGREGAR COLUMNA created_by_user A 6 TABLAS
-- =====================================================

ALTER TABLE Afiliados 
ADD COLUMN created_by_user INT NULL AFTER tenant_id;

ALTER TABLE Postulaciones 
ADD COLUMN created_by_user INT NULL AFTER tenant_id;

ALTER TABLE Entrevistas 
ADD COLUMN created_by_user INT NULL AFTER tenant_id;

ALTER TABLE Vacantes 
ADD COLUMN created_by_user INT NULL AFTER tenant_id;

ALTER TABLE Clientes 
ADD COLUMN created_by_user INT NULL AFTER tenant_id;

ALTER TABLE Contratados 
ADD COLUMN created_by_user INT NULL AFTER tenant_id;


-- =====================================================
-- 2. AGREGAR FOREIGN KEYS
-- =====================================================

ALTER TABLE Afiliados 
ADD CONSTRAINT fk_afiliados_created_by 
FOREIGN KEY (created_by_user) REFERENCES Users(id) ON DELETE SET NULL;

ALTER TABLE Postulaciones 
ADD CONSTRAINT fk_postulaciones_created_by 
FOREIGN KEY (created_by_user) REFERENCES Users(id) ON DELETE SET NULL;

ALTER TABLE Entrevistas 
ADD CONSTRAINT fk_entrevistas_created_by 
FOREIGN KEY (created_by_user) REFERENCES Users(id) ON DELETE SET NULL;

ALTER TABLE Vacantes 
ADD CONSTRAINT fk_vacantes_created_by 
FOREIGN KEY (created_by_user) REFERENCES Users(id) ON DELETE SET NULL;

ALTER TABLE Clientes 
ADD CONSTRAINT fk_clientes_created_by 
FOREIGN KEY (created_by_user) REFERENCES Users(id) ON DELETE SET NULL;

ALTER TABLE Contratados 
ADD CONSTRAINT fk_contratados_created_by 
FOREIGN KEY (created_by_user) REFERENCES Users(id) ON DELETE SET NULL;


-- =====================================================
-- 3. CREAR ÍNDICES PARA OPTIMIZAR BÚSQUEDAS
-- =====================================================

CREATE INDEX idx_afiliados_created_by ON Afiliados(created_by_user, tenant_id);
CREATE INDEX idx_postulaciones_created_by ON Postulaciones(created_by_user, tenant_id);
CREATE INDEX idx_entrevistas_created_by ON Entrevistas(created_by_user, tenant_id);
CREATE INDEX idx_vacantes_created_by ON Vacantes(created_by_user, tenant_id);
CREATE INDEX idx_clientes_created_by ON Clientes(created_by_user, tenant_id);
CREATE INDEX idx_contratados_created_by ON Contratados(created_by_user, tenant_id);


-- =====================================================
-- ✅ VERIFICACIÓN
-- =====================================================

-- Ver que las columnas existen
SELECT 'Afiliados' as tabla, COUNT(*) as tiene_columna 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Afiliados' 
  AND COLUMN_NAME = 'created_by_user'

UNION ALL

SELECT 'Postulaciones', COUNT(*) 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Postulaciones' 
  AND COLUMN_NAME = 'created_by_user'

UNION ALL

SELECT 'Entrevistas', COUNT(*) 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Entrevistas' 
  AND COLUMN_NAME = 'created_by_user'

UNION ALL

SELECT 'Vacantes', COUNT(*) 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Vacantes' 
  AND COLUMN_NAME = 'created_by_user'

UNION ALL

SELECT 'Clientes', COUNT(*) 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Clientes' 
  AND COLUMN_NAME = 'created_by_user'

UNION ALL

SELECT 'Contratados', COUNT(*) 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'whatsapp_backend' 
  AND TABLE_NAME = 'Contratados' 
  AND COLUMN_NAME = 'created_by_user';


-- Ver foreign keys creados (debe mostrar 6)
SELECT COUNT(*) as foreign_keys_creados
FROM information_schema.TABLE_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'whatsapp_backend'
  AND CONSTRAINT_TYPE = 'FOREIGN KEY'
  AND CONSTRAINT_NAME LIKE 'fk_%_created_by';


-- Ver índices creados (debe mostrar 6)
SELECT COUNT(*) as indices_creados
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'whatsapp_backend'
  AND INDEX_NAME LIKE 'idx_%_created_by';


SELECT '✅ Módulo B2 completado' as resultado;


