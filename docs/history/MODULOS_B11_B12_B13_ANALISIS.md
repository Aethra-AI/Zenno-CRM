# 🔍 MÓDULOS B11, B12, B13 - ANÁLISIS CONJUNTO

**Fecha:** Octubre 9, 2025  
**Estado:** Análisis completo

---

## 📋 ENDPOINTS IDENTIFICADOS

### **MÓDULO B11: DASHBOARD (4 endpoints)**

#### 1. GET `/api/dashboard` (línea 4164)
**Situación actual:**
```python
cursor.execute("SELECT COUNT(*) FROM Entrevistas ...")
cursor.execute("SELECT ... FROM Postulaciones P JOIN Vacantes V ...")
cursor.execute("SELECT COUNT(*) FROM Afiliados ...")
# ❌ SIN filtro por tenant_id
# ❌ SIN filtro por usuario
```

**Problemas:**
- ❌ Queries sin `tenant_id`
- ❌ Muestra datos de TODOS los tenants
- ❌ No respeta jerarquía de usuarios

**Solución:**
- Agregar `WHERE tenant_id = %s` a TODOS los queries
- Aplicar `build_user_filter_condition` para filtrar por usuario según rol
- Join con created_by_user en Vacantes

---

#### 2. GET `/api/dashboard/metrics` (línea 4218)
**Situación actual:**
```python
tenant_id = get_current_tenant_id()  # ✅ Ya filtra por tenant
cursor.execute("SELECT COUNT(*) FROM Afiliados WHERE tenant_id = %s", (tenant_id,))
cursor.execute("SELECT ... FROM Vacantes WHERE tenant_id = %s", (tenant_id,))
# ✅ Ya tiene tenant_id
# ❌ NO filtra por usuario según rol
```

**Problemas:**
- ✅ Tiene filtro por `tenant_id` (BUENO)
- ❌ NO filtra por usuario según rol
- ❌ Admin, Supervisor y Reclutador ven las MISMAS métricas

**Solución:**
- Mantener filtro de tenant
- Agregar `build_user_filter_condition` para filtrar métricas según rol
- Aplicar filtro en queries de Vacantes, Postulaciones, Contratados, Clientes

---

#### 3. GET `/api/dashboard/activity_chart` (línea 7786)
**Necesita revisión** - no lo leí completo

---

#### 4. GET `/api/dashboard/stats` (línea 8337)
**Necesita revisión** - no lo leí completo

---

### **MÓDULO B12: REPORTES (1 endpoint)**

#### 1. GET `/api/reports/kpi` (línea 3688)
**Situación actual:**
```python
tenant_id = get_current_tenant_id()  # ✅ Obtiene tenant
# Pero los queries NO usan tenant_id:
cursor.execute("""
    SELECT AVG(...) FROM Vacantes 
    WHERE estado = 'Cerrada' ...
""")  # ❌ SIN filtro por tenant
cursor.execute("""
    SELECT ... FROM Postulaciones p
    JOIN Vacantes v ON ...
    GROUP BY p.estado
""")  # ❌ SIN filtro por tenant
```

**Problemas:**
- ❌ Obtiene `tenant_id` pero NO lo usa en queries
- ❌ Reportes mezclados entre tenants
- ❌ NO respeta jerarquía de usuarios

**Solución:**
- Agregar `WHERE tenant_id = %s` o `AND v.tenant_id = %s` a TODOS los queries
- Aplicar `build_user_filter_condition` para filtrar KPIs por usuario
- Métricas deben ser específicas del usuario según rol

---

### **MÓDULO B13: NOTIFICACIONES (1 endpoint)**

#### 1. GET `/api/notifications` (línea 5083)
**Situación actual:**
```python
tenant_id = get_current_tenant_id()  # ✅ Obtiene tenant
notifications = []

# 1. Nuevos candidatos
cursor.execute("""
    SELECT COUNT(*) FROM Afiliados 
    WHERE DATE(fecha_registro) = CURDATE()
""")  # ❌ SIN filtro por tenant ni usuario

# 2. Entrevistas de hoy
cursor.execute("""
    SELECT COUNT(*) FROM Entrevistas 
    WHERE DATE(fecha_hora) = CURDATE() ...
""")  # ❌ SIN filtro por tenant ni usuario

# 3. Aplicaciones pendientes
cursor.execute("""
    SELECT COUNT(*) FROM Postulaciones p
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE p.estado = 'Pendiente' ...
""")  # ❌ SIN filtro por tenant
```

**Problemas:**
- ❌ Obtiene `tenant_id` pero NO lo usa
- ❌ Notificaciones mezcladas entre tenants
- ❌ NO respeta jerarquía de usuarios

**Solución:**
- Agregar `WHERE tenant_id = %s` o `AND v.tenant_id = %s` a TODOS los queries
- Aplicar `build_user_filter_condition` para filtrar notificaciones por usuario
- Reclutadores solo ven notificaciones de SUS recursos

---

## 🔧 ESTRATEGIA DE IMPLEMENTACIÓN

### **Principio general:**
Los endpoints de Dashboard, Reportes y Notificaciones son **AGREGADOS** que muestran conteos y métricas.

**¿Cómo aplicar permisos?**
1. Admin: Ve métricas de TODO el tenant
2. Supervisor: Ve métricas de su equipo + propios
3. Reclutador: Ve métricas solo de sus recursos

**Implementación:**
- Usar `build_user_filter_condition(user_id, tenant_id, 'column_name')` en CADA query
- Filtrar por `created_by_user` en tablas principales
- Para recursos relacionados (Postulaciones, Entrevistas), filtrar a través de Vacantes

---

## 🎯 CAMBIOS ESPECÍFICOS

### **B11.1: GET `/api/dashboard`**

**Antes:**
```python
cursor.execute("""
    SELECT COUNT(*) as total FROM Entrevistas 
    WHERE fecha_hora >= CURDATE()
""")

cursor.execute("""
    SELECT V.cargo_solicitado, C.empresa, COUNT(P.id_postulacion) 
    FROM Postulaciones P 
    JOIN Vacantes V ON P.id_vacante = V.id_vacante 
    JOIN Clientes C ON V.id_cliente = C.id_cliente 
    GROUP BY V.id_vacante ...
""")

cursor.execute("""
    SELECT COUNT(*) FROM Afiliados 
    WHERE DATE(fecha_registro) = CURDATE()
""")
```

**Después:**
```python
user_id = g.current_user['user_id']
tenant_id = get_current_tenant_id()

# Filtro para Vacantes
vacancy_condition, vacancy_params = build_user_filter_condition(user_id, tenant_id, 'V.created_by_user')

# Filtro para Afiliados
candidate_condition, candidate_params = build_user_filter_condition(user_id, tenant_id, 'a.created_by_user')

# Entrevistas (filtrar a través de Vacantes)
cursor.execute("""
    SELECT COUNT(*) as total 
    FROM Entrevistas e
    JOIN Postulaciones p ON e.id_postulacion = p.id_postulacion
    JOIN Vacantes v ON p.id_vacante = v.id_vacante
    WHERE e.fecha_hora >= CURDATE() AND v.tenant_id = %s
    AND ({})
""".format(vacancy_condition or "1=1"), [tenant_id] + vacancy_params)

# Postulaciones por vacante
cursor.execute("""
    SELECT V.cargo_solicitado, C.empresa, COUNT(P.id_postulacion) 
    FROM Vacantes V
    JOIN Clientes C ON V.id_cliente = C.id_cliente
    LEFT JOIN Postulaciones P ON V.id_vacante = P.id_vacante
    WHERE V.tenant_id = %s AND ({})
    GROUP BY V.id_vacante ...
""".format(vacancy_condition or "1=1"), [tenant_id] + vacancy_params)

# Candidatos
cursor.execute("""
    SELECT COUNT(*) FROM Afiliados a
    WHERE DATE(a.fecha_registro) = CURDATE() AND a.tenant_id = %s
    AND ({})
""".format(candidate_condition or "1=1"), [tenant_id] + candidate_params)
```

---

### **B11.2: GET `/api/dashboard/metrics`**

**Cambios:**
- ✅ Ya tiene filtro por `tenant_id`
- Agregar filtro por usuario en:
  - Vacantes (`V.created_by_user`)
  - Postulaciones (a través de Vacantes)
  - Contratados (`co.created_by_user`)
  - Candidatos (`a.created_by_user`)
  - Clientes (`c.created_by_user`)

---

### **B12.1: GET `/api/reports/kpi`**

**Cambios críticos:**
- Agregar `WHERE v.tenant_id = %s` o `AND v.tenant_id = %s` a TODOS los queries
- Aplicar `build_user_filter_condition` para filtrar KPIs por usuario
- Queries de Vacantes, Postulaciones, Entrevistas, Contratados deben filtrar

**Queries a modificar:**
1. Time to fill (Vacantes)
2. Time to hire (Contratados)
3. Embudo de conversión (Postulaciones)
4. Métricas de candidatos
5. Métricas de vacantes
6. Métricas de entrevistas

---

### **B13.1: GET `/api/notifications`**

**Cambios:**
- Agregar `WHERE a.tenant_id = %s` en queries de Afiliados
- Agregar `AND v.tenant_id = %s` en queries con JOIN a Vacantes
- Aplicar `build_user_filter_condition` para filtrar por usuario

**Queries a modificar:**
1. Nuevos candidatos registrados hoy
2. Entrevistas programadas para hoy (a través de Vacantes)
3. Nuevas aplicaciones pendientes (a través de Vacantes)
4. Entrevistas sin resultado (a través de Vacantes)

---

## ⚠️ CONSIDERACIONES CRÍTICAS

### **1. Métricas agregadas vs individuales**

**Admin:**
- Métricas = TODO el tenant

**Supervisor:**
- Métricas = Su equipo + propios

**Reclutador:**
- Métricas = Solo sus recursos

---

### **2. Queries complejos con múltiples JOINs**

Para queries con múltiples tablas, aplicar filtro en la tabla principal:

```sql
SELECT ...
FROM Postulaciones p
JOIN Vacantes v ON p.id_vacante = v.id_vacante
JOIN Clientes c ON v.id_cliente = c.id_cliente
WHERE v.tenant_id = %s                     -- ← Filtro de tenant
AND (v.created_by_user = %s                -- ← Filtro de usuario
     OR v.created_by_user IN (%s, %s))     -- ← O en equipo
GROUP BY ...
```

---

### **3. Contadores en notificaciones**

Las notificaciones se crean dinámicamente basadas en contadores.
Si el contador es 0 (por permisos), NO se crea la notificación.

**Ejemplo:**
```python
# Reclutador 8 NO tiene candidatos hoy
cursor.execute("""
    SELECT COUNT(*) FROM Afiliados 
    WHERE DATE(fecha_registro) = CURDATE() 
    AND tenant_id = %s 
    AND (created_by_user = %s OR created_by_user IS NULL)
""", (tenant_id, user_id))
new_candidates = cursor.fetchone()['count']  # = 0

if new_candidates > 0:  # ← NO se ejecuta
    notifications.append(...)
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### **B11: Dashboard**
- [ ] Modificar `GET /api/dashboard` con filtros de usuario
- [ ] Modificar `GET /api/dashboard/metrics` con filtros de usuario
- [ ] Revisar `GET /api/dashboard/activity_chart`
- [ ] Revisar `GET /api/dashboard/stats`

### **B12: Reportes**
- [ ] Modificar `GET /api/reports/kpi` con filtros de tenant y usuario

### **B13: Notificaciones**
- [ ] Modificar `GET /api/notifications` con filtros de tenant y usuario

---

## 📊 IMPACTO ESPERADO

| Endpoint | Admin | Supervisor | Reclutador |
|----------|-------|------------|------------|
| **Dashboard general** | TODO | Equipo + propios | Solo propios |
| **Métricas** | TODO | Equipo + propios | Solo propios |
| **Reportes KPI** | TODO | Equipo + propios | Solo propios |
| **Notificaciones** | TODO | Equipo + propios | Solo propios |

---

## 🚨 BUGS ESPERADOS (Predicción)

### **Bug 1: Queries sin tenant_id**
**Impacto:** CRÍTICO  
**Ubicación:** `/api/dashboard`, `/api/reports/kpi`, `/api/notifications`  
**Descripción:** Múltiples queries NO filtran por `tenant_id`

---

### **Bug 2: Métricas incorrectas**
**Impacto:** ALTO  
**Descripción:** Si no filtramos, las métricas serán incorrectas para Supervisores y Reclutadores

---

**Tiempo estimado:** 2-3 horas para los 3 módulos  
**Riesgo:** Medio (queries complejos con múltiples JOINs)

**Próximo paso:** Implementar cambios en `app.py` 🚀

