#!/bin/bash
# Script de verificación post-deployment
# Shosanna 🔥

API_BASE="https://ops-backend-production-e8ce.up.railway.app/api/v1"

echo "🔥 VERIFICACIÓN DE DEPLOYMENT - Operations Backend"
echo "=================================================="
echo ""

# 1. Health check
echo "1️⃣ Health Check..."
HEALTH=$(curl -s -m 10 https://ops-backend-production-e8ce.up.railway.app/health)
if [[ $HEALTH == *"ok"* ]]; then
    echo "   ✅ Backend funcionando"
else
    echo "   ❌ Backend no responde"
    echo "   Response: $HEALTH"
fi
echo ""

# 2. Verificar proyectos
echo "2️⃣ Verificando proyectos..."
PROJECTS=$(curl -s -m 10 "$API_BASE/projects" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [[ $PROJECTS -gt 0 ]]; then
    echo "   ✅ $PROJECTS proyectos disponibles"
else
    echo "   ❌ No hay proyectos"
fi
echo ""

# 3. Verificar épicas
echo "3️⃣ Verificando épicas..."
EPICS=$(curl -s -m 10 "$API_BASE/epics" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [[ $EPICS -gt 0 ]]; then
    echo "   ✅ $EPICS épicas disponibles"
else
    echo "   ⚠️  No hay épicas (puede ser normal)"
fi
echo ""

# 4. Verificar usuarios (nuevo)
echo "4️⃣ Verificando usuarios..."
USERS=$(curl -s -m 10 "$API_BASE/users" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [[ $USERS -ge 4 ]]; then
    echo "   ✅ $USERS usuarios creados (seed OK)"
else
    echo "   ❌ Solo $USERS usuarios (esperados: 4)"
fi
echo ""

# 5. Verificar equipos (nuevo)
echo "5️⃣ Verificando equipos..."
TEAMS=$(curl -s -m 10 "$API_BASE/teams" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [[ $TEAMS -ge 1 ]]; then
    echo "   ✅ $TEAMS equipos creados"
else
    echo "   ❌ No hay equipos"
fi
echo ""

# 6. Verificar transcripts (nuevo)
echo "6️⃣ Verificando transcripts..."
TRANSCRIPTS=$(curl -s -m 10 "$API_BASE/transcripts" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [[ $TRANSCRIPTS -ge 2 ]]; then
    echo "   ✅ $TRANSCRIPTS transcripts creados (seed OK)"
else
    echo "   ⚠️  Solo $TRANSCRIPTS transcripts"
fi
echo ""

# 7. Verificar Agent API (nuevo)
echo "7️⃣ Verificando Agent API..."
# Intentar registrar un agente de prueba
REGISTER_RESULT=$(curl -s -m 10 -X POST "$API_BASE/agent-api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"agent_name":"VerifyBot","permissions":"read:tasks"}' \
    | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('api_key','FAIL'))" 2>/dev/null)

if [[ $REGISTER_RESULT != "FAIL" && $REGISTER_RESULT != "" ]]; then
    echo "   ✅ Agent API funcionando (API key generada)"
else
    echo "   ❌ Agent API tiene problemas"
fi
echo ""

# 8. Verificar OpenAPI docs
echo "8️⃣ Verificando OpenAPI docs..."
DOCS=$(curl -s -m 10 https://ops-backend-production-e8ce.up.railway.app/docs)
if [[ $DOCS == *"Swagger"* ]]; then
    echo "   ✅ Swagger UI disponible en /docs"
else
    echo "   ❌ Swagger UI no disponible"
fi
echo ""

echo "=================================================="
echo "🔥 VERIFICACIÓN COMPLETADA"
echo ""
echo "📊 URLs Importantes:"
echo "   Backend:     https://ops-backend-production-e8ce.up.railway.app"
echo "   Health:      https://ops-backend-production-e8ce.up.railway.app/health"
echo "   Swagger:     https://ops-backend-production-e8ce.up.railway.app/docs"
echo "   API Base:    $API_BASE"
