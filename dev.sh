#!/bin/bash
# Script de desarrollo rápido con hot reload

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔥 Shosanna - Dev Server${NC}"
echo "=========================="

# Verificar venv
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment no encontrado${NC}"
    echo "Ejecuta: ./dev_setup.sh"
    exit 1
fi

# Activar venv
source venv/bin/activate

# Cargar .env si existe
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✅ Variables de entorno cargadas${NC}"
fi

# Verificar puerto (default 8000)
PORT=${PORT:-8000}

echo ""
echo -e "${YELLOW}Server config:${NC}"
echo "  Host: 0.0.0.0"
echo "  Port: $PORT"
echo "  Reload: ✅ Enabled"
echo "  DB: ${DATABASE_URL:-sqlite:///./operations.db}"
echo ""
echo -e "${GREEN}Iniciando server...${NC}"
echo "=========================="
echo ""

# Ejecutar uvicorn con reload
uvicorn main:app \
  --host 0.0.0.0 \
  --port $PORT \
  --reload \
  --reload-include "*.py" \
  --reload-include "*.env" \
  --log-level info
