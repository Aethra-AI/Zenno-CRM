#!/bin/bash

# Script de prueba con tu API Key real
# Ejecuta esto en tu VM donde corre el backend

API_KEY="hnm_live_8a5a7b54c27390ade44de69457f8b43b35f099e0373412dddb6ec575ccd04e9d"
API_URL="http://localhost:5000"

echo "=========================================="
echo "🧪 Pruebas de API WhatsApp"
echo "=========================================="
echo ""

# Test 1: Buscar candidatos
echo "1️⃣ Test: Buscar candidatos con 'Juan'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X GET "${API_URL}/public-api/v1/candidates/search?q=Juan&limit=5" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || echo "Error en la respuesta"
echo ""
echo ""

# Test 2: Validar candidato por identidad
echo "2️⃣ Test: Validar candidato por identidad"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X GET "${API_URL}/public-api/v1/candidates/validate?identity=0801199012345" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || echo "Error en la respuesta"
echo ""
echo ""

# Test 3: Validar candidato por nombre
echo "3️⃣ Test: Validar candidato por nombre"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X GET "${API_URL}/public-api/v1/candidates/validate?name=Maria" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || echo "Error en la respuesta"
echo ""
echo ""

# Test 4: Consultar vacantes
echo "4️⃣ Test: Consultar vacantes disponibles"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X GET "${API_URL}/public-api/v1/vacancies?limit=3" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || echo "Error en la respuesta"
echo ""
echo ""

# Test 5: Consultar vacantes por ciudad
echo "5️⃣ Test: Vacantes en Tegucigalpa"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X GET "${API_URL}/public-api/v1/vacancies?ciudad=Tegucigalpa&limit=3" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || echo "Error en la respuesta"
echo ""
echo ""

echo "=========================================="
echo "✅ Pruebas completadas"
echo "=========================================="
