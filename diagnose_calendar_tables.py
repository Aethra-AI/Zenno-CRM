#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para diagnosticar problemas con las tablas del calendario
"""

import mysql.connector
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'zenno_crm'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return None

def check_table_structure():
    """Verificar la estructura de las tablas del calendario"""
    print("🔍 Verificando estructura de tablas del calendario...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # 1. Verificar si las tablas existen
        print("\n1. 📋 Verificando existencia de tablas:")
        tables_to_check = ['calendar_reminders', 'interviews']
        
        for table in tables_to_check:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            result = cursor.fetchone()
            if result:
                print(f"   ✅ {table}: Existe")
            else:
                print(f"   ❌ {table}: NO EXISTE")
        
        # 2. Verificar estructura de calendar_reminders
        print("\n2. 📊 Estructura de calendar_reminders:")
        try:
            cursor.execute("DESCRIBE calendar_reminders")
            columns = cursor.fetchall()
            print("   Columnas:")
            for col in columns:
                print(f"     - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'} {col[4] if col[4] else ''}")
        except Exception as e:
            print(f"   ❌ Error obteniendo estructura: {e}")
        
        # 3. Verificar estructura de interviews
        print("\n3. 📊 Estructura de interviews:")
        try:
            cursor.execute("DESCRIBE interviews")
            columns = cursor.fetchall()
            print("   Columnas:")
            for col in columns:
                print(f"     - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'} {col[4] if col[4] else ''}")
        except Exception as e:
            print(f"   ❌ Error obteniendo estructura: {e}")
        
        # 4. Verificar datos de ejemplo
        print("\n4. 📝 Verificando datos de ejemplo:")
        try:
            cursor.execute("SELECT COUNT(*) FROM calendar_reminders")
            count = cursor.fetchone()[0]
            print(f"   - calendar_reminders: {count} registros")
            
            if count > 0:
                cursor.execute("SELECT * FROM calendar_reminders LIMIT 1")
                sample = cursor.fetchone()
                print(f"   - Muestra: {sample}")
        except Exception as e:
            print(f"   ❌ Error verificando datos: {e}")
        
        # 5. Verificar permisos del usuario
        print("\n5. 🔐 Verificando permisos del usuario:")
        try:
            cursor.execute("SELECT USER(), CURRENT_USER()")
            user_info = cursor.fetchone()
            print(f"   - Usuario actual: {user_info}")
            
            cursor.execute("SHOW GRANTS")
            grants = cursor.fetchall()
            print("   - Permisos:")
            for grant in grants[:3]:  # Solo mostrar los primeros 3
                print(f"     {grant[0]}")
        except Exception as e:
            print(f"   ❌ Error verificando permisos: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

def test_sql_queries():
    """Probar las consultas SQL que usan los endpoints"""
    print("\n6. 🧪 Probando consultas SQL de los endpoints:")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Probar consulta de recordatorios
        print("\n   📅 Probando consulta de recordatorios:")
        try:
            query = """
                SELECT r.*, u.username as created_by_name
                FROM calendar_reminders r
                LEFT JOIN users u ON r.created_by = u.id
                WHERE r.tenant_id = %s 
                AND YEAR(r.date) = %s 
                AND MONTH(r.date) = %s
                ORDER BY r.date, r.time
            """
            cursor.execute(query, (1, 2025, 9))
            results = cursor.fetchall()
            print(f"     ✅ Consulta exitosa: {len(results)} registros encontrados")
            if results:
                print(f"     - Primer registro: {results[0]}")
        except Exception as e:
            print(f"     ❌ Error en consulta: {e}")
            traceback.print_exc()
        
        # Probar consulta de entrevistas
        print("\n   🎯 Probando consulta de entrevistas:")
        try:
            query = """
                SELECT 
                    i.id,
                    i.candidate_id,
                    a.nombre_completo as candidate_name,
                    i.vacancy_id,
                    v.cargo_solicitado as vacancy_title,
                    i.interview_date as date,
                    i.interview_time as time,
                    i.status,
                    i.notes,
                    i.interviewer,
                    i.created_at
                FROM interviews i
                LEFT JOIN Afiliados a ON i.candidate_id = a.id_afiliado
                LEFT JOIN Vacantes v ON i.vacancy_id = v.id_vacante
                WHERE i.tenant_id = %s 
                AND YEAR(i.interview_date) = %s 
                AND MONTH(i.interview_date) = %s
                ORDER BY i.interview_date, i.interview_time
            """
            cursor.execute(query, (1, 2025, 9))
            results = cursor.fetchall()
            print(f"     ✅ Consulta exitosa: {len(results)} registros encontrados")
            if results:
                print(f"     - Primer registro: {results[0]}")
        except Exception as e:
            print(f"     ❌ Error en consulta: {e}")
            traceback.print_exc()
        
        # Probar consulta de actividades
        print("\n   📈 Probando consulta de actividades:")
        try:
            query = """
                SELECT 
                    CONCAT('postulation_', p.id_postulacion) as id,
                    'application' as type,
                    CONCAT('Nueva postulación: ', a.nombre_completo) as description,
                    a.nombre_completo as candidate_name,
                    v.cargo_solicitado as vacancy_title,
                    p.fecha_aplicacion as timestamp,
                    NULL as user_id,
                    'Sistema' as user_name
                FROM Postulaciones p
                LEFT JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
                LEFT JOIN Vacantes v ON p.id_vacante = v.id_vacante
                WHERE YEAR(p.fecha_aplicacion) = %s 
                AND MONTH(p.fecha_aplicacion) = %s
                LIMIT 5
            """
            cursor.execute(query, (2025, 9))
            results = cursor.fetchall()
            print(f"     ✅ Consulta exitosa: {len(results)} registros encontrados")
            if results:
                print(f"     - Primer registro: {results[0]}")
        except Exception as e:
            print(f"     ❌ Error en consulta: {e}")
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Error general en pruebas SQL: {e}")
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

def check_foreign_keys():
    """Verificar las claves foráneas y tablas relacionadas"""
    print("\n7. 🔗 Verificando claves foráneas y tablas relacionadas:")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Verificar si existe la tabla users
        cursor.execute("SHOW TABLES LIKE 'users'")
        users_exists = cursor.fetchone()
        print(f"   - Tabla 'users': {'✅ Existe' if users_exists else '❌ NO EXISTE'}")
        
        # Verificar si existe la tabla Afiliados
        cursor.execute("SHOW TABLES LIKE 'Afiliados'")
        afiliados_exists = cursor.fetchone()
        print(f"   - Tabla 'Afiliados': {'✅ Existe' if afiliados_exists else '❌ NO EXISTE'}")
        
        # Verificar si existe la tabla Vacantes
        cursor.execute("SHOW TABLES LIKE 'Vacantes'")
        vacantes_exists = cursor.fetchone()
        print(f"   - Tabla 'Vacantes': {'✅ Existe' if vacantes_exists else '❌ NO EXISTE'}")
        
        # Verificar si existe la tabla Postulaciones
        cursor.execute("SHOW TABLES LIKE 'Postulaciones'")
        postulaciones_exists = cursor.fetchone()
        print(f"   - Tabla 'Postulaciones': {'✅ Existe' if postulaciones_exists else '❌ NO EXISTE'}")
        
        # Verificar estructura de users si existe
        if users_exists:
            print("\n   📊 Estructura de tabla 'users':")
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            for col in columns:
                print(f"     - {col[0]} ({col[1]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando claves foráneas: {e}")
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Función principal de diagnóstico"""
    print("🚀 Iniciando diagnóstico completo de tablas del calendario...")
    print("=" * 60)
    
    # Ejecutar todas las verificaciones
    success = True
    
    success &= check_table_structure()
    success &= test_sql_queries()
    success &= check_foreign_keys()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Diagnóstico completado exitosamente")
        print("\n📋 Resumen:")
        print("   - Todas las verificaciones se ejecutaron")
        print("   - Revisa los resultados arriba para identificar problemas")
    else:
        print("❌ Diagnóstico completado con errores")
        print("   - Revisa los errores mostrados arriba")
    
    print("\n💡 Próximos pasos:")
    print("   1. Si hay tablas faltantes, ejecuta create_calendar_tables.py")
    print("   2. Si hay errores en consultas, verifica la estructura de las tablas")
    print("   3. Si hay problemas de permisos, verifica la configuración del usuario DB")

if __name__ == "__main__":
    main()
