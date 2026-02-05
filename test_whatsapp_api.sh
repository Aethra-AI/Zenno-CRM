#!/bin/bash

# Script de prueba para los nuevos endpoints de la API
# Asegúrate de tener una API Key válida y el servidor corriendo

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
API_URL="http://localhost:5000"
API_KEY="tu_api_key_aqui"  # ⚠️ CAMBIA ESTO por tu API Key real

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}Prueba de Endpoints de Candidatos${NC}"
echo -e "${YELLOW}======================================${NC}\n"

# Test 1: Buscar candidatos por nombre
echo -e "${YELLOW}Test 1: Buscar candidatos con 'Juan'${NC}"
RESPONSE=$(curl -s -X GET "${API_URL}/public-api/v1/candidates/search?q=Juan&limit=5" \
  -H "X-API-Key: ${API_KEY}")

if echo "$RESPONSE" | grep -q '"success": true'; then
    echo -e "${GREEN}✅ Búsqueda exitosa${NC}"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}❌ Error en búsqueda${NC}"
    echo "$RESPONSE"
fi

echo -e "\n---\n"

# Test 2: Validar candidato por identidad (ejemplo)
echo -e "${YELLOW}Test 2: Validar candidato por identidad${NC}"
RESPONSE=$(curl -s -X GET "${API_URL}/public-api/v1/candidates/validate?identity=0801199012345" \
  -H "X-API-Key: ${API_KEY}")

if echo "$RESPONSE" | grep -q '"success": true'; then
    echo -e "${GREEN}✅ Validación exitosa${NC}"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}❌ Error en validación${NC}"
    echo "$RESPONSE"
fi

echo -e "\n---\n"

# Test 3: Validar candidato por nombre
echo -e "${YELLOW}Test 3: Validar candidato por nombre${NC}"
RESPONSE=$(curl -s -X GET "${API_URL}/public-api/v1/candidates/validate?name=Juan%20Perez" \
  -H "X-API-Key: ${API_KEY}")

if echo "$RESPONSE" | grep -q '"success": true'; then
    echo -e "${GREEN}✅ Validación exitosa${NC}"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}❌ Error en validación${NC}"
    echo "$RESPONSE"
fi

echo -e "\n---\n"

# Test 4: Error - Sin parámetro q
echo -e "${YELLOW}Test 4: Búsqueda sin parámetro 'q' (debe fallar)${NC}"
RESPONSE=$(curl -s -X GET "${API_URL}/public-api/v1/candidates/search" \
  -H "X-API-Key: ${API_KEY}")

if echo "$RESPONSE" | grep -q '"error"'; then
    echo -e "${GREEN}✅ Error manejado correctamente${NC}"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}❌ Debería retornar error${NC}"
    echo "$RESPONSE"
fi

echo -e "\n---\n"

# Test 5: Error - Sin API Key
echo -e "${YELLOW}Test 5: Búsqueda sin API Key (debe fallar)${NC}"
RESPONSE=$(curl -s -X GET "${API_URL}/public-api/v1/candidates/search?q=test")

if echo "$RESPONSE" | grep -q '"error"'; then
    echo -e "${GREEN}✅ Error de autenticación manejado correctamente${NC}"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}❌ Debería retornar error de autenticación${NC}"
    echo "$RESPONSE"
fi

echo -e "\n${YELLOW}======================================${NC}"
echo -e "${YELLOW}Pruebas completadas${NC}"
echo -e "${YELLOW}======================================${NC}\n"
