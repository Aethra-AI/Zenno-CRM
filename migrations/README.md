# Migraciones de Base de Datos

Este directorio contiene los scripts de migración para la base de datos del sistema. Las migraciones se utilizan para gestionar los cambios en el esquema de la base de datos de manera controlada y reproducible.

## Estructura del Directorio

- `001_initial_schema_updates.sql`: Primera migración que agrega nuevas tablas y modifica las existentes
- `run_migrations.py`: Script para ejecutar las migraciones pendientes
- `.env.example`: Archivo de ejemplo para configurar las variables de entorno

## Cómo Ejecutar las Migraciones

1. **Configuración Inicial**
   - Copia el archivo `.env.example` a `.env`
   - Configura las variables de entorno con los valores correctos para tu entorno

2. **Instalar Dependencias**
   Asegúrate de tener instaladas las dependencias necesarias:
   ```bash
   pip install mysql-connector-python python-dotenv
   ```

3. **Ejecutar las Migraciones**
   ```bash
   python run_migrations.py
   ```

   Este script:
   - Verificará la conexión a la base de datos
   - Creará la tabla de control de migraciones si no existe
   - Identificará y ejecutará las migraciones pendientes
   - Registrará el resultado en el archivo `migration.log`

## Convenciones para Crear Nuevas Migraciones

1. **Nombrado de Archivos**:
   - Formato: `NNN_nombre_descriptivo.sql` (donde NNN es un número secuencial)
   - Ejemplo: `002_add_new_feature_tables.sql`

2. **Contenido del Archivo**:
   - Incluir comentarios descriptivos al inicio del archivo
   - Cada sentencia SQL debe terminar con punto y coma
   - Incluir sentencias para deshacer la migración (rollback) si es posible

3. **Pruebas**:
   - Probar las migraciones en un entorno de desarrollo antes de aplicar en producción
   - Verificar que los datos existentes no se vean afectados negativamente

## Manejo de Errores

Si ocurre un error durante la migración:

1. Revisa el archivo `migration.log` para ver el error específico
2. Si es necesario, realiza un rollback manual de los cambios
3. Corrige el problema y vuelve a ejecutar la migración

## Seguridad

- Nunca incluyas información sensible (contraseñas, claves API) en los scripts de migración
- Utiliza variables de entorno para manejar credenciales
- Asegúrate de que solo los usuarios autorizados tengan acceso a ejecutar migraciones
