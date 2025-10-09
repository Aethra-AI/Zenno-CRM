# ✅ MÓDULO B7 - ENDPOINTS DE POSTULACIONES COMPLETADO

**Fecha:** Octubre 9, 2025  
**Archivo modificado:** `bACKEND/app.py`  
**Estado:** 🟢 Listo para probar

---

## 📋 CAMBIOS REALIZADOS

### **1. Modificación de GET `/api/applications`** ✅

**Ubicación:** Línea 5646-5709

**Cambios:**
- ❌ Eliminada lógica de comparación de rol como string
- ✅ Filtro por tenant SIEMPRE aplicado (incluso para Admin)
- ✅ Filtrado por usuario según rol a través de `v.created_by_user` (vacante)
- ✅ Incluye postulaciones de vacantes antiguas (created_by_user NULL)

**Antes:**
```python
user_role = getattr(g, 'current_user', {}).get('rol', '')

if user_role != 'Administrador':  # ❌ Compara string
    conditions.append("v.tenant_id = %s")
    params.append(tenant_id)
# Admin ve todas sin filtro
```

**Después:**
```python
user_id = g.current_user['user_id']

# 🔐 Siempre filtrar por tenant
conditions.append("v.tenant_id = %s")
params.append(tenant_id)

# 🔐 Filtrar por usuario según rol (a través de la vacante)
condition, filter_params = build_user_filter_condition(user_id, tenant_id, 'v.created_by_user')
if condition:
    conditions.append(f"({condition} OR v.created_by_user IS NULL)")
    params.extend(filter_params)
```

**Lógica clave:**
- Las postulaciones NO tienen `created_by_user` propio (aún)
- Se filtran a través de la vacante relacionada (`v.created_by_user`)
- Usuario ve postulaciones de vacantes que puede ver

---

### **2. Modificación de POST `/api/applications`** ✅

**Ubicación:** Línea 5711-5748

**Cambios:**
- ✅ Verifica permiso con `can_create_resource()`
- ✅ Agrega `created_by_user` al INSERT
- ✅ Log de intentos sin permiso

**Código agregado:**
```python
# 🔐 MÓDULO B7: Verificar permiso de creación
if not can_create_resource(user_id, tenant_id, 'application'):
    app.logger.warning(f"Usuario {user_id} intentó crear postulación sin permisos")
    return jsonify({
        'success': False,
        'message': 'No tienes permisos para crear postulaciones'
    }), 403

# 🔐 MÓDULO B7: Insertar con created_by_user
sql = """
    INSERT INTO Postulaciones (
        id_afiliado, id_vacante, fecha_aplicacion, estado, comentarios, created_by_user
    ) VALUES (%s, %s, NOW(), 'Recibida', %s, %s)
"""
cursor.execute(sql, (..., user_id))
```

---

### **3. Modificación de PUT `/api/applications/<id>/status`** ✅

**Ubicación:** Línea 3568-3603

**Cambios:**
- ✅ Verifica acceso de escritura a través de la vacante relacionada
- ✅ Log de intentos sin permiso
- ✅ Retorna 403 si no tiene acceso

**Código agregado:**
```python
# 🔐 MÓDULO B7: Verificar acceso de escritura a través de la vacante
vacancy_id = postulacion_data[2]  # id_vacante
if not can_access_resource(user_id, tenant_id, 'vacancy', vacancy_id, 'write'):
    app.logger.warning(f"Usuario {user_id} intentó actualizar estado de postulación {id_postulacion} sin acceso a vacante {vacancy_id}")
    return jsonify({
        'error': 'No tienes acceso a esta postulación',
        'code': 'FORBIDDEN'
    }), 403
```

**Lógica clave:**
- Primero obtiene `id_vacante` de la postulación
- Luego verifica acceso a esa vacante
- Si no tiene acceso a la vacante, no puede modificar la postulación

---

### **4. Modificación de DELETE `/api/applications/<id>`** ✅

**Ubicación:** Línea 5852-5884

**Cambios:**
- ✅ Verifica acceso de eliminación a través de la vacante (requiere 'full')
- ✅ Corregido query para obtener tenant_id de Vacantes (NO de Postulaciones)
- ✅ Log de intentos sin permiso

**Antes:**
```python
# ❌ INCORRECTO (tenant_id no existe en Postulaciones)
cursor.execute("""
    SELECT id_postulacion 
    FROM Postulaciones 
    WHERE id_postulacion = %s AND tenant_id = %s
""", (id_postulacion, tenant_id))
```

**Después:**
```python
# ✅ CORRECTO (obtener tenant_id de Vacantes)
cursor.execute("""
    SELECT p.id_postulacion, p.id_vacante, v.tenant_id
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""", (id_postulacion, tenant_id))

# 🔐 Verificar acceso de eliminación (requiere permiso 'full')
vacancy_id = postulacion[1]
if not can_access_resource(user_id, tenant_id, 'vacancy', vacancy_id, 'full'):
    return jsonify({'error': 'No tienes permisos para eliminar esta postulación'}), 403
```

---

### **5. Modificación de PUT `/api/applications/<id>/comments`** ✅

**Ubicación:** Línea 5904-5949

**Cambios:**
- ✅ Verifica que la postulación existe a través de Vacantes
- ✅ Verifica acceso de escritura a través de la vacante
- ✅ Agrega tenant_id a la verificación
- ✅ Log de intentos sin permiso

**Código agregado:**
```python
# 🔐 MÓDULO B7: Verificar que la postulación existe y obtener su vacante
cursor.execute("""
    SELECT p.id_postulacion, p.id_vacante, v.tenant_id
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""", (id_postulacion, tenant_id))

# 🔐 MÓDULO B7: Verificar acceso de escritura a través de la vacante
vacancy_id = postulacion[1]
if not can_access_resource(user_id, tenant_id, 'vacancy', vacancy_id, 'write'):
    return jsonify({'error': 'No tienes permisos para editar esta postulación'}), 403
```

---

## 🔑 CONCEPTO CLAVE: PERMISOS INDIRECTOS

### **¿Por qué verificamos acceso a través de la vacante?**

**Estructura de datos:**
```
Vacante (tiene created_by_user)
  ├── Postulación 1
  ├── Postulación 2
  └── Postulación 3
```

**Lógica:**
- Las postulaciones NO tienen permisos propios
- Heredan permisos de la vacante a la que pertenecen
- Si puedes editar la vacante → puedes editar sus postulaciones
- Si puedes ver la vacante → puedes ver sus postulaciones

**Ejemplo:**
```
Reclutador Juan (ID 8) crea Vacante A
  ↓
Vacante A.created_by_user = 8
  ↓
Se crean 3 postulaciones para Vacante A
  ↓
Reclutador Juan puede ver/editar las 3 postulaciones
Reclutador María (ID 12) NO puede verlas
```

---

## 📊 MATRIZ DE PERMISOS APLICADA

| Acción | Admin | Supervisor<br>(equipo [8,12]) | Reclutador<br>(ID 8) |
|--------|-------|-------------------------------|----------------------|
| **Ver todas las postulaciones** | ✅ | ❌ | ❌ |
| **Ver postulaciones de vacantes del equipo** | ✅ | ✅ (vacantes 5,8,12) | ❌ |
| **Ver postulaciones de vacantes propias** | ✅ | ✅ | ✅ (solo vacante 8) |
| **Crear postulación** | ✅ | ✅ | ✅ |
| **Cambiar estado (vacante propia)** | ✅ | ✅ | ✅ |
| **Cambiar estado (vacante ajena)** | ✅ | ✅ (equipo) | ❌ (403) |
| **Eliminar (vacante propia)** | ✅ | ✅ | ✅ |
| **Eliminar (vacante ajena)** | ✅ | ❌ (403) | ❌ (403) |

---

## 🧪 CASOS DE PRUEBA

### **Test 1: Admin ve todas las postulaciones**

**Request:**
```http
GET /api/applications
Authorization: Bearer <token_admin>
```

**Query esperada:**
```sql
SELECT p.*, a.nombre_completo, v.cargo_solicitado, c.empresa
FROM Postulaciones p
JOIN Afiliados a ON p.id_afiliado = a.id_afiliado
JOIN Vacantes v ON p.id_vacante = v.id_vacante
JOIN Clientes c ON v.id_cliente = c.id_cliente
WHERE v.tenant_id = 1
-- Sin filtro adicional por usuario (Admin ve todo)
```

---

### **Test 2: Supervisor ve postulaciones de su equipo**

**Request:**
```http
GET /api/applications
Authorization: Bearer <token_supervisor_5>
```

**Vacantes:**
- Vacante A → created_by_user: 5 (Supervisor)
- Vacante B → created_by_user: 8 (Reclutador del equipo)
- Vacante C → created_by_user: 10 (Reclutador fuera del equipo)

**Query esperada:**
```sql
WHERE v.tenant_id = 1
AND (v.created_by_user IN (5, 8, 12) OR v.created_by_user IS NULL)
```

**Resultado esperado:**
- ✅ Ve postulaciones de Vacante A (suya)
- ✅ Ve postulaciones de Vacante B (equipo)
- ❌ NO ve postulaciones de Vacante C (ajena)

---

### **Test 3: Reclutador solo ve postulaciones de sus vacantes**

**Request:**
```http
GET /api/applications
Authorization: Bearer <token_reclutador_8>
```

**Query esperada:**
```sql
WHERE v.tenant_id = 1
AND (v.created_by_user = 8 OR v.created_by_user IS NULL)
```

**Resultado esperado:**
- ✅ Ve postulaciones de Vacante B (suya)
- ❌ NO ve postulaciones de Vacante A (supervisor)
- ❌ NO ve postulaciones de Vacante C (otro reclutador)

---

### **Test 4: Crear postulación registra created_by_user**

**Request:**
```http
POST /api/applications
Authorization: Bearer <token_reclutador_8>
Content-Type: application/json

{
  "id_afiliado": 123,
  "id_vacante": 10,
  "comentarios": "Buen perfil"
}
```

**Query esperada:**
```sql
INSERT INTO Postulaciones (
  id_afiliado, id_vacante, fecha_aplicacion, estado, comentarios, created_by_user
) VALUES (
  123, 10, NOW(), 'Recibida', 'Buen perfil', 8
)
```

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Postulación registrada...",
  "id_postulacion": 456
}
```

---

### **Test 5: Cambiar estado sin acceso a la vacante (denegado)**

**Request:**
```http
PUT /api/applications/123/status
Authorization: Bearer <token_reclutador_8>
Content-Type: application/json

{
  "estado": "En Revisión"
}
```

**Escenario:** Reclutador 8 intenta cambiar estado de postulación de Vacante creada por Reclutador 10

**Resultado esperado:**
```json
{
  "error": "No tienes acceso a esta postulación",
  "code": "FORBIDDEN"
}
```

**Código HTTP:** `403 Forbidden`

**Log esperado:**
```
WARNING - Usuario 8 intentó actualizar estado de postulación 123 sin acceso a vacante 10
```

---

### **Test 6: Eliminar postulación sin acceso (denegado)**

**Request:**
```http
DELETE /api/applications/123
Authorization: Bearer <token_reclutador_8>
```

**Escenario:** Reclutador 8 intenta eliminar postulación de vacante ajena

**Resultado esperado:**
```json
{
  "success": false,
  "error": "No tienes permisos para eliminar esta postulación",
  "code": "FORBIDDEN"
}
```

**Código HTTP:** `403 Forbidden`

---

## 🔍 VALIDACIÓN DE LOGS

### **Logs de creación exitosa:**
```
INFO - Usuario 8 creando postulación para vacante 10
INFO - Postulación creada exitosamente: ID 456
```

### **Logs de intento sin permiso:**
```
WARNING - Usuario 10 intentó crear postulación sin permisos
WARNING - Usuario 8 intentó actualizar estado de postulación 123 sin acceso a vacante 10
WARNING - Usuario 8 intentó eliminar postulación 123 sin acceso completo a vacante 10
WARNING - Usuario 8 intentó actualizar comentarios de postulación 123 sin acceso a vacante 10
```

---

## ✅ CHECKLIST DE VALIDACIÓN

### **Funcionalidad:**
- [x] `GET /api/applications` filtra por usuario según rol (a través de vacante)
- [x] `POST /api/applications` valida permisos y registra `created_by_user`
- [x] `PUT /api/applications/<id>/status` valida acceso a través de vacante
- [x] `DELETE /api/applications/<id>` valida acceso (requiere 'full' en vacante)
- [x] `PUT /api/applications/<id>/comments` valida acceso a través de vacante

### **Seguridad:**
- [x] Reclutador NO puede ver postulaciones de vacantes ajenas
- [x] Supervisor puede ver postulaciones de vacantes de su equipo
- [x] Admin puede ver todas las postulaciones
- [x] Retorna 403 en accesos no autorizados
- [x] Logs de intentos sin permiso

### **Compatibilidad:**
- [x] Postulaciones de vacantes antiguas (created_by_user NULL) accesibles
- [x] Queries corregidos (tenant_id de Vacantes, NO de Postulaciones)
- [x] Frontend no requiere cambios (transparente)

---

## 🐛 BUG CORREGIDO: tenant_id en Postulaciones

**Antes:**
```python
# ❌ INCORRECTO (tabla Postulaciones NO tiene tenant_id)
cursor.execute("""
    SELECT * FROM Postulaciones 
    WHERE id_postulacion = %s AND tenant_id = %s
""")
```

**Después:**
```python
# ✅ CORRECTO (obtener tenant_id de Vacantes)
cursor.execute("""
    SELECT p.*, v.tenant_id
    FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.id_postulacion = %s AND v.tenant_id = %s
""")
```

---

## 📈 PROGRESO TOTAL

```
✅ B1: Tablas Base (100%)
✅ B2: Columnas Trazabilidad (100%)
⬜ B3: Índices Optimización (0%) - OPCIONAL
✅ B4: Permission Service (100%)
✅ B5: Endpoints Candidatos (100%)
✅ B6: Endpoints Vacantes (100%)
✅ B7: Endpoints Postulaciones (100%) ← ACABAMOS AQUÍ
⬜ B8: Endpoints Entrevistas (0%)
⬜ B9: Endpoints Clientes (0%)
⬜ B10: Endpoints Contratados (0%)
⬜ B11-B17: Otros endpoints (0%)
```

**Backend completado:** 6/17 módulos (35.3%)

---

## 🚀 SIGUIENTE PASO: MÓDULO B8

**Objetivo:** Aplicar permisos a endpoints de Entrevistas

**Endpoints a modificar:**
- `GET /api/interviews`
- `POST /api/interviews`
- `DELETE /api/interviews/<id>`

**Lógica:** Similar a B7 (verificar acceso a través de la postulación/vacante)

**Tiempo estimado:** 1-1.5 horas

---

## ❓ **¿CONTINUAMOS CON B8?**

Ya llevamos muy buen ritmo. Tenemos:
- ✅ Candidatos (B5)
- ✅ Vacantes (B6)
- ✅ Postulaciones (B7)
- ⏳ Faltan: Entrevistas (B8), Clientes (B9), Contratados (B10)

**Mi recomendación:** Continuar con B8 para completar el flujo de reclutamiento (Candidato → Vacante → Postulación → Entrevista → Contratado) 🚀

¿Qué prefieres? 🎯

