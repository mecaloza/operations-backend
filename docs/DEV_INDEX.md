# 🔥 Development Setup - Índice

Setup completo de desarrollo ágil para Operations Backend.

## 📚 Documentación

1. **[README_DEV.md](../README_DEV.md)** - Quick start y TL;DR
2. **[DEVELOPMENT.md](DEVELOPMENT.md)** - Guía completa de desarrollo
3. **[DEVLOOP_CHEATSHEET.md](DEVLOOP_CHEATSHEET.md)** - Comandos rápidos y workflows

## 🛠️ Archivos de Configuración

### Desarrollo
- `dev_setup.sh` - Setup inicial automático
- `dev.sh` - Servidor de desarrollo con hot reload
- `validate_setup.sh` - Validar configuración

### Python
- `requirements.txt` - Dependencias de producción
- `requirements-dev.txt` - Dependencias de desarrollo

### Testing
- `pytest.ini` - Configuración de pytest
- `.coveragerc` - Configuración de coverage
- `tests/conftest.py` - Fixtures compartidos
- `tests/test_health.py` - Tests de health endpoint
- `tests/test_projects.py` - Tests de projects

### Code Quality
- `pyproject.toml` - Config de black, ruff, mypy
- `.pre-commit-config.yaml` - Pre-commit hooks
- `.gitignore` - Archivos ignorados por git

## 🚀 Quick Start

```bash
# 1. Setup inicial (primera vez)
./dev_setup.sh

# 2. Validar setup
./validate_setup.sh

# 3. Desarrollo (cada día)
source venv/bin/activate
./dev.sh
```

## 📋 Checklist de Setup

- [x] requirements.txt creado
- [x] requirements-dev.txt creado
- [x] dev_setup.sh script
- [x] dev.sh script  
- [x] validate_setup.sh script
- [x] pytest.ini configurado
- [x] pyproject.toml configurado
- [x] .pre-commit-config.yaml
- [x] .coveragerc
- [x] .gitignore actualizado
- [x] tests/conftest.py con fixtures
- [x] tests/test_health.py
- [x] tests/test_projects.py
- [x] docs/DEVELOPMENT.md
- [x] docs/DEVLOOP_CHEATSHEET.md
- [x] README_DEV.md

## 🔧 Herramientas Configuradas

### Development
- ✅ **uvicorn** - ASGI server con hot reload
- ✅ **watchfiles** - File watcher para cambios
- ✅ **ipdb** - Debugger interactivo

### Testing
- ✅ **pytest** - Framework de testing
- ✅ **pytest-asyncio** - Testing async
- ✅ **pytest-cov** - Coverage reports
- ✅ **httpx** - HTTP client para tests

### Code Quality
- ✅ **black** - Code formatter
- ✅ **ruff** - Linter (reemplaza flake8, isort, etc)
- ✅ **mypy** - Type checker
- ✅ **pre-commit** - Git hooks

## 🎯 Objetivos Logrados

### 1. ❌ RadLoop NO existe
RadLoop no es una herramienta real. En su lugar, implementamos:

### 2. ✅ Setup de Desarrollo Ágil

**Hot Reload:**
- Uvicorn con `--reload` para auto-reload en cambios
- Watchfiles como alternativa avanzada
- Recarga automática de `.py` y `.env`

**Testing:**
- Pytest configurado con async support
- Fixtures para DB y client
- Coverage tracking
- Tests de ejemplo (health, projects)

**Code Quality:**
- Black para formatting consistente
- Ruff para linting moderno
- MyPy para type checking
- Pre-commit hooks automáticos

### 3. ✅ Scripts Automatizados

- `dev_setup.sh` - Setup completo en un comando
- `dev.sh` - Dev server listo
- `validate_setup.sh` - Verificación de config

### 4. ✅ Documentación Completa

- Guía de desarrollo detallada
- Cheatsheet de comandos
- README quick start
- Inline comments en configs

## 🌟 Features Destacadas

### 🔥 Hot Reload Nativo
No necesitas herramientas externas. Uvicorn recarga en cada cambio.

### 🧪 Testing First-Class
Tests unitarios e integración con fixtures reusables.

### 🎨 Code Quality Automático
Pre-commit hooks evitan commits con código mal formateado.

### 📚 Docs Inline
Cada config tiene comments explicando qué hace.

### ⚡ Zero Config
`./dev_setup.sh` y estás listo en 30 segundos.

## 🔄 Workflow Típico

```bash
# Terminal 1: Dev server
./dev.sh

# Terminal 2: Tests
pytest --watch

# Editas código → Guardas → Server recarga → Tests corren
# Loop infinito de productividad 🔥
```

## 📊 Métricas de Calidad

**Configurado:**
- Coverage goal: >80%
- Black line length: 100
- Ruff: estricto
- Pre-commit: black + ruff + mypy

**Comandos rápidos:**
```bash
pytest --cov=.              # Coverage
black . --check             # Format check
ruff check .                # Lint
mypy .                      # Type check
```

## 🚀 Deploy

```bash
# Local validation
pytest && black . --check && ruff check .

# Deploy a Railway
railway up --detach
```

## 📖 Lectura Recomendada

**Para empezar:**
1. [README_DEV.md](../README_DEV.md) - 2 minutos
2. Ejecuta `./dev_setup.sh`
3. Ejecuta `./dev.sh`

**Para profundizar:**
1. [DEVELOPMENT.md](DEVELOPMENT.md) - Guía completa (15 min)
2. [DEVLOOP_CHEATSHEET.md](DEVLOOP_CHEATSHEET.md) - Referencia rápida

**Cuando necesites algo:**
- Busca en DEVLOOP_CHEATSHEET.md primero
- Luego en DEVELOPMENT.md
- Luego en el código (está comentado)

## 🆘 Troubleshooting

**"No funciona nada"**
```bash
./validate_setup.sh
```

**"Module not found"**
```bash
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

**"Tests fallan"**
```bash
rm operations.db
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
pytest
```

## 🎓 Aprendizajes

### Lo que SÍ implementamos
- Hot reload con uvicorn (nativo FastAPI)
- Testing comprehensivo con pytest
- Code quality con black + ruff
- Pre-commit hooks automáticos
- Scripts bash para automatización
- Docs extensivas

### Lo que NO es necesario
- RadLoop (no existe)
- Herramientas complejas de hot reload
- Configuraciones manuales repetitivas
- Setup manual de DB
- Documentación dispersa

### Resultado
**Setup moderno, rápido, bien documentado, y totalmente funcional.**

---

**Hecho con 🔥 por Shosanna**

**Stack:** FastAPI • Pytest • Black • Ruff • Uvicorn

**Filosofía:** Automatiza todo. Documenta todo. Zero friction.
