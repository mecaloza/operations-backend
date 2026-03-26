#!/bin/bash
# Test de autenticación de endpoints protegidos

set -e

BASE_URL="${BASE_URL:-https://ops-backend-production-e8ce.up.railway.app}"

echo "🔒 TESTING AUTENTICACIÓN DE ENDPOINTS"
echo "Base URL: $BASE_URL"
echo ""

# Test 1: /health debe ser público
echo "1️⃣  Testing /health (público)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$STATUS" = "200" ]; then
    echo "   ✅ /health público OK (200)"
else
    echo "   ❌ /health falló ($STATUS)"
    exit 1
fi

# Test 2: /api/v1/projects sin token debe ser 401
echo "2️⃣  Testing /api/v1/projects sin token (debe ser 401)..."
STATUS=$(curl -sL -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/projects")
if [ "$STATUS" = "401" ]; then
    echo "   ✅ /api/v1/projects protegido OK (401)"
else
    echo "   ❌ /api/v1/projects NO protegido! ($STATUS)"
    exit 1
fi

# Test 3: Login y obtener token
echo "3️⃣  Testing /api/v1/auth/login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=padawan&password=admin123")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
    echo "   ❌ Login falló"
    echo "   Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "   ✅ Login OK, token obtenido"

# Test 4: /api/v1/projects con token debe ser 200
echo "4️⃣  Testing /api/v1/projects con token (debe ser 200)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/projects")

if [ "$STATUS" = "200" ]; then
    echo "   ✅ /api/v1/projects con auth OK (200)"
else
    echo "   ❌ /api/v1/projects con token falló ($STATUS)"
    exit 1
fi

# Test 5: /api/v1/tasks sin token debe ser 401
echo "5️⃣  Testing /api/v1/tasks sin token (debe ser 401)..."
STATUS=$(curl -sL -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/tasks")
if [ "$STATUS" = "401" ]; then
    echo "   ✅ /api/v1/tasks protegido OK (401)"
else
    echo "   ❌ /api/v1/tasks NO protegido! ($STATUS)"
    exit 1
fi

# Test 6: /api/v1/dashboard/stats sin token debe ser 401
echo "6️⃣  Testing /api/v1/dashboard/stats sin token (debe ser 401)..."
STATUS=$(curl -sL -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/dashboard/stats")
if [ "$STATUS" = "401" ]; then
    echo "   ✅ /api/v1/dashboard/stats protegido OK (401)"
else
    echo "   ❌ /api/v1/dashboard/stats NO protegido! ($STATUS)"
    exit 1
fi

echo ""
echo "✅ TODOS LOS TESTS PASARON"
echo "🔒 Endpoints correctamente protegidos con JWT"
