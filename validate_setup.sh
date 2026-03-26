#!/bin/bash
# Validar que el setup de desarrollo está completo

set -e

echo "🔥 Validando Setup de Desarrollo"
echo "================================="
echo ""

ERRORS=0

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python: $(python3 --version)"
else
    echo "❌ Python 3 no encontrado"
    ERRORS=$((ERRORS + 1))
fi

# Check venv
if [ -d "venv" ]; then
    echo "✅ Virtual environment existe"
else
    echo "❌ Virtual environment no encontrado (ejecuta ./dev_setup.sh)"
    ERRORS=$((ERRORS + 1))
fi

# Check requirements.txt
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt existe"
else
    echo "❌ requirements.txt no encontrado"
    ERRORS=$((ERRORS + 1))
fi

# Check requirements-dev.txt
if [ -f "requirements-dev.txt" ]; then
    echo "✅ requirements-dev.txt existe"
else
    echo "❌ requirements-dev.txt no encontrado"
    ERRORS=$((ERRORS + 1))
fi

# Check .env
if [ -f ".env" ]; then
    echo "✅ .env existe"
else
    echo "⚠️  .env no encontrado (se creará en dev_setup.sh)"
fi

# Check scripts
if [ -x "dev_setup.sh" ]; then
    echo "✅ dev_setup.sh es ejecutable"
else
    echo "❌ dev_setup.sh no es ejecutable (ejecuta chmod +x dev_setup.sh)"
    ERRORS=$((ERRORS + 1))
fi

if [ -x "dev.sh" ]; then
    echo "✅ dev.sh es ejecutable"
else
    echo "❌ dev.sh no es ejecutable (ejecuta chmod +x dev.sh)"
    ERRORS=$((ERRORS + 1))
fi

# Check config files
if [ -f "pytest.ini" ]; then
    echo "✅ pytest.ini existe"
else
    echo "❌ pytest.ini no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "pyproject.toml" ]; then
    echo "✅ pyproject.toml existe"
else
    echo "❌ pyproject.toml no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ -f ".pre-commit-config.yaml" ]; then
    echo "✅ .pre-commit-config.yaml existe"
else
    echo "❌ .pre-commit-config.yaml no encontrado"
    ERRORS=$((ERRORS + 1))
fi

# Check directories
if [ -d "tests" ]; then
    echo "✅ Directorio tests/ existe"
else
    echo "❌ Directorio tests/ no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "docs" ]; then
    echo "✅ Directorio docs/ existe"
else
    echo "❌ Directorio docs/ no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "routers" ]; then
    echo "✅ Directorio routers/ existe"
else
    echo "❌ Directorio routers/ no encontrado"
    ERRORS=$((ERRORS + 1))
fi

# Check docs
if [ -f "docs/DEVELOPMENT.md" ]; then
    echo "✅ docs/DEVELOPMENT.md existe"
else
    echo "❌ docs/DEVELOPMENT.md no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "docs/DEVLOOP_CHEATSHEET.md" ]; then
    echo "✅ docs/DEVLOOP_CHEATSHEET.md existe"
else
    echo "❌ docs/DEVLOOP_CHEATSHEET.md no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "README_DEV.md" ]; then
    echo "✅ README_DEV.md existe"
else
    echo "❌ README_DEV.md no encontrado"
    ERRORS=$((ERRORS + 1))
fi

# Check test files
if [ -f "tests/test_health.py" ]; then
    echo "✅ tests/test_health.py existe"
else
    echo "❌ tests/test_health.py no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "tests/conftest.py" ]; then
    echo "✅ tests/conftest.py existe"
else
    echo "❌ tests/conftest.py no encontrado"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ Validación completa!"
    echo ""
    echo "Siguiente paso:"
    echo "  ./dev_setup.sh    # Si es primera vez"
    echo "  ./dev.sh          # Para iniciar desarrollo"
else
    echo "❌ Encontrados $ERRORS errores"
    echo ""
    echo "Ejecuta los comandos sugeridos arriba"
fi
echo "================================="
