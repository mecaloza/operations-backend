#!/bin/bash
# Setup de entorno de desarrollo para Operations Backend

set -e

echo "🔥 Shosanna - Setup de Desarrollo"
echo "=================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Crear venv si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando virtual environment..."
    python3 -m venv venv
fi

# Activar venv
echo "🔌 Activando venv..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias de producción
echo "📚 Instalando requirements.txt..."
pip install -r requirements.txt

# Instalar dependencias de desarrollo
echo "🛠️  Instalando requirements-dev.txt..."
pip install -r requirements-dev.txt

# Verificar .env
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado. Creando ejemplo..."
    cat > .env << 'EOF'
DATABASE_URL=sqlite:///./operations.db
ENVIRONMENT=development
DEBUG=true
EOF
    echo "✏️  Edita .env con tus valores"
fi

# Crear directorio de tests si no existe
if [ ! -d "tests" ]; then
    echo "📁 Creando directorio tests/..."
    mkdir -p tests
    touch tests/__init__.py
fi

# Setup de pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🪝 Instalando pre-commit hooks..."
    pre-commit install
else
    echo "ℹ️  No se encontró .pre-commit-config.yaml"
fi

# Crear DB local
echo "🗄️  Inicializando base de datos..."
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine); print('✅ DB creada')"

echo ""
echo "=================================="
echo "✅ Setup completado!"
echo ""
echo "Para iniciar desarrollo:"
echo "  source venv/bin/activate"
echo "  ./dev.sh"
echo ""
echo "Para ejecutar tests:"
echo "  pytest"
echo ""
echo "Para formatear código:"
echo "  black ."
echo "  ruff check ."
echo "=================================="
