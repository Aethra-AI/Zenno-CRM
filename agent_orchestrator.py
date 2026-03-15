import os
import subprocess
import logging
import json

# Configuración del orquestador
AGENT_IMAGE_NAME = "esc-agent-image"
BASE_DATA_PATH = "/opt/esc-crm/agents-data" # Ruta en la VM para persistencia
DOCKER_NETWORK = "esc-network"

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Gestiona el ciclo de vida de las instancias de Clawdbot por Tenant"""
    
    def __init__(self):
        # Asegurar que el directorio de datos existe
        os.makedirs(BASE_DATA_PATH, exist_ok=True)
        # Crear red de docker si no existe
        try:
            subprocess.run(["docker", "network", "create", DOCKER_NETWORK], capture_output=True)
        except:
            pass

    def build_base_image(self):
        """Construye o actualiza la imagen maestra de los agentes"""
        logger.info("Construyendo imagen maestra de agentes ESC...")
        result = subprocess.run(
            ["docker", "build", "-t", AGENT_IMAGE_NAME, "-f", "Dockerfile.agent", "."],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            logger.info("Imagen construida exitosamente.")
            return True
        else:
            logger.error(f"Error construyendo imagen: {result.stderr}")
            return False

    def deploy_agent(self, tenant_id, tenant_api_key, llm_api_key, crm_url):
        """
        Despliega o reinicia el agente único para un Tenant.
        """
        container_name = f"esc-agent-tenant-{tenant_id}"
        tenant_data_path = os.path.join(BASE_DATA_PATH, f"tenant_{tenant_id}")
        os.makedirs(tenant_data_path, exist_ok=True)

        # 1. Detener y eliminar contenedor anterior si existe
        logger.info(f"Limpiando instancia previa para Tenant {tenant_id}...")
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        subprocess.run(["docker", "rm", container_name], capture_output=True)

        # 2. Comando de ejecución
        # Cada agente tiene su propio volumen para MEMORY.md y sesión de WhatsApp
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--network", DOCKER_NETWORK,
            "-v", f"{tenant_data_path}:/app/data",
            "-e", f"OPENAI_API_KEY={llm_api_key}",
            "-e", f"ESC_TENANT_API_KEY={tenant_api_key}",
            "-e", f"ESC_CRM_URL={crm_url}",
            "--restart", "unless-stopped",
            AGENT_IMAGE_NAME
        ]

        logger.info(f"Desplegando agente para Tenant {tenant_id}...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"✅ Agente para Tenant {tenant_id} desplegado (ID: {result.stdout[:12]})")
            return True, container_name
        else:
            logger.error(f"❌ Error al desplegar agente: {result.stderr}")
            return False, result.stderr

    def stop_agent(self, tenant_id):
        """Detiene y elimina el agente de un tenant (ej. por falta de pago)"""
        container_name = f"esc-agent-tenant-{tenant_id}"
        subprocess.run(["docker", "stop", container_name])
        subprocess.run(["docker", "rm", container_name])
        return True

# Instancia global para usar en app.py
orchestrator = AgentOrchestrator()
