# 🔥 Development Guide - Operations Backend

Guía completa para desarrollo local del backend de Operations Dashboard.

## 📋 Tabla de Contenidos

- [Setup Inicial](#setup-inicial)
- [Desarrollo Diario](#desarrollo-diario)
- [Hot Reload](#hot-reload)
- [Testing](#testing)
- [Debugging](#debugging)
- [Linting y Formatting](#linting-y-formatting)
- [Git Workflow](#git-workflow)
- [Base de Datos](#base-de-datos)
- [Variables de Entorno](#variables-de-entorno)

---

## 🚀 Setup Inicial

### Requisitos

- Python 3.11+
- Git
- Virtual environment (venv)

### Primera vez

```bash
# Clonar el repo (si no lo tienes)
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations/backend/

# Ejecutar setup automático
chmod +x dev_setup.sh
./dev_setup.sh
```

Esto hará:
- ✅ Crear virtual environment
- ✅ Instalar dependencias de prod y dev
- ✅ Crear `.env` si no existe
- ✅ Inicializar base de datos local
- ✅ Instalar pre-commit hooks

---

## 💻 Desarrollo Diario

### Iniciar servidor de desarrollo

```bash
# Activar venv
source venv/bin/activate

# Iniciar con hot reload
chmod +x dev.sh
./dev.sh
```

El servidor estará en: **http://localhost:8000**

API docs automática: **http://localhost:8000/docs**

### Estructura de carpetas

```
backend/
├── main.py              # FastAPI app principal
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── database.py          # Configuración de DB
├── routers/             # Endpoints por recurso
│   ├── projects.py
│   ├── agents.py
│   ├── tasks.py
│   └── ...
├── tests/               # Tests
│   ├── test_health.py
│   └── test_projects.py
├── docs/                # Documentación
└── requirements*.txt    # Dependencias
```

---

## 🔥 Hot Reload

### Uvicorn Auto-reload

El script `dev.sh` usa uvicorn con `--reload`:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Qué recarga automáticamente:**
- ✅ Cambios en archivos `.py`
- ✅ Cambios en archivos `.env`
- ✅ Modificaciones en routers
- ✅ Updates de models y schemas

**Qué NO recarga:**
- ❌ Cambios en requirements.txt (necesitas reinstalar)
- ❌ Modificaciones de DB schema (necesitas migrations)

### Alternativa: watchfiles

Si necesitas más control:

```bash
watchfiles --filter python 'uvicorn main:app --reload' .
```

---

## 🧪 Testing

### Ejecutar todos los tests

```bash
pytest
```

### Tests específicos

```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Un archivo específico
pytest tests/test_health.py

# Una función específica
pytest tests/test_health.py::test_health_endpoint
```

### Coverage

```bash
# Con reporte en terminal
pytest --cov=. --cov-report=term-missing

# Generar HTML
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Escribir tests

Usa los fixtures en `tests/conftest.py`:

```python
def test_my_endpoint(client: TestClient):
    response = client.get("/api/v1/endpoint")
    assert response.status_code == 200
```

---

## 🐛 Debugging

### Con ipdb

Agrega breakpoints en tu código:

```python
import ipdb; ipdb.set_trace()
```

### Con VS Code

Crea `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

### Logs

FastAPI muestra logs automáticamente en desarrollo:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("This is info")
logger.error("This is error")
```

---

## 🎨 Linting y Formatting

### Black (formatter)

```bash
# Formatear todo
black .

# Check sin modificar
black . --check

# Un archivo específico
black main.py
```

### Ruff (linter)

```bash
# Lint todo
ruff check .

# Fix automático
ruff check . --fix

# Un archivo específico
ruff check main.py
```

### MyPy (type checking)

```bash
# Check types
mypy .

# Ignorar errores específicos
mypy . --ignore-missing-imports
```

### Pre-commit hooks

Si están instalados (con `dev_setup.sh`):

```bash
# Ejecutar manualmente
pre-commit run --all-files

# Se ejecutan automáticamente en cada commit
git commit -m "message"
```

---

## 🔀 Git Workflow

### Branches

```bash
# Feature nueva
git checkout -b feature/nombre-descriptivo

# Bugfix
git checkout -b fix/descripcion-bug

# Hotfix en prod
git checkout -b hotfix/issue-critico
```

### Commits

Mensajes descriptivos:

```bash
git commit -m "feat: agregar endpoint de tareas"
git commit -m "fix: corregir query de proyectos"
git commit -m "refactor: simplificar routers"
git commit -m "test: agregar tests de agents"
```

### Pre-push checklist

Antes de hacer push:

```bash
# 1. Tests pasan
pytest

# 2. Código formateado
black .

# 3. Sin errores de linting
ruff check .

# 4. Types OK (opcional)
mypy .
```

---

## 🗄️ Base de Datos

### Local (SQLite)

Por defecto en desarrollo:

```bash
DATABASE_URL=sqlite:///./operations.db
```

### Producción (PostgreSQL via Supabase)

En Railway:

```bash
DATABASE_URL=postgresql://postgres.xorxplnzfdnmuiecgvtt:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

### Migrations (manual)

Si cambias models:

```python
# En Python shell
from database import engine
from models import Base

# Drop y recreate (⚠️ pierdes data)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
```

### Seed data

El app hace seed automático en startup (ver `main.py` lifespan):

```python
SEED_PROJECTS = [...]
SEED_AGENTS = [...]
```

---

## 🔧 Variables de Entorno

### Archivo `.env`

```bash
# Database
DATABASE_URL=sqlite:///./operations.db

# App
ENVIRONMENT=development
DEBUG=true
PORT=8000

# CORS (opcional)
ALLOWED_ORIGINS=http://localhost:3000,https://operations-dashboard-nine.vercel.app
```

### Cargar en código

```python
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
```

El script `dev.sh` carga `.env` automáticamente.

---

## 🚀 Deploy

### Railway

```bash
# Desde el backend dir
railway up --detach
```

Railway usa:
- `requirements.txt` para dependencias
- Puerto de env var `PORT`
- PostgreSQL de Supabase

### Verificar deploy

```bash
curl https://ops-backend-production-e8ce.up.railway.app/health
```

---

## 📚 Recursos

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Pytest**: https://docs.pytest.org
- **Black**: https://black.readthedocs.io
- **Ruff**: https://docs.astral.sh/ruff

---

## 💡 Tips

### Productividad

1. **Usa los scripts**: `dev_setup.sh` y `dev.sh` automatizan todo
2. **Hot reload**: guarda y el server se actualiza solo
3. **API docs**: ve a `/docs` para probar endpoints en vivo
4. **Tests rápidos**: `pytest -x` para stop en primer error
5. **Coverage HTML**: visual para ver qué falta testear

### Debugging común

**"Module not found"**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**"Database locked"**
```bash
rm operations.db
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
```

**"Port already in use"**
```bash
lsof -ti:8000 | xargs kill -9
./dev.sh
```

---

**Hecho con 🔥 por Shosanna**
