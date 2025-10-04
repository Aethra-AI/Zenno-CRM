#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la estructura de la tabla Users en MySQL
"""

import mysql.connector
import os
from dotenv import load_dotenv

def check_mysql_users():
    """Verificar estructura y datos de la tabla Users"""
    
    load_dotenv()
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3306)),
            database=os.getenv('DB_NAME', 'crm_database')
        )
        
        cursor = conn.cursor()
        
        print("🔗 Conectado a MySQL exitosamente")
        
        # Verificar estructura de la tabla Users
        cursor.execute("DESCRIBE Users")
        columns = cursor.fetchall()
        
        print("\n📋 Estructura de la tabla Users:")
        print("-" * 50)
        for col in columns:
            print(f"   {col[0]} - {col[1]} - {col[2]} - {col[3]}")
        
        # Verificar usuarios existentes
        cursor.execute("SELECT id, email, username, nombre FROM Users LIMIT 10")
        users = cursor.fetchall()
        
        print(f"\n👥 Usuarios existentes ({len(users)}):")
        print("-" * 50)
        for user in users:
            print(f"   ID: {user[0]}, Email: {user[1]}, Username: {user[2]}, Nombre: {user[3]}")
        
        # Verificar si existe usuario admin
        cursor.execute("SELECT id FROM Users WHERE email = %s", ("admin@example.com",))
        admin_user = cursor.fetchone()
        
        if admin_user:
            print(f"\n✅ Usuario admin encontrado con ID: {admin_user[0]}")
        else:
            print("\n❌ Usuario admin no encontrado")
        
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"❌ Error de MySQL: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_mysql_users()
