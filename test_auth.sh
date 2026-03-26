#!/bin/bash
# Test de autenticación del Operations Dashboard

set -e

BASE_URL="https://ops-backend-production-e8ce.up.railway.app"

echo "🔥 Testing Operations Dashboard Authentication"
echo "=============================================="
echo ""

# Test 1: Health Check
echo "✅ Test 1: Health Check"
curl -s "${BASE_URL}/health" | jq .
echo ""

# Test 2: Login con usuario admin
echo "✅ Test 2: Login (padawan - admin)"
LOGIN_RESPONSE=$(curl -s "${BASE_URL}/api/v1/auth/login" \
  -X POST \
  -d "username=padawan&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded")

echo "$LOGIN_RESPONSE" | jq .
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r .access_token)
echo ""

# Test 3: Validar token con /auth/me
echo "✅ Test 3: Get Current User (/auth/me)"
curl -s "${BASE_URL}/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# Test 4: Login con usuario leader
echo "✅ Test 4: Login (hanslanda - leader)"
curl -s "${BASE_URL}/api/v1/auth/login" \
  -X POST \
  -d "username=hanslanda&password=leader123" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq .
echo ""

# Test 5: Login con usuario member
echo "✅ Test 5: Login (shosanna - member)"
curl -s "${BASE_URL}/api/v1/auth/login" \
  -X POST \
  -d "username=shosanna&password=member123" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq .
echo ""

# Test 6: Refresh token
echo "✅ Test 6: Refresh Token"
curl -s "${BASE_URL}/api/v1/auth/refresh" \
  -X POST \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# Test 7: Login inválido (password incorrecto)
echo "❌ Test 7: Login Inválido (debe fallar)"
curl -s "${BASE_URL}/api/v1/auth/login" \
  -X POST \
  -d "username=padawan&password=wrong_password" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq .
echo ""

# Test 8: Endpoint protegido sin token
echo "❌ Test 8: Endpoint Protegido Sin Token (debe fallar)"
curl -s "${BASE_URL}/api/v1/auth/me" | jq .
echo ""

echo "=============================================="
echo "🔥 Todos los tests completados!"
