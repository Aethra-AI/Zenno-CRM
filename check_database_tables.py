#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar las tablas en la base de datos
"""

import sqlite3
import os

def check_tables():
    """Verificar tablas en la base de datos"""
    db_path = os.path.join(os.path.dirname(__file__), 'whatsapp_multi_tenant.db')
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("📋 Tablas en la base de datos:")
        print("-" * 40)
        
        for table in tables:
            table_name = table[0]
            print(f"📄 {table_name}")
            
            # Mostrar estructura de la tabla
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            # Mostrar algunos datos de ejemplo
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📊 Registros: {count}")
            
            if count > 0 and table_name.lower() in ['users', 'users']:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                print("   📝 Datos de ejemplo:")
                for row in rows:
                    print(f"      {row}")
            
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_tables()
