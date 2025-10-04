#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear usuario admin en la base de datos MySQL existente
"""

import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

def create_mysql_admin():
    """Crear usuario admin en MySQL"""
    
    # Cargar variables de entorno
    load_dotenv()
    
    try:
        # Conectar a MySQL
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3306)),
            database=os.getenv('DB_NAME', 'crm_database')
        )
        
        cursor = conn.cursor()
        
        print("🔗 Conectado a MySQL exitosamente")
        
        # Verificar si la tabla Users existe
        cursor.execute("SHOW TABLES LIKE 'Users'")
        if not cursor.fetchone():
            print("❌ Tabla 'Users' no encontrada")
            print("📋 Tablas disponibles:")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            for table in tables:
                print(f"   - {table[0]}")
            return
        
        # Verificar si el usuario admin ya existe
        cursor.execute("SELECT id FROM Users WHERE email = %s", ("admin@example.com",))
        if cursor.fetchone():
            print("✅ Usuario admin ya existe")
        else:
            # Crear usuario admin
            password = "admin123"
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute("""
                INSERT INTO Users (email, password_hash, nombre, telefono, rol_id, activo, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, ("admin@example.com", hashed_password.decode('utf-8'), "Administrador", "1234567890", 1, 1))
            
            conn.commit()
            print("✅ Usuario admin creado exitosamente")
        
        # Verificar usuarios existentes
        cursor.execute("SELECT id, email, nombre FROM Users LIMIT 5")
        users = cursor.fetchall()
        
        print("\n👥 Usuarios en la base de datos:")
        for user in users:
            print(f"   ID: {user[0]}, Email: {user[1]}, Nombre: {user[2]}")
        
        conn.close()
        print("\n🔑 Credenciales para pruebas:")
        print("   Email: admin@example.com")
        print("   Password: admin123")
        
    except mysql.connector.Error as e:
        print(f"❌ Error de MySQL: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_mysql_admin()
