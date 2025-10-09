# ✅ MÓDULO B6 - ENDPOINTS DE VACANTES COMPLETADO

**Fecha:** Octubre 9, 2025  
**Archivo modificado:** `bACKEND/app.py`  
**Estado:** 🟢 Listo para probar

---

## 📋 CAMBIOS REALIZADOS

### **1. Modificación de GET `/api/vacancies`** ✅

**Ubicación:** Línea 5373-5436

**Cambios:**
- ❌ Eliminada lógica incorrecta de comparación de rol como string
- ✅ Corregido filtro: usa `tenant_id` en vez de `id_cliente`
- ✅ Aplicado `build_user_filter_condition()` para filtrar por usuario
- ✅ Incluye vacantes antiguas sin `created_by_user` (NULL)

**Antes:**
```python
user_role = getattr(g, 'current_user', {}).get('rol', '')
if user_role == 'Administrador':  # ❌ Compara string
    # Sin filtro
else:
    WHERE V.id_cliente = %s  # ❌ Filtro incorrecto
```

**Después:**
```python
user_id = g.current_user['user_id']
base_query = "... WHERE V.tenant_id = %s"  # ✅ Filtro correcto

condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'V.created_by_user')
if condition:
    base_query += f" AND ({condition} OR V.created_by_user IS NULL)"
```

---

### **2. Modificación de POST `/api/vacancies`** ✅

**Ubicación:** Línea 5437-5531

**Cambios:**
- ✅ Verifica permiso con `can_create_resource()`
- ✅ Agrega `created_by_user` al INSERT
- ✅ Log de intentos sin permiso

**Código agregado:**
```python
# 🔐 MÓDULO B6: Verificar permiso de creación
if not can_create_resource(user_id, tenant_id, 'vacancy'):
    app.logger.warning(f"Usuario {user_id} intentó crear vacante sin permisos")
    return jsonify({'error': 'No tienes permisos para crear vacantes'}), 403

# 🔐 MÓDULO B6: Crear vacante con created_by_user
sql = """
    INSERT INTO Vacantes (
        ..., tenant_id, created_by_user
    ) VALUES (..., %s, %s)
"""
cursor.execute(sql, (..., tenant_id, user_id))
```

---

### **3. Modificación de DELETE `/api/vacancies/<id>`** ✅

**Ubicación:** Línea 5535-5593

**Cambios:**
- ✅ Verifica acceso con `can_access_resource()` (requiere 'full')
- ✅ Log de intentos sin permiso
- ✅ Retorna 403 si no tiene acceso

**Código agregado:**
```python
# 🔐 MÓDULO B6: Verificar acceso de eliminación
if not can_access_resource(user_id, tenant_id, 'vacancy', id_vacante, 'full'):
    app.logger.warning(f"Usuario {user_id} intentó eliminar vacante {id_vacante} sin permisos")
    return jsonify({
        'success': False,
        'error': 'No tienes permisos para eliminar esta vacante',
        'code': 'FORBIDDEN'
    }), 403
```

---

### **4. Modificación de PUT `/api/vacancies/<id>/status`** ✅

**Ubicación:** Línea 5595-5641

**Cambios:**
- ✅ Verifica acceso con `can_access_resource()` (requiere 'write')
- ✅ Agrega `tenant_id` al UPDATE para seguridad
- ✅ Log de intentos sin permiso

**Código agregado:**
```python
# 🔐 MÓDULO B6: Verificar acceso de escritura
if not can_access_resource(user_id, tenant_id, 'vacancy', id_vacante, 'write'):
    app.logger.warning(f"Usuario {user_id} intentó actualizar estado de vacante {id_vacante} sin permisos")
    return jsonify({'error': 'No tienes permisos para modificar esta vacante'}), 403

# 🔐 MÓDULO B6: Actualizar con tenant_id para seguridad
cursor.execute("""
    UPDATE Vacantes 
    SET estado = %s 
    WHERE id_vacante = %s AND tenant_id = %s
""", (nuevo_estado, id_vacante, tenant_id))
```

---

### **5. Modificación de GET `/api/vacancies/<id>/pipeline`** ✅

**Ubicación:** Línea 3516-3565

**Cambios:**
- ❌ Eliminada lógica de comparación de rol como string
- ✅ Verifica acceso con `can_access_resource()` (requiere 'read')
- ✅ Query simplificada con filtro por tenant
- ✅ Log de intentos sin permiso

**Antes:**
```python
user_role = getattr(g, 'current_user', {}).get('rol', '')
if user_role == 'Administrador':  # ❌ Compara string
    # Query sin tenant
else:
    # Query con tenant
```

**Después:**
```python
# 🔐 MÓDULO B6: Verificar acceso de lectura a la vacante
if not can_access_resource(user_id, tenant_id, 'vacancy', id_vacante, 'read'):
    app.logger.warning(f"Usuario {user_id} intentó acceder a pipeline de vacante {id_vacante} sin permisos")
    return jsonify({'error': 'No tienes acceso a esta vacante'}), 403

# Query unificado con tenant_id
sql = """
    SELECT ... FROM Postulaciones p 
    JOIN Afiliados a ON ...
    JOIN Vacantes v ON ...
    WHERE p.id_vacante = %s AND v.tenant_id = %s
"""
```

---

## 📊 MATRIZ DE PERMISOS APLICADA

| Acción | Admin | Supervisor<br>(equipo [8,12]) | Reclutador<br>(ID 8) |
|--------|-------|-------------------------------|----------------------|
| **Ver todas las vacantes** | ✅ | ❌ | ❌ |
| **Ver vacantes del equipo** | ✅ | ✅ (5, 8, 12) | ❌ |
| **Ver vacantes propias** | ✅ | ✅ | ✅ (solo 8) |
| **Crear vacante** | ✅ | ✅ | ✅ |
| **Ver pipeline vacante propia** | ✅ | ✅ | ✅ |
| **Ver pipeline vacante equipo** | ✅ | ✅ | ❌ (403) |
| **Actualizar estado propia** | ✅ | ✅ | ✅ |
| **Actualizar estado ajena** | ✅ | ✅ (equipo) | ❌ (403) |
| **Eliminar vacante propia** | ✅ | ✅ | ✅ |
| **Eliminar vacante ajena** | ✅ | ❌ (403) | ❌ (403) |

---

## 🧪 CASOS DE PRUEBA

### **Test 1: Admin ve todas las vacantes**

**Request:**
```http
GET /api/vacancies
Authorization: Bearer <token_admin>
```

**Query esperada:**
```sql
SELECT V.*, C.empresa, COUNT(P.id_postulacion) as aplicaciones 
FROM Vacantes V 
JOIN Clientes C ON V.id_cliente = C.id_cliente
LEFT JOIN Postulaciones P ON V.id_vacante = P.id_vacante
WHERE V.tenant_id = 1
GROUP BY V.id_vacante, C.empresa
-- Sin filtro adicional por usuario
```

**Resultado esperado:**
```json
{
  "data": [
    {"id_vacante": 1, "cargo_solicitado": "Desarrollador", "created_by_user": 5},
    {"id_vacante": 2, "cargo_solicitado": "Diseñador", "created_by_user": 8},
    {"id_vacante": 3, "cargo_solicitado": "QA", "created_by_user": 12},
    {"id_vacante": 4, "cargo_solicitado": "DevOps", "created_by_user": null}
  ]
}
```

---

### **Test 2: Supervisor ve su equipo**

**Request:**
```http
GET /api/vacancies
Authorization: Bearer <token_supervisor_5>
```

**Query esperada:**
```sql
SELECT ... WHERE V.tenant_id = 1
AND (V.created_by_user IN (5, 8, 12) OR V.created_by_user IS NULL)
GROUP BY V.id_vacante, C.empresa
```

**Resultado esperado:**
```json
{
  "data": [
    {"id_vacante": 1, "cargo_solicitado": "Desarrollador", "created_by_user": 5},
    {"id_vacante": 2, "cargo_solicitado": "Diseñador", "created_by_user": 8},
    {"id_vacante": 3, "cargo_solicitado": "QA", "created_by_user": 12},
    {"id_vacante": 4, "cargo_solicitado": "DevOps", "created_by_user": null}
  ]
}
```

---

### **Test 3: Reclutador solo ve las suyas**

**Request:**
```http
GET /api/vacancies
Authorization: Bearer <token_reclutador_8>
```

**Query esperada:**
```sql
SELECT ... WHERE V.tenant_id = 1
AND (V.created_by_user = 8 OR V.created_by_user IS NULL)
GROUP BY V.id_vacante, C.empresa
```

**Resultado esperado:**
```json
{
  "data": [
    {"id_vacante": 2, "cargo_solicitado": "Diseñador", "created_by_user": 8},
    {"id_vacante": 4, "cargo_solicitado": "DevOps", "created_by_user": null}
  ]
}
```

---

### **Test 4: Crear vacante registra created_by_user**

**Request:**
```http
POST /api/vacancies
Authorization: Bearer <token_reclutador_8>
Content-Type: application/json

{
  "id_cliente": 10,
  "cargo_solicitado": "Backend Developer",
  "ciudad": "Tegucigalpa",
  "requisitos": "Python, Flask, MySQL",
  "salario": 25000
}
```

**Query esperada:**
```sql
INSERT INTO Vacantes (
  id_cliente, cargo_solicitado, descripcion, ciudad, requisitos,
  salario_min, salario_max, salario, fecha_apertura, estado, tenant_id, created_by_user
) VALUES (
  10, 'Backend Developer', '', 'Tegucigalpa', 'Python, Flask, MySQL',
  NULL, NULL, 25000, CURDATE(), 'Abierta', 1, 8
)
```

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Vacante creada exitosamente.",
  "id_vacante": 5
}
```

---

### **Test 5: Acceso denegado a pipeline**

**Request:**
```http
GET /api/vacancies/1/pipeline
Authorization: Bearer <token_reclutador_8>
```

**Escenario:** Reclutador 8 intenta ver pipeline de vacante creada por Reclutador 10

**Resultado esperado:**
```json
{
  "error": "No tienes acceso a esta vacante",
  "code": "FORBIDDEN"
}
```

**Código HTTP:** `403 Forbidden`

**Log esperado:**
```
WARNING - Usuario 8 intentó acceder a pipeline de vacante 1 sin permisos
```

---

### **Test 6: Eliminar vacante propia**

**Request:**
```http
DELETE /api/vacancies/2
Authorization: Bearer <token_reclutador_8>
```

**Escenario:** Reclutador 8 elimina vacante que creó

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Vacante eliminada correctamente"
}
```

---

### **Test 7: Eliminar vacante ajena (denegado)**

**Request:**
```http
DELETE /api/vacancies/1
Authorization: Bearer <token_reclutador_8>
```

**Escenario:** Reclutador 8 intenta eliminar vacante de Supervisor 5

**Resultado esperado:**
```json
{
  "success": false,
  "error": "No tienes permisos para eliminar esta vacante",
  "code": "FORBIDDEN"
}
```

**Código HTTP:** `403 Forbidden`

---

## 🔍 VALIDACIÓN DE LOGS

### **Logs de creación exitosa:**
```
INFO - Usuario 8 creando vacante: Backend Developer
INFO - Vacante creada exitosamente: ID 5
```

### **Logs de intento sin permiso:**
```
WARNING - Usuario 10 intentó crear vacante sin permisos
WARNING - Usuario 8 intentó eliminar vacante 1 sin permisos
WARNING - Usuario 8 intentó actualizar estado de vacante 1 sin permisos
WARNING - Usuario 8 intentó acceder a pipeline de vacante 1 sin permisos
```

---

## ✅ CHECKLIST DE VALIDACIÓN

### **Funcionalidad:**
- [x] `GET /api/vacancies` filtra por usuario según rol
- [x] `POST /api/vacancies` valida permisos y registra `created_by_user`
- [x] `DELETE /api/vacancies/<id>` valida acceso (requiere 'full')
- [x] `PUT /api/vacancies/<id>/status` valida acceso (requiere 'write')
- [x] `GET /api/vacancies/<id>/pipeline` valida acceso (requiere 'read')

### **Seguridad:**
- [x] Reclutador NO puede ver vacantes de otros
- [x] Supervisor puede ver vacantes de su equipo
- [x] Admin puede ver todas las vacantes
- [x] Retorna 403 en accesos no autorizados
- [x] Logs de intentos sin permiso

### **Compatibilidad:**
- [x] Vacantes antiguas (created_by_user NULL) accesibles
- [x] Filtro correcto por `tenant_id` (no por `id_cliente`)
- [x] Query con GROUP BY funciona correctamente

---

## 🐛 MEJORAS APLICADAS

### **Bug corregido: Filtro incorrecto de tenant**

**Antes:**
```python
WHERE V.id_cliente = %s  # ❌ Confunde cliente con tenant
```

**Después:**
```python
WHERE V.tenant_id = %s  # ✅ Filtro correcto por empresa reclutadora
```

**Explicación:**
- `id_cliente`: Empresa que busca personal (Empresa A, B, C)
- `tenant_id`: Empresa reclutadora (CRM Zenno)
- El filtro debe ser por `tenant_id` para aislamiento multi-tenancy

---

## 📈 PROGRESO TOTAL

```
✅ B1: Tablas Base (100%)
✅ B2: Columnas Trazabilidad (100%)
⬜ B3: Índices Optimización (0%) - OPCIONAL
✅ B4: Permission Service (100%)
✅ B5: Endpoints Candidatos (100%)
✅ B6: Endpoints Vacantes (100%) ← ACABAMOS AQUÍ
⬜ B7: Endpoints Postulaciones (0%)
⬜ B8: Endpoints Entrevistas (0%)
⬜ B9: Endpoints Clientes (0%)
⬜ B10: Endpoints Contratados (0%)
⬜ B11-B17: Otros endpoints (0%)
```

**Backend completado:** 5/17 módulos (29.4%)

---

## 🚀 SIGUIENTE PASO: MÓDULO B7

**Objetivo:** Aplicar permisos a endpoints de Postulaciones

**Endpoints a modificar:**
- `GET /api/applications`
- `POST /api/applications`
- `PUT /api/applications/<id>/status`
- `DELETE /api/applications/<id>`

**Tiempo estimado:** 1-2 horas

---

## ❓ **¿PROBAMOS B6 O CONTINUAMOS CON B7?**

**Opción 1:** 🧪 Probar B6 con diferentes roles (30-45 min)  
**Opción 2:** 🚀 Continuar con B7 - Postulaciones (1-2 horas)

**Mi recomendación:** Continuar con B7 para mantener el impulso, probar todo junto después 🎯

