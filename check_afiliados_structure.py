#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
from dotenv import load_dotenv
import os

def check_afiliados_structure():
    """Verificar la estructura de la tabla Afiliados"""
    
    load_dotenv()
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'crm_henmir')
        )
        cursor = conn.cursor()
        
        # Obtener estructura de la tabla Afiliados
        cursor.execute('DESCRIBE Afiliados')
        columns = cursor.fetchall()
        
        print('=== ESTRUCTURA TABLA AFILIADOS ===')
        for col in columns:
            print(f'{col[0]}: {col[1]} {col[2]} {col[3]} {col[4]} {col[5]}')
        
        # Obtener una muestra de datos
        cursor.execute('SELECT * FROM Afiliados LIMIT 1')
        sample = cursor.fetchone()
        if sample:
            print('\n=== MUESTRA DE DATOS ===')
            for i, col in enumerate(columns):
                print(f'{col[0]}: {sample[i]}')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_afiliados_structure()