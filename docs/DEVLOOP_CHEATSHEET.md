# 🔥 DevLoop Cheatsheet

Comandos rápidos para desarrollo ágil.

## 🚀 Inicio Rápido

```bash
# Activar entorno
source venv/bin/activate

# Iniciar server
./dev.sh

# En otra terminal: watch tests
pytest --watch
```

## 📝 Workflow Típico

### 1. Nueva feature

```bash
git checkout -b feature/nueva-cosa
```

### 2. Código + tests

```bash
# Edita código
vim routers/nueva_cosa.py

# Server recarga solo (gracias uvicorn --reload)

# Agrega tests
vim tests/test_nueva_cosa.py

# Corre tests
pytest tests/test_nueva_cosa.py -v
```

### 3. Quality checks

```bash
# Formatear
black .

# Lint
ruff check . --fix

# Coverage
pytest --cov=. --cov-report=term-missing
```

### 4. Commit

```bash
git add .
git commit -m "feat: agregar endpoint nueva-cosa"
```

Pre-commit hooks corren automáticamente.

---

## 🧪 Testing

```bash
# Todos
pytest

# Solo uno
pytest tests/test_health.py

# Con coverage
pytest --cov=.

# Stop en primer error
pytest -x

# Verbose
pytest -v

# Solo failed del último run
pytest --lf

# Watch mode (necesita pytest-watch)
ptw
```

---

## 🎨 Code Quality

```bash
# Black (formatter)
black .                    # Formatear todo
black main.py              # Un archivo
black . --check            # Check sin modificar

# Ruff (linter)
ruff check .               # Lint todo
ruff check . --fix         # Fix automático
ruff check main.py         # Un archivo

# MyPy (type checking)
mypy .
mypy main.py
```

---

## 🐛 Debugging

### Breakpoint en código

```python
import ipdb; ipdb.set_trace()
```

### Logs

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug info")
logger.info("Info message")
logger.warning("Warning!")
logger.error("Error occurred")
```

### Inspect request

```python
from fastapi import Request

@app.get("/endpoint")
def endpoint(request: Request):
    print(request.headers)
    print(request.query_params)
    return {"ok": True}
```

---

## 🗄️ Database

### Reset local DB

```bash
rm operations.db
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
```

### Python shell

```bash
python
>>> from database import SessionLocal, engine
>>> from models import Project, Agent, Task
>>> db = SessionLocal()
>>> projects = db.query(Project).all()
>>> print(projects)
```

### SQL directo (SQLite)

```bash
sqlite3 operations.db
sqlite> .tables
sqlite> SELECT * FROM projects;
sqlite> .quit
```

---

## 🔧 Comandos útiles

```bash
# Ver qué está usando el puerto
lsof -ti:8000

# Matar proceso en puerto
lsof -ti:8000 | xargs kill -9

# Ver logs de Railway
railway logs

# Deploy a Railway
railway up --detach

# Ver env vars
cat .env

# Reinstalar deps
pip install -r requirements.txt -r requirements-dev.txt

# Actualizar deps
pip list --outdated
pip install --upgrade package-name
```

---

## 🚀 Deploy

```bash
# Verificar antes de deploy
pytest && black . --check && ruff check .

# Deploy
railway up --detach

# Check health
curl https://ops-backend-production-e8ce.up.railway.app/health
```

---

## 🔥 Hot Reload Tips

**Lo que recarga automáticamente:**
- ✅ Archivos `.py`
- ✅ Archivos `.env`
- ✅ Cambios en routers, models, schemas

**Lo que necesita restart:**
- ❌ requirements.txt (reinstalar)
- ❌ DB schema changes (migrations)
- ❌ Cambios en config de uvicorn

**Forzar recarga:**
```bash
# Toca main.py
touch main.py
```

---

## 📊 Coverage Goals

```bash
# HTML coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

**Meta: >80% coverage**

Prioridad:
1. ✅ Endpoints críticos (projects, agents, tasks)
2. ✅ Business logic
3. ⚠️ Error handlers
4. 💭 Utils y helpers

---

## ⚡ Speed Hacks

```bash
# Alias útiles (agrega a tu .zshrc)
alias act="source venv/bin/activate"
alias dev="./dev.sh"
alias t="pytest"
alias tf="pytest --lf"  # test failed
alias tc="pytest --cov=."
alias fmt="black . && ruff check . --fix"
```

Luego:

```bash
cd backend/
act      # activa venv
dev      # lanza server
```

En otra terminal:

```bash
cd backend/
act
t        # corre tests
```

---

## 🎯 Workflow Óptimo

**Terminal 1: Dev server**
```bash
./dev.sh
```

**Terminal 2: Tests + code**
```bash
# Watch tests automático
pytest-watch

# O manual
pytest --lf -x  # solo failed, stop en error
```

**Edita código → Guarda → Server recarga → Tests corren → Repeat**

**No más restarts. No más manual refresh. Puro flujo.**

---

**Hecho con 🔥 por Shosanna**
