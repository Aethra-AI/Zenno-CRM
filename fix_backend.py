#!/bin/bash
# -*- coding: utf-8 -*-
import os
import subprocess
import sys

def check_docker():
    """Verifica si docker esta instalado y el usuario tiene permisos"""
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        # Verificar permisos
        res = subprocess.run(["docker", "ps"], capture_output=True)
        if res.returncode != 0:
            print("❌ ERROR: El usuario no tiene permisos para usar Docker.")
            print("Ejecuta: sudo usermod -aG docker $USER y REINICIA TU SESION SSH.")
            return False
        return True
    except:
        print("❌ ERROR: Docker no esta instalado.")
        return False

def fix_permissions():
    """Asegura que el usuario ubuntu sea el dueño de la carpeta"""
    print("🔐 Asegurando permisos de archivos...")
    subprocess.run(["sudo", "chown", "-R", "ubuntu:ubuntu", "/opt/whatsapp-backend"])

def main():
    print("🚀 Iniciando REPARACION del Backend ESC...")
    
    # 1. Permisos
    fix_permissions()
    
    # 2. Docker
    if not check_docker():
        sys.exit(1)
        
    # 3. Construir imagen (manualmente fuera de Flask para no bloquearlo)
    print("📦 Construyendo imagen maestra de agentes (esto puede tardar)...")
    try:
        # Usar el script de setup que ya existe
        res = subprocess.run(["python3", "setup_agents.py"], capture_output=True, text=True)
        if res.returncode == 0:
            print("✅ Imagen base lista.")
        else:
            print(f"❌ Error construyendo imagen: {res.stderr}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 4. Reiniciar servicio
    print("🔄 Reiniciando servicio whatsapp-backend...")
    subprocess.run(["sudo", "systemctl", "restart", "whatsapp-backend.service"])
    
    print("\n✨ REPARACION COMPLETADA.")
    print("Verifica los logs con: sudo journalctl -u whatsapp-backend.service -f")

if __name__ == "__main__":
    main()
