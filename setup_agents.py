import os
import sys
import subprocess

def setup():
    print("🚀 Iniciando configuración del entorno ESC Agent...")
    
    # 1. Construir la imagen maestra
    print("📦 Construyendo imagen base de Docker (esto puede tardar unos minutos)...")
    try:
        # Importamos aquí para asegurar que los paths son relativos al bACKEND
        from agent_orchestrator import orchestrator
        if orchestrator.build_base_image():
            print("✅ Imagen base construida exitosamente.")
        else:
            print("❌ Error al construir la imagen base.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # 2. Verificar Red de Docker
    print("🌐 Verificando red interna de agentes...")
    subprocess.run(["docker", "network", "create", "esc-network"], capture_output=True)
    
    print("\n🎉 ¡Sistema listo para producción!")
    print("Los agentes se crearán automáticamente cuando los Tenants los activen desde el CRM.")

if __name__ == "__main__":
    setup()
