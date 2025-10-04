#!/usr/bin/env python3
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def check_postulaciones_structure():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'zenno_crm')
    )
    cursor = conn.cursor()
    
    print("📊 Estructura de tabla 'Postulaciones':")
    cursor.execute("DESCRIBE Postulaciones")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
    
    print("\n📝 Muestra de datos:")
    cursor.execute("SELECT * FROM Postulaciones LIMIT 2")
    samples = cursor.fetchall()
    for i, sample in enumerate(samples, 1):
        print(f"  Registro {i}: {sample}")
    
    conn.close()

if __name__ == "__main__":
    check_postulaciones_structure()
