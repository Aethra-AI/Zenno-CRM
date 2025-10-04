#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar usuarios en la base de datos
"""

import sqlite3
import os

def check_users():
    """Verificar usuarios en la base de datos"""
    db_path = os.path.join(os.path.dirname(__file__), 'whatsapp_multi_tenant.db')
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar usuarios
        cursor.execute("SELECT id, email, username, tenant_id FROM users LIMIT 10")
        users = cursor.fetchall()
        
        print("👥 Usuarios en la base de datos:")
        print("-" * 50)
        
        for user in users:
            print(f"ID: {user[0]}, Email: {user[1]}, Username: {user[2]}, Tenant: {user[3]}")
        
        # Verificar si hay usuarios
        if not users:
            print("❌ No hay usuarios en la base de datos")
            
            # Crear usuario de prueba
            print("\n🔧 Creando usuario de prueba...")
            cursor.execute("""
                INSERT INTO users (email, username, password, tenant_id, role)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin@example.com", "admin", "admin123", 1, "admin"))
            
            conn.commit()
            print("✅ Usuario admin creado")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_users()