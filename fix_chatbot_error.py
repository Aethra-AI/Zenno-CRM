#!/usr/bin/env python3
"""
Script para aplicar un parche temporal al error del chatbot
"""

import re

def fix_chatbot_error():
    """Aplicar parche al archivo app.py en la VM"""
    
    # Leer el archivo
    with open('/opt/whatsapp-backend/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar la línea problemática y reemplazarla
    old_pattern = r'(\s+)user_role = current_user\.get\(\'rol\', \'\'\)'
    new_pattern = r'''\1# DEBUG: Verificar tipo de current_user
\1app.logger.info(f"DEBUG - Tipo de current_user: {type(current_user)}")
\1app.logger.info(f"DEBUG - Contenido de current_user: {current_user}")
\1
\1# Si current_user es una tupla, extraer el diccionario
\1if isinstance(current_user, tuple):
\1    app.logger.warning("current_user es una tupla, extrayendo primer elemento")
\1    current_user = current_user[0] if len(current_user) > 0 else {}
\1
\1user_role = current_user.get('rol', '') if isinstance(current_user, dict) else '''
    
    # Aplicar el reemplazo
    new_content = re.sub(old_pattern, new_pattern, content)
    
    # También arreglar las referencias a empresa_nombre
    old_pattern2 = r'(\s+)empresa_nombre = current_user\.get\(\'empresa_nombre\', \'la organización\'\)'
    new_pattern2 = r'''\1# Obtener empresa_nombre de forma segura
\1empresa_nombre = current_user.get('empresa_nombre', 'la organización') if isinstance(current_user, dict) else 'la organización''''
    
    new_content = re.sub(old_pattern2, new_pattern2, new_content)
    
    # Escribir el archivo corregido
    with open('/opt/whatsapp-backend/app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Parche aplicado exitosamente")
    print("🔄 Reiniciando servicio...")
    
    import subprocess
    subprocess.run(['sudo', 'systemctl', 'restart', 'whatsapp-backend.service'], check=True)
    print("✅ Servicio reiniciado")

if __name__ == "__main__":
    fix_chatbot_error()
