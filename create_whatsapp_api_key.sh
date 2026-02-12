#!/bin/bash

# Script para crear API Key desde la línea de comandos
# Ejecuta esto en la VM donde está tu base de datos

echo "=== Crear API Key para WhatsApp Agent ==="
echo ""

# Configuración de la base de datos (ajusta según tu .env)
DB_HOST="localhost"
DB_USER="tu_usuario_mysql"
DB_PASS="tu_password_mysql"
DB_NAME="crm_database"

# Datos de la API Key
TENANT_ID=1  # Ajusta según tu tenant
NOMBRE="WhatsApp Agent API Key"
PERMISOS='{"vacancies": true, "candidates": true}'

# Generar API Key segura
API_KEY="hnm_live_$(openssl rand -hex 32)"

echo "Creando API Key en la base de datos..."
echo ""

mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" <<EOF
INSERT INTO Tenant_API_Keys (
    tenant_id,
    api_key,
    nombre_descriptivo,
    permisos,
    activa,
    fecha_creacion,
    fecha_expiracion
) VALUES (
    $TENANT_ID,
    '$API_KEY',
    '$NOMBRE',
    '$PERMISOS',
    1,
    NOW(),
    DATE_ADD(NOW(), INTERVAL 365 DAY)
);
EOF

if [ $? -eq 0 ]; then
    echo "✅ API Key creada exitosamente!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔑 TU API KEY (guárdala en un lugar seguro):"
    echo ""
    echo "   $API_KEY"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Válida por: 365 días"
    echo "Permisos: vacancies, candidates"
else
    echo "❌ Error creando API Key"
fi
