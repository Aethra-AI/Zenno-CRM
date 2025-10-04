#!/usr/bin/env python3
"""
Script para agregar tenant_id a la tabla Afiliados
"""

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'crm_database')
    )
    cursor = conn.cursor()
    
    print("🔧 Agregando columna tenant_id a la tabla Afiliados...")
    
    # Verificar si la columna ya existe
    cursor.execute("SHOW COLUMNS FROM Afiliados LIKE 'tenant_id'")
    if cursor.fetchone():
        print("✅ La columna tenant_id ya existe")
    else:
        # Agregar columna tenant_id
        cursor.execute("ALTER TABLE Afiliados ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id_afiliado")
        print("✅ Columna tenant_id agregada")
        
        # Agregar índice
        cursor.execute("ALTER TABLE Afiliados ADD INDEX idx_tenant_id (tenant_id)")
        print("✅ Índice agregado")
        
        # Actualizar registros existentes
        cursor.execute("UPDATE Afiliados SET tenant_id = 1 WHERE tenant_id IS NULL OR tenant_id = 0")
        print("✅ Registros existentes actualizados")
    
    conn.commit()
    print("🎉 Tabla Afiliados actualizada correctamente")
    
    # Verificar la nueva estructura
    cursor.execute("DESCRIBE Afiliados")
    columns = cursor.fetchall()
    print("\n📋 Nueva estructura de la tabla:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
