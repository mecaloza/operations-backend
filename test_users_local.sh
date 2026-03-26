#!/bin/bash
# Test local de endpoints de Users y Teams
# Requiere que el servidor esté corriendo en http://localhost:8000

BASE_URL="http://localhost:8000/api/v1"

echo "🔥 Testing Users & Teams Endpoints"
echo ""

# 1. Listar usuarios
echo "📋 GET /users - Listar usuarios"
curl -s "$BASE_URL/users" | python3 -m json.tool | head -20
echo ""

# 2. Listar equipos
echo "📋 GET /teams - Listar equipos"
curl -s "$BASE_URL/teams" | python3 -m json.tool
echo ""

# 3. Crear usuario de prueba
echo "➕ POST /users - Crear usuario test"
curl -s -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ops.dev",
    "username": "testuser",
    "full_name": "Test User",
    "password": "test123",
    "role": "member",
    "team_id": 1
  }' | python3 -m json.tool
echo ""

# 4. Obtener usuario por ID
echo "🔍 GET /users/1 - Detalle de usuario"
curl -s "$BASE_URL/users/1" | python3 -m json.tool
echo ""

# 5. Asignar agente a usuario
echo "🔗 POST /users/1/assign-agent/1 - Asignar agente"
curl -s -X POST "$BASE_URL/users/1/assign-agent/1" | python3 -m json.tool
echo ""

# 6. Listar agentes del usuario
echo "📋 GET /users/1/agents - Agentes del usuario"
curl -s "$BASE_URL/users/1/agents" | python3 -m json.tool
echo ""

# 7. Listar miembros del equipo
echo "📋 GET /teams/1/members - Miembros del equipo"
curl -s "$BASE_URL/teams/1/members" | python3 -m json.tool
echo ""

echo "✅ Tests completados"
