#!/usr/bin/env python3
"""
🐛 DEBUG DE PERMISOS - Prueba directa sin HTTP
Ejecutar desde el directorio bACKEND/
"""

import sys
import os

# Asegurarse de que estamos en el directorio correcto
if not os.path.exists('permission_service.py'):
    print("❌ Este script debe ejecutarse desde el directorio bACKEND/")
    print(f"   Directorio actual: {os.getcwd()}")
    print(f"   Cambia al directorio bACKEND/ y ejecuta nuevamente")
    sys.exit(1)

# Importar módulos
try:
    from permission_service import (
        get_user_role_info,
        get_user_role_name,
        is_admin,
        is_supervisor,
        is_recruiter,
        get_accessible_user_ids,
        build_user_filter_condition
    )
    print("✅ Módulo permission_service importado correctamente")
except ImportError as e:
    print(f"❌ Error importando permission_service: {str(e)}")
    sys.exit(1)

def print_separator():
    print("\n" + "=" * 60)

def test_user(user_id, tenant_id, expected_role_type):
    """Prueba un usuario específico"""
    print_separator()
    print(f"🧪 PROBANDO USER_ID={user_id}, TENANT_ID={tenant_id}")
    print(f"   Rol esperado: {expected_role_type}")
    print("-" * 60)
    
    # 1. Obtener información completa del rol
    print("\n1️⃣ get_user_role_info():")
    role_info = get_user_role_info(user_id, tenant_id)
    if role_info:
        print(f"   ✅ Role ID: {role_info.get('role_id')}")
        print(f"   ✅ Role Name: '{role_info.get('role_name')}'")
        print(f"   ✅ Longitud: {len(role_info.get('role_name', ''))} caracteres")
        print(f"   ✅ Tiene permisos: {role_info.get('permissions') is not None}")
    else:
        print(f"   ❌ No se encontró información del rol")
        return
    
    # 2. Obtener solo el nombre del rol
    print("\n2️⃣ get_user_role_name():")
    role_name = get_user_role_name(user_id, tenant_id)
    print(f"   Resultado: '{role_name}'")
    
    # 3. Probar is_admin()
    print("\n3️⃣ is_admin():")
    admin_result = is_admin(user_id, tenant_id)
    print(f"   Resultado: {admin_result}")
    print(f"   Comparación: '{role_name}' == 'Administrador' → {role_name == 'Administrador'}")
    
    if expected_role_type == "admin":
        if admin_result:
            print("   ✅ CORRECTO: Detectado como Admin")
        else:
            print("   ❌ ERROR: Debería ser Admin pero no lo detecta")
    else:
        if not admin_result:
            print("   ✅ CORRECTO: NO es Admin")
        else:
            print("   ❌ ERROR: No debería ser Admin pero lo detecta")
    
    # 4. Probar is_supervisor()
    print("\n4️⃣ is_supervisor():")
    supervisor_result = is_supervisor(user_id, tenant_id)
    print(f"   Resultado: {supervisor_result}")
    print(f"   Comparación: '{role_name}' == 'Supervisor' → {role_name == 'Supervisor'}")
    
    if expected_role_type == "supervisor":
        if supervisor_result:
            print("   ✅ CORRECTO: Detectado como Supervisor")
        else:
            print("   ❌ ERROR: Debería ser Supervisor pero no lo detecta")
    else:
        if not supervisor_result:
            print("   ✅ CORRECTO: NO es Supervisor")
        else:
            print("   ❌ ERROR: No debería ser Supervisor pero lo detecta")
    
    # 5. Probar is_recruiter()
    print("\n5️⃣ is_recruiter():")
    recruiter_result = is_recruiter(user_id, tenant_id)
    print(f"   Resultado: {recruiter_result}")
    print(f"   Comparación: '{role_name}' == 'Reclutador' → {role_name == 'Reclutador'}")
    
    if expected_role_type == "recruiter":
        if recruiter_result:
            print("   ✅ CORRECTO: Detectado como Reclutador")
        else:
            print("   ❌ ERROR: Debería ser Reclutador pero no lo detecta")
    else:
        if not recruiter_result:
            print("   ✅ CORRECTO: NO es Reclutador")
        else:
            print("   ❌ ERROR: No debería ser Reclutador pero lo detecta")
    
    # 6. Obtener usuarios accesibles
    print("\n6️⃣ get_accessible_user_ids():")
    accessible = get_accessible_user_ids(user_id, tenant_id)
    print(f"   Resultado: {accessible}")
    
    if accessible is None:
        print("   → Admin: Ve TODOS los usuarios del tenant")
    elif len(accessible) == 1:
        print("   → Reclutador: Ve SOLO su propio perfil")
    else:
        print(f"   → Supervisor/Equipo: Ve {len(accessible)} usuarios")
    
    # 7. Construir filtro SQL
    print("\n7️⃣ build_user_filter_condition():")
    condition, params = build_user_filter_condition(user_id, tenant_id)
    print(f"   Condición SQL: '{condition}'")
    print(f"   Parámetros: {params}")
    
    if condition == "":
        print("   → Sin filtro (Admin ve todo)")
    elif "=" in condition:
        print("   → Filtro de 1 usuario (Reclutador)")
    elif "IN" in condition:
        print("   → Filtro de múltiples usuarios (Supervisor/Equipo)")
    
    # Resumen
    print("\n" + "-" * 60)
    print("📊 RESUMEN:")
    print(f"   Rol en BD: '{role_name}'")
    print(f"   is_admin: {admin_result}")
    print(f"   is_supervisor: {supervisor_result}")
    print(f"   is_recruiter: {recruiter_result}")
    print(f"   Usuarios accesibles: {accessible}")
    
    # Diagnóstico
    if expected_role_type == "admin" and not admin_result:
        print("\n⚠️  PROBLEMA DETECTADO:")
        print("   Usuario debería ser Admin pero no lo detecta")
        print("   Revisar función is_admin()")
    elif expected_role_type == "recruiter" and not recruiter_result:
        print("\n⚠️  PROBLEMA DETECTADO:")
        print("   Usuario debería ser Reclutador pero no lo detecta")
        print("   Revisar función is_recruiter()")
    elif expected_role_type == "admin" and accessible is not None:
        print("\n⚠️  PROBLEMA DETECTADO:")
        print("   Admin debería retornar None (ve todos) pero retorna lista")
    elif expected_role_type == "recruiter" and accessible != [user_id]:
        print("\n⚠️  PROBLEMA DETECTADO:")
        print(f"   Reclutador debería retornar [{user_id}] pero retorna {accessible}")
    else:
        print("\n✅ TODO CORRECTO para este usuario")

def main():
    """Ejecutar pruebas"""
    print("=" * 60)
    print("🐛 DEBUG DE PERMISOS - PRUEBA DIRECTA")
    print("=" * 60)
    
    # CONFIGURACIÓN - CAMBIAR SEGÚN TUS USUARIOS REALES
    print("\n📝 Configura los IDs de tus usuarios de prueba:")
    print("   (Presiona Enter para usar valores por defecto)")
    
    # Usuario Admin
    admin_id = input("\n👑 ID del usuario Admin (default 1): ").strip()
    admin_id = int(admin_id) if admin_id else 1
    
    # Usuario Reclutador
    recruiter_id = input("👤 ID del usuario Reclutador (default 2): ").strip()
    recruiter_id = int(recruiter_id) if recruiter_id else 2
    
    # Usuario Supervisor (opcional)
    supervisor_input = input("👔 ID del usuario Supervisor (Enter para omitir): ").strip()
    supervisor_id = int(supervisor_input) if supervisor_input else None
    
    # Tenant ID
    tenant_id = input("🏢 Tenant ID (default 1): ").strip()
    tenant_id = int(tenant_id) if tenant_id else 1
    
    # Ejecutar pruebas
    print("\n" + "=" * 60)
    print("INICIANDO PRUEBAS...")
    print("=" * 60)
    
    # Probar Admin
    test_user(admin_id, tenant_id, "admin")
    
    # Probar Reclutador
    test_user(recruiter_id, tenant_id, "recruiter")
    
    # Probar Supervisor (si se proporcionó)
    if supervisor_id:
        test_user(supervisor_id, tenant_id, "supervisor")
    
    # Resumen final
    print_separator()
    print("🎯 DIAGNÓSTICO FINAL")
    print("=" * 60)
    print("\nSi ves algún '❌ ERROR' arriba, ese es el problema.")
    print("\nPosibles problemas:")
    print("1. Función is_admin() no detecta al Admin correctamente")
    print("2. Función is_recruiter() no detecta al Reclutador correctamente")
    print("3. get_accessible_user_ids() retorna valores incorrectos")
    print("4. Las comparaciones de strings tienen problema")
    print("\nRevisa las líneas con ❌ para ver qué está fallando.")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()




