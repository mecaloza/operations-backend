# Developer Guide 🛠️

Guía completa para desarrollar y desplegar el backend de Operations Dashboard.

---

## 📋 Tabla de Contenidos

- [Setup Local](#setup-local)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Base de Datos](#base-de-datos)
- [Agregar Nuevos Endpoints](#agregar-nuevos-endpoints)
- [Testing](#testing)
- [Deploy](#deploy)
- [Troubleshooting](#troubleshooting)

---

## Setup Local

### Prerrequisitos

- Python 3.11+
- pip
- Git

### 1. Clonar el Repositorio

```bash
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations
# o la ubicación de tu workspace
```

### 2. Crear Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
fastapi>=0.115.0
uvicorn[standard]>=0.31.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.0
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en el directorio `backend/`:

```bash
# backend/.env

# Database (SQLite local, PostgreSQL en producción)
DATABASE_URL=sqlite:///./operations.db

# Jira Sync (opcional)
JIRA_DOMAIN=your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Workspace (opcional, para file tree)
WORKSPACE_ROOT=/Users/lukeskywalker/.openclaw/workspace
```

**Nota:** Para producción con PostgreSQL:
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

### 5. Inicializar Base de Datos

```bash
python main.py
```

Esto:
- Crea todas las tablas (via `Base.metadata.create_all`)
- Inserta proyectos y agentes de seed

### 6. Verificar que Funciona

```bash
# En una terminal
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# En otra terminal
curl http://localhost:8000/health
# {"status":"ok"}

curl http://localhost:8000/api/v1/projects
# [{"id":1,"name":"Action Experience",...}]
```

### 7. Explorar Swagger UI

Abre en tu browser:
```
http://localhost:8000/docs
```

---

## Estructura del Proyecto

```
backend/
├── main.py              # FastAPI app, lifespan, CORS, routers
├── database.py          # Engine, SessionLocal, get_db dependency
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic request/response schemas
├── requirements.txt     # Python dependencies
├── .env                 # Variables de entorno (local)
├── .dockerignore        # Archivos ignorados en Docker build
├── Dockerfile           # Imagen Docker (para Railway)
├── operations.db        # SQLite local (git-ignored)
│
├── routers/
│   ├── __init__.py
│   ├── projects.py      # CRUD de proyectos
│   ├── agents.py        # CRUD de agentes
│   ├── tasks.py         # Tareas + kanban + bulk ops + status transitions
│   ├── epics.py         # Épicas + sub-tareas + sprint reports
│   ├── dashboard.py     # Stats globales
│   ├── comms.py         # Communication logs
│   ├── files.py         # File tree + read file
│   └── jira_sync.py     # Sincronización con Jira
│
├── docs/
│   ├── API_REFERENCE.md
│   ├── AGENT_INTEGRATION.md
│   ├── DEVELOPER_GUIDE.md (este archivo)
│   ├── SCHEMAS.md
│   └── EXAMPLES.md
│
└── .secrets/            # Opcional: secrets locales (git-ignored)
    └── jira.env
```

---

## Base de Datos

### Modelos (models.py)

```
Project (proyectos)
├── id (PK)
├── name (unique)
├── slug (unique)
├── description
├── team
├── status
└── created_at

Agent (agentes AI)
├── id (PK)
├── name (unique)
├── role
├── status
├── current_task
├── main_files
├── project_id (FK → Project)
└── created_at

Task (tareas regulares)
├── id (PK)
├── title
├── description
├── status (enum: backlog, in_progress, done, blocked)
├── priority (enum: low, medium, high, critical)
├── assigned_to
├── project_id (FK → Project)
├── jira_key (nullable, unique)
├── created_at
└── updated_at

Epic (épicas de features)
├── id (PK)
├── title
├── description
├── project_id (FK → Project)
├── target_progress (float, meta %)
├── calculated_progress (float, auto-calculado)
├── status (enum: active, completed, blocked)
├── deleted (soft delete)
├── created_at
└── updated_at

EpicTask (sub-tareas de épica)
├── id (PK)
├── title
├── epic_id (FK → Epic)
├── progress (float, 0-100)
├── assigned_to
├── status (enum: backlog, in_progress, done, qa)
├── deleted (soft delete)
├── created_at
└── updated_at

EpicProgressHistory (snapshots de progreso)
├── id (PK)
├── epic_id (FK → Epic)
├── progress (float)
└── snapshot_date

CommunicationLog (logs de comunicación)
├── id (PK)
├── from_agent
├── to_agent
├── message
├── channel
└── timestamp
```

### Relaciones

- `Project` → `Agent` (1:N)
- `Project` → `Task` (1:N)
- `Project` → `Epic` (1:N)
- `Epic` → `EpicTask` (1:N, cascade delete)
- `Epic` → `EpicProgressHistory` (1:N)

### Migraciones

**Estado actual:** No hay sistema de migraciones (Alembic).

**Proceso actual:**
1. Modifica `models.py`
2. Borra `operations.db` (local) o aplica cambios manualmente (producción)
3. Reinicia el servidor (auto-crea tablas)

**Recomendación futura:** Usar Alembic para migraciones versionadas.

```bash
# Setup Alembic (futuro)
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Seeding

El seed se ejecuta automáticamente en el `lifespan` de FastAPI:

```python
# main.py
SEED_PROJECTS = [...]
SEED_AGENTS = [...]

def _seed(db):
    # Crea proyectos y agentes si no existen
    ...

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed(db)
    finally:
        db.close()
    yield
```

Para agregar más seeds, edita las listas `SEED_PROJECTS` y `SEED_AGENTS`.

---

## Agregar Nuevos Endpoints

### Paso 1: Crear/Editar Schema (schemas.py)

```python
# schemas.py
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

### Paso 2: Crear/Editar Model (models.py)

```python
# models.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

### Paso 3: Crear Router (routers/users.py)

```python
# routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserOut

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get(
    "/",
    response_model=list[UserOut],
    summary="Listar usuarios",
    description="Obtiene todos los usuarios registrados."
)
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.post(
    "/",
    response_model=UserOut,
    status_code=201,
    summary="Crear usuario",
    description="Registra un nuevo usuario en el sistema."
)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    # Hash password (usa bcrypt en producción)
    password_hash = f"hashed_{data.password}"
    
    user = User(
        email=data.email,
        name=data.name,
        password_hash=password_hash
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Obtener usuario por ID"
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user
```

### Paso 4: Registrar Router (main.py)

```python
# main.py
from routers import users  # Importar nuevo router

app.include_router(users.router, prefix="/api/v1")
```

### Paso 5: Test

```bash
# Reinicia el servidor
uvicorn main:app --reload

# Test con curl
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"secret123"}'

curl http://localhost:8000/api/v1/users
```

### Paso 6: Documenta en Swagger

Los decoradores `summary` y `description` ya generan la documentación automáticamente.

Verifica en `http://localhost:8000/docs`.

---

## Testing

### Testing Manual con curl

Ver [EXAMPLES.md](./EXAMPLES.md) para ejemplos completos.

**Quick test:**
```bash
# Health check
curl http://localhost:8000/health

# List projects
curl http://localhost:8000/api/v1/projects

# Create task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test task",
    "description": "Testing",
    "status": "backlog",
    "priority": "medium",
    "assigned_to": "Shosanna 🔥",
    "project_id": 1
  }'
```

### Testing con Pytest (futuro)

**Setup:**
```bash
pip install pytest pytest-asyncio httpx
```

**Ejemplo de test:**
```python
# tests/test_projects.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_list_projects():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

@pytest.mark.asyncio
async def test_create_project():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/projects",
            json={
                "name": "Test Project",
                "slug": "test-project",
                "description": "Test",
                "team": "",
                "status": "active"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
```

**Ejecutar:**
```bash
pytest tests/ -v
```

---

## Deploy

### Railway (Producción Actual)

#### Setup Inicial

1. **Instala Railway CLI:**
```bash
npm install -g @railway/cli
# o
brew install railway
```

2. **Login:**
```bash
railway login
```

3. **Link al Proyecto:**
```bash
cd backend/
railway link
# Selecciona: ops-backend-production
```

#### Deploy

```bash
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations/backend
railway up --detach
```

**Proceso:**
1. Railway detecta `Dockerfile`
2. Buildea la imagen Docker
3. Deploya el contenedor
4. URL: `https://ops-backend-production-e8ce.up.railway.app`

#### Variables de Entorno

```bash
# Ver variables
railway variables

# Setear variable
railway variables set DATABASE_URL="postgresql://..."
railway variables set JIRA_DOMAIN="your-domain.atlassian.net"
```

**Variables configuradas en producción:**
- `DATABASE_URL`: PostgreSQL de Supabase
- `JIRA_DOMAIN`, `JIRA_EMAIL`, `JIRA_API_TOKEN`: Credenciales de Jira
- `WORKSPACE_ROOT`: `/workspace` (dentro del contenedor)

#### Logs

```bash
# Ver logs en tiempo real
railway logs

# Últimas 100 líneas
railway logs --limit 100
```

#### Rollback

```bash
# Ver deploys anteriores
railway status

# Rollback (via dashboard web)
# Railway > ops-backend-production > Deployments > [deploy anterior] > Redeploy
```

---

### Supabase (PostgreSQL)

**Proyecto:** `xorxplnzfdnmuiecgvtt`  
**Región:** `us-west-2`

#### Conexión

**Pooler (recomendado para serverless):**
```
Host: aws-0-us-west-1.pooler.supabase.com
Port: 6543
Database: postgres
User: postgres.xorxplnzfdnmuiecgvtt
Password: [ver Railway variables]
```

**Direct (para admin/psql):**
```
Host: aws-0-us-west-1.pooler.supabase.com
Port: 5432
```

#### String de Conexión

```bash
# Railway variable
DATABASE_URL=postgresql://postgres.xorxplnzfdnmuiecgvtt:PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

#### Acceso con psql

```bash
psql "postgresql://postgres.xorxplnzfdnmuiecgvtt:PASSWORD@aws-0-us-west-1.pooler.supabase.com:5432/postgres"

# Listar tablas
\dt

# Describe tabla
\d projects

# Query
SELECT * FROM projects;
```

#### Backups

Supabase hace backups automáticos diarios. Para backup manual:

```bash
# Desde Supabase dashboard:
# Database > Backups > Create backup
```

---

### Docker Local (Opcional)

**Buildear imagen:**
```bash
docker build -t ops-backend .
```

**Correr contenedor:**
```bash
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./operations.db \
  --name ops-backend \
  ops-backend
```

**Ver logs:**
```bash
docker logs -f ops-backend
```

**Parar:**
```bash
docker stop ops-backend
docker rm ops-backend
```

---

## Troubleshooting

### Problema: Import Error al Iniciar

**Error:**
```
ImportError: cannot import name 'X' from 'Y'
```

**Solución:**
```bash
# Reinstala dependencias
pip install -r requirements.txt --upgrade

# O recrear venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Problema: Database Locked (SQLite)

**Error:**
```
sqlalchemy.exc.OperationalError: database is locked
```

**Solución:**
```bash
# Cierra todas las conexiones
pkill -f uvicorn

# O borra y recrea la DB
rm operations.db
python main.py
```

**Prevención:** Usa PostgreSQL en producción (ya configurado en Railway).

---

### Problema: CORS Error en Frontend

**Error:** Browser bloquea request por CORS.

**Solución:** Agrega el origen del frontend a `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://operations-dashboard-nine.vercel.app",
        "https://tu-nuevo-frontend.vercel.app"  # Agregar acá
    ],
    ...
)
```

---

### Problema: Railway Deploy Falla

**Error:** Build error en Railway.

**Solución:**
1. Revisa logs: `railway logs`
2. Verifica que `Dockerfile` existe
3. Verifica que `requirements.txt` está actualizado
4. Rebuild: `railway up --detach`

---

### Problema: Supabase Connection Error

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solución:**
1. Verifica que `DATABASE_URL` está bien configurado en Railway
2. Usa el **pooler** (puerto 6543), no el puerto directo
3. Revisa que la password es correcta
4. Whitelista la IP de Railway en Supabase (si está restringido)

```bash
# Test conexión
railway run psql "$DATABASE_URL"
```

---

### Problema: Swagger UI No Muestra Endpoints

**Causa:** Router no está registrado en `main.py`.

**Solución:**
```python
# main.py
from routers import mi_nuevo_router

app.include_router(mi_nuevo_router.router, prefix="/api/v1")
```

Reinicia el servidor y verifica en `/docs`.

---

## Recursos Adicionales

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Pydantic v2 Docs](https://docs.pydantic.dev/latest/)
- [Railway Docs](https://docs.railway.app/)
- [Supabase Docs](https://supabase.com/docs)

---

## Contribuyendo

### Workflow

1. Crea una rama feature:
```bash
git checkout -b feature/nueva-funcionalidad
```

2. Desarrolla y testea localmente

3. Commit y push:
```bash
git add .
git commit -m "feat: implementa nueva funcionalidad"
git push origin feature/nueva-funcionalidad
```

4. Deploy a Railway (se auto-deploya en push a main)

### Convenciones

- **Commits:** Usa conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)
- **Branches:** `feature/`, `fix/`, `docs/`
- **Code style:** Black + isort (futuro)

---

**Última actualización:** 2025-03-25  
**Versión:** 1.0.0  
**Mantenido por:** Shosanna 🔥 & Padawan 👨‍💻
