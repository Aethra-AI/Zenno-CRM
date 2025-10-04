#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir el hash de la contraseña en la base de datos
"""

import sqlite3
import os
import bcrypt

def fix_password_hash():
    """Corregir el hash de la contraseña del usuario admin"""
    db_path = os.path.join(os.path.dirname(__file__), 'whatsapp_multi_tenant.db')
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Generar hash correcto con bcrypt
        password = "admin123"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Actualizar el usuario admin
        cursor.execute("""
            UPDATE users 
            SET password = ? 
            WHERE email = 'admin@example.com'
        """, (hashed_password.decode('utf-8'),))
        
        conn.commit()
        
        # Verificar el cambio
        cursor.execute("""
            SELECT email, password FROM users WHERE email = 'admin@example.com'
        """)
        user = cursor.fetchone()
        
        if user:
            print(f"✅ Usuario actualizado: {user[0]}")
            print(f"🔑 Hash generado correctamente")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_password_hash()
