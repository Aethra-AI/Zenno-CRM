#!/bin/bash
# Script para actualizar el Backend y asegurar el entorno de agentes
# Ejecutar este script despues de un git pull

echo "🚀 Actualizando sistema de agentes ESC..."

# 1. Instalar dependencias nuevas del backend (si las hay)
pip install -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt

# 2. Re-construir la imagen maestra de los agentes
# Esto asegura que si cambiaste la Skill o el Dockerfile, los nuevos agentes esten actualizados
echo "📦 Actualizando imagen base de Clawdbot..."
python3 setup_agents.py

# 3. Reiniciar el servicio del backend (Asumiendo que usas systemd o pm2)
# Si usas un servicio de systemd llamado 'esc-backend':
# sudo systemctl restart esc-backend

echo "✅ Sistema actualizado. Los agentes existentes seguiran corriendo,"
echo "y los nuevos usaran la version mas reciente del codigo."
