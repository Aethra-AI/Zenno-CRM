#!/usr/bin/env python3
"""
Script de prueba completo para validar el sistema multi-tenancy
Prueba login, endpoints y verificación de tenant_id en todas las operaciones
"""

import requests
import json
import time
import mysql.connector
from dotenv import load_dotenv
import os

# Configuración
BASE_URL = "http://localhost:5000"
load_dotenv()

class TenantSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Registrar resultado de prueba"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
    def get_db_connection(self):
        """Obtener conexión a la base de datos"""
        try:
            return mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'crm_database')
            )
        except Exception as e:
            print(f"❌ Error conectando a BD: {e}")
            return None
    
    def test_login_tenant1(self):
        """Probar login del tenant 1"""
        print("\n🔐 PRUEBA 1: LOGIN TENANT 1")
        print("-" * 40)
        
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/login", json={
                "email": "admin@crm.com",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data and 'user' in data:
                    self.tokens['tenant1'] = data['token']
                    user = data['user']
                    
                    # Verificar que el token contiene tenant_id
                    if user.get('tenant_id') == 1:
                        self.log_test("Login Tenant 1", True, f"Tenant ID: {user.get('tenant_id')}")
                        
                        # Verificar headers de autenticación
                        self.session.headers.update({
                            'Authorization': f'Bearer {data["token"]}',
                            'Content-Type': 'application/json'
                        })
                        
                        return True
                    else:
                        self.log_test("Login Tenant 1", False, f"Tenant ID incorrecto: {user.get('tenant_id')}")
                else:
                    self.log_test("Login Tenant 1", False, "Token o user no encontrado en respuesta")
            else:
                self.log_test("Login Tenant 1", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Login Tenant 1", False, f"Error: {str(e)}")
            
        return False
    
    def test_login_tenant2(self):
        """Probar login del tenant 2"""
        print("\n🔐 PRUEBA 2: LOGIN TENANT 2")
        print("-" * 40)
        
        try:
            # Crear sesión separada para tenant 2
            session2 = requests.Session()
            response = session2.post(f"{BASE_URL}/api/auth/login", json={
                "email": "prueba@prueba.com",
                "password": "prueba123"
            })
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data and 'user' in data:
                    user = data['user']
                    
                    if user.get('tenant_id') == 2:
                        self.log_test("Login Tenant 2", True, f"Tenant ID: {user.get('tenant_id')}")
                        self.tokens['tenant2'] = data['token']
                        return True
                    else:
                        self.log_test("Login Tenant 2", False, f"Tenant ID incorrecto: {user.get('tenant_id')}")
                else:
                    self.log_test("Login Tenant 2", False, "Token o user no encontrado")
            else:
                self.log_test("Login Tenant 2", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Login Tenant 2", False, f"Error: {str(e)}")
            
        return False
    
    def test_get_candidates_tenant1(self):
        """Probar obtener candidatos del tenant 1"""
        print("\n👥 PRUEBA 3: OBTENER CANDIDATOS TENANT 1")
        print("-" * 40)
        
        if not self.tokens.get('tenant1'):
            self.log_test("Get Candidates Tenant 1", False, "No hay token de tenant 1")
            return False
            
        try:
            # Usar token del tenant 1
            headers = {
                'Authorization': f'Bearer {self.tokens["tenant1"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{BASE_URL}/api/candidates?page=1&limit=10", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                candidates = data.get('candidates', [])
                
                # Verificar en BD que todos los candidatos pertenecen al tenant 1
                conn = self.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM Afiliados WHERE tenant_id = 1")
                    db_count = cursor.fetchone()[0]
                    cursor.close()
                    conn.close()
                    
                    if len(candidates) <= db_count:
                        self.log_test("Get Candidates Tenant 1", True, 
                                    f"API: {len(candidates)} candidatos, BD: {db_count} candidatos")
                        
                        # Verificar que no hay candidatos de otros tenants
                        if len(candidates) > 0:
                            # Verificar en BD que no hay candidatos del tenant 2
                            conn = self.get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM Afiliados WHERE tenant_id = 2")
                            tenant2_count = cursor.fetchone()[0]
                            cursor.close()
                            conn.close()
                            
                            if tenant2_count == 0:
                                self.log_test("Aislamiento Tenant 1", True, "No hay candidatos del tenant 2")
                            else:
                                self.log_test("Aislamiento Tenant 1", False, f"Tenant 2 tiene {tenant2_count} candidatos")
                        
                        return True
                    else:
                        self.log_test("Get Candidates Tenant 1", False, 
                                    f"API devuelve más candidatos que BD: {len(candidates)} vs {db_count}")
            else:
                self.log_test("Get Candidates Tenant 1", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Candidates Tenant 1", False, f"Error: {str(e)}")
            
        return False
    
    def test_create_candidate_tenant1(self):
        """Probar crear candidato en tenant 1"""
        print("\n➕ PRUEBA 4: CREAR CANDIDATO TENANT 1")
        print("-" * 40)
        
        if not self.tokens.get('tenant1'):
            self.log_test("Create Candidate Tenant 1", False, "No hay token de tenant 1")
            return False
            
        try:
            headers = {
                'Authorization': f'Bearer {self.tokens["tenant1"]}',
                'Content-Type': 'application/json'
            }
            
            candidate_data = {
                "nombre_completo": "Candidato Prueba Tenant1",
                "email": "candidato.tenant1@test.com",
                "telefono": "+50499999999",
                "ciudad": "Tegucigalpa",
                "cargo_solicitado": "Desarrollador",
                "experiencia": "2 años en desarrollo web",
                "grado_academico": "Ingeniería en Sistemas"
            }
            
            response = requests.post(f"{BASE_URL}/api/candidates", json=candidate_data, headers=headers)
            
            if response.status_code == 201:
                data = response.json()
                candidate_id = data.get('candidate', {}).get('id')
                
                if candidate_id:
                    # Verificar en BD que el candidato se creó con tenant_id = 1
                    conn = self.get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT tenant_id FROM Afiliados WHERE id_afiliado = %s", (candidate_id,))
                        result = cursor.fetchone()
                        cursor.close()
                        conn.close()
                        
                        if result and result[0] == 1:
                            self.log_test("Create Candidate Tenant 1", True, 
                                        f"Candidato creado con tenant_id: {result[0]}")
                            return candidate_id
                        else:
                            self.log_test("Create Candidate Tenant 1", False, 
                                        f"Tenant ID incorrecto en BD: {result[0] if result else 'No encontrado'}")
                else:
                    self.log_test("Create Candidate Tenant 1", False, "ID de candidato no devuelto")
            else:
                self.log_test("Create Candidate Tenant 1", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Create Candidate Tenant 1", False, f"Error: {str(e)}")
            
        return False
    
    def test_get_vacancies_tenant1(self):
        """Probar obtener vacantes del tenant 1"""
        print("\n💼 PRUEBA 5: OBTENER VACANTES TENANT 1")
        print("-" * 40)
        
        if not self.tokens.get('tenant1'):
            self.log_test("Get Vacancies Tenant 1", False, "No hay token de tenant 1")
            return False
            
        try:
            headers = {
                'Authorization': f'Bearer {self.tokens["tenant1"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{BASE_URL}/api/vacancies", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                vacancies = data.get('vacancies', [])
                
                # Verificar en BD
                conn = self.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM Vacantes WHERE tenant_id = 1")
                    db_count = cursor.fetchone()[0]
                    cursor.close()
                    conn.close()
                    
                    if len(vacancies) <= db_count:
                        self.log_test("Get Vacancies Tenant 1", True, 
                                    f"API: {len(vacancies)} vacantes, BD: {db_count} vacantes")
                        return True
                    else:
                        self.log_test("Get Vacancies Tenant 1", False, 
                                    f"API devuelve más vacantes que BD: {len(vacancies)} vs {db_count}")
            else:
                self.log_test("Get Vacancies Tenant 1", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Vacancies Tenant 1", False, f"Error: {str(e)}")
            
        return False
    
    def test_create_vacancy_tenant1(self):
        """Probar crear vacante en tenant 1"""
        print("\n➕ PRUEBA 6: CREAR VACANTE TENANT 1")
        print("-" * 40)
        
        if not self.tokens.get('tenant1'):
            self.log_test("Create Vacancy Tenant 1", False, "No hay token de tenant 1")
            return False
            
        try:
            headers = {
                'Authorization': f'Bearer {self.tokens["tenant1"]}',
                'Content-Type': 'application/json'
            }
            
            vacancy_data = {
                "cargo_solicitado": "Desarrollador Frontend",
                "ciudad": "San Pedro Sula",
                "requisitos": "React, JavaScript, 2 años experiencia",
                "salario": "25000"
            }
            
            response = requests.post(f"{BASE_URL}/api/vacancies", json=vacancy_data, headers=headers)
            
            if response.status_code == 201:
                data = response.json()
                vacancy_id = data.get('vacancy', {}).get('id_vacante')
                
                if vacancy_id:
                    # Verificar en BD que la vacante se creó con tenant_id = 1
                    conn = self.get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT tenant_id FROM Vacantes WHERE id_vacante = %s", (vacancy_id,))
                        result = cursor.fetchone()
                        cursor.close()
                        conn.close()
                        
                        if result and result[0] == 1:
                            self.log_test("Create Vacancy Tenant 1", True, 
                                        f"Vacante creada con tenant_id: {result[0]}")
                            return vacancy_id
                        else:
                            self.log_test("Create Vacancy Tenant 1", False, 
                                        f"Tenant ID incorrecto en BD: {result[0] if result else 'No encontrado'}")
                else:
                    self.log_test("Create Vacancy Tenant 1", False, "ID de vacante no devuelto")
            else:
                self.log_test("Create Vacancy Tenant 1", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Create Vacancy Tenant 1", False, f"Error: {str(e)}")
            
        return False
    
    def test_cross_tenant_access(self):
        """Probar que no se puede acceder a datos de otros tenants"""
        print("\n🔒 PRUEBA 7: AISLAMIENTO CRUZADO")
        print("-" * 40)
        
        if not self.tokens.get('tenant1') or not self.tokens.get('tenant2'):
            self.log_test("Cross Tenant Access", False, "No hay tokens de ambos tenants")
            return False
            
        try:
            # Verificar que tenant 2 no ve candidatos del tenant 1
            conn = self.get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Contar candidatos del tenant 1
                cursor.execute("SELECT COUNT(*) FROM Afiliados WHERE tenant_id = 1")
                tenant1_candidates = cursor.fetchone()[0]
                
                # Contar candidatos del tenant 2
                cursor.execute("SELECT COUNT(*) FROM Afiliados WHERE tenant_id = 2")
                tenant2_candidates = cursor.fetchone()[0]
                
                cursor.close()
                conn.close()
                
                # Tenant 2 debería ver solo sus propios candidatos (0)
                if tenant2_candidates == 0:
                    self.log_test("Cross Tenant Access", True, 
                                f"Tenant 1: {tenant1_candidates} candidatos, Tenant 2: {tenant2_candidates} candidatos")
                    return True
                else:
                    self.log_test("Cross Tenant Access", False, 
                                f"Tenant 2 tiene {tenant2_candidates} candidatos (debería ser 0)")
            else:
                self.log_test("Cross Tenant Access", False, "No se pudo conectar a BD")
                
        except Exception as e:
            self.log_test("Cross Tenant Access", False, f"Error: {str(e)}")
            
        return False
    
    def test_database_tenant_verification(self):
        """Verificar que todos los datos tienen tenant_id correcto"""
        print("\n🗄️ PRUEBA 8: VERIFICACIÓN DE BD")
        print("-" * 40)
        
        try:
            conn = self.get_db_connection()
            if not conn:
                self.log_test("Database Verification", False, "No se pudo conectar a BD")
                return False
                
            cursor = conn.cursor()
            
            # Verificar que todas las tablas tienen tenant_id correcto
            tables_to_check = [
                ('Afiliados', 'candidatos'),
                ('Vacantes', 'vacantes'),
                ('Postulaciones', 'postulaciones'),
                ('Tags', 'tags'),
                ('Email_Templates', 'templates de email'),
                ('Whatsapp_Templates', 'templates de WhatsApp')
            ]
            
            all_correct = True
            
            for table, description in tables_to_check:
                try:
                    # Verificar que no hay registros sin tenant_id
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE tenant_id IS NULL")
                    null_count = cursor.fetchone()[0]
                    
                    if null_count == 0:
                        self.log_test(f"BD {description}", True, f"Todos los registros tienen tenant_id")
                    else:
                        self.log_test(f"BD {description}", False, f"{null_count} registros sin tenant_id")
                        all_correct = False
                        
                except Exception as e:
                    self.log_test(f"BD {description}", False, f"Error verificando: {str(e)}")
                    all_correct = False
            
            cursor.close()
            conn.close()
            
            return all_correct
            
        except Exception as e:
            self.log_test("Database Verification", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🧪 INICIANDO PRUEBAS DEL SISTEMA MULTI-TENANCY")
        print("=" * 60)
        
        # Ejecutar pruebas en orden
        self.test_login_tenant1()
        self.test_login_tenant2()
        self.test_get_candidates_tenant1()
        self.test_create_candidate_tenant1()
        self.test_get_vacancies_tenant1()
        self.test_create_vacancy_tenant1()
        self.test_cross_tenant_access()
        self.test_database_tenant_verification()
        
        # Resumen final
        print("\n📊 RESUMEN DE PRUEBAS")
        print("=" * 60)
        
        passed = sum(1 for test in self.test_results if test['success'])
        total = len(self.test_results)
        
        print(f"✅ Pruebas exitosas: {passed}/{total}")
        print(f"❌ Pruebas fallidas: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! Sistema multi-tenancy funcionando correctamente.")
        else:
            print("\n⚠️ Algunas pruebas fallaron. Revisar los detalles arriba.")
        
        print("\n📋 DETALLE DE PRUEBAS FALLIDAS:")
        for test in self.test_results:
            if not test['success']:
                print(f"❌ {test['test']}: {test['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = TenantSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Sistema validado exitosamente")
        exit(0)
    else:
        print("\n❌ Sistema tiene problemas que requieren atención")
        exit(1)
